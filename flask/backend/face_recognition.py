import cv2
import numpy as np
from deepface import DeepFace
from .database import Database
from .models import FaceEmbedding
import json
import os
from datetime import datetime
import base64
from PIL import Image
import io

class FaceRecognition:
    def __init__(self, faces_dir='faces', model_name='Facenet'):
        self.faces_dir = faces_dir
        self.model_name = model_name  # e.g., 'Facenet', 'ArcFace', 'VGG-Face'
        self.cascade = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_frontalface_default.xml')
        self.db = Database()
        self.embedding_model = FaceEmbedding(self.db)
        
        # Create faces directory if it doesn't exist
        if not os.path.exists(faces_dir):
            os.makedirs(faces_dir)

    def set_model(self, model_name):
        self.model_name = model_name

    def compute_embedding_from_image(self, image_bgr):
        # DeepFace.represent expects RGB
        image_rgb = cv2.cvtColor(image_bgr, cv2.COLOR_BGR2RGB)
        reps = DeepFace.represent(img_path=image_rgb, enforce_detection=False, model_name=self.model_name)
        if isinstance(reps, list) and len(reps) > 0:
            vector = reps[0]['embedding'] if isinstance(reps[0], dict) and 'embedding' in reps[0] else reps[0]
            return vector
        return None

    def store_embedding(self, user_id, pose, vector):
        embedding_text = json.dumps(vector)
        self.embedding_model.upsert_embedding(user_id, pose, self.model_name, embedding_text)
        return True

    def get_user_embeddings(self, user_id):
        rows = self.embedding_model.get_user_embeddings(user_id, self.model_name)
        embeddings_by_pose = {}
        for row in rows:
            try:
                embeddings_by_pose[row['pose']] = json.loads(row['embedding'])
            except Exception:
                pass
        return embeddings_by_pose
    
    def validate_face_quality(self, image, pose=None):
        """Validate face quality and optionally enforce pose guidance (front/left/right/up/down)."""
        try:
            # Convert to grayscale for face detection
            if len(image.shape) == 3:
                gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
            else:
                gray = image
            
            # Detect faces
            faces = self.cascade.detectMultiScale(gray, 1.3, 5)
            
            if len(faces) == 0:
                return False, "No face detected. Please ensure your full face is visible."
            
            if len(faces) > 1:
                return False, "Multiple faces detected. Please ensure only your face is visible."
            
            # Get the face region
            (x, y, w, h) = faces[0]
            
            # Check face size (should be reasonably large)
            face_area = w * h
            image_area = image.shape[0] * image.shape[1]
            face_ratio = face_area / image_area
            
            if face_ratio < 0.05:  # Face too small
                return False, "Face too small. Please move closer to the camera."
            
            if face_ratio > 0.8:  # Face too large
                return False, "Face too close. Please move back from the camera."
            
            # Check face position (should be roughly centered)
            center_x = x + w/2
            center_y = y + h/2
            image_center_x = image.shape[1] / 2
            image_center_y = image.shape[0] / 2
            
            # Allow some tolerance for centering
            tolerance_x = image.shape[1] * 0.3
            tolerance_y = image.shape[0] * 0.3
            
            if pose in (None, '', 'front'):
                # For front, require stricter centering
                if abs(center_x - image_center_x) > tolerance_x * 0.4 or abs(center_y - image_center_y) > tolerance_y * 0.4:
                    return False, "Center your face inside the circle."
            elif pose == 'left':
                if not (center_x < image_center_x - tolerance_x * 0.15):
                    return False, "Turn your head slightly left."
            elif pose == 'right':
                if not (center_x > image_center_x + tolerance_x * 0.15):
                    return False, "Turn your head slightly right."
            elif pose == 'up':
                if not (center_y < image_center_y - tolerance_y * 0.15):
                    return False, "Tilt your head up."
            elif pose == 'down':
                if not (center_y > image_center_y + tolerance_y * 0.15):
                    return False, "Tilt your head down."
            
            # Check lighting (brightness and contrast)
            face_roi = gray[y:y+h, x:x+w]
            brightness = np.mean(face_roi)
            contrast = np.std(face_roi)
            
            if brightness < 50:
                return False, "Image too dark. Please improve lighting."
            
            if brightness > 200:
                return False, "Image too bright. Please reduce lighting."
            
            if contrast < 20:
                return False, "Low contrast. Please improve lighting conditions."
            
            # Check if eyes are visible (rough estimate)
            eye_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_eye.xml')
            eyes = eye_cascade.detectMultiScale(face_roi, 1.1, 3)
            
            if len(eyes) < 1:
                return False, "Eyes not clearly visible. Please remove glasses or improve lighting."
            
            return True, "Face quality is good"
            
        except Exception as e:
            return False, f"Error validating face quality: {str(e)}"
    
    def capture_face_from_camera(self, user_id):
        """Capture face from camera with quality validation"""
        cap = cv2.VideoCapture(0)
        
        if not cap.isOpened():
            return False, "Camera not available"
        
        face_captured = False
        face_path = None
        quality_message = ""
        
        print("Face Capture Instructions:")
        print("1. Position your face in the center of the frame")
        print("2. Ensure good lighting (not too bright or dark)")
        print("3. Remove glasses if they cause glare")
        print("4. Look directly at the camera")
        print("5. Press SPACE to capture when ready")
        print("6. Press Q to quit")
        
        while not face_captured:
            ret, frame = cap.read()
            if not ret:
                continue
            
            # Create a copy for display
            display_frame = frame.copy()
            
            # Detect faces
            gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
            faces = self.cascade.detectMultiScale(gray, 1.3, 5)
            
            # Draw face detection rectangle and quality indicators
            for (x, y, w, h) in faces:
                # Validate face quality
                is_valid, message = self.validate_face_quality(frame)
                
                if is_valid:
                    cv2.rectangle(display_frame, (x, y), (x+w, y+h), (0, 255, 0), 2)
                    cv2.putText(display_frame, 'Face OK - Press SPACE to capture', (10, 30), 
                               cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)
                    quality_message = "Face quality is good"
                else:
                    cv2.rectangle(display_frame, (x, y), (x+w, y+h), (0, 0, 255), 2)
                    cv2.putText(display_frame, 'Face Quality Issue', (10, 30), 
                               cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 255), 2)
                    quality_message = message
            
            # Draw center guide
            center_x = display_frame.shape[1] // 2
            center_y = display_frame.shape[0] // 2
            cv2.circle(display_frame, (center_x, center_y), 50, (255, 255, 0), 2)
            cv2.putText(display_frame, 'Center your face here', (center_x - 100, center_y - 60), 
                       cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 0), 1)
            
            # Show quality message
            if quality_message:
                cv2.putText(display_frame, quality_message, (10, display_frame.shape[0] - 20), 
                           cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1)
            
            cv2.imshow('Face Capture - Quality Check', display_frame)
            
            key = cv2.waitKey(1) & 0xFF
            if key == ord('q'):
                break
            elif key == ord(' '):  # Space bar to capture
                if len(faces) > 0:
                    is_valid, message = self.validate_face_quality(frame)
                    if is_valid:
                        face_path = os.path.join(self.faces_dir, f'user_{user_id}.jpg')
                        cv2.imwrite(face_path, frame)
                        face_captured = True
                        print(f"Face captured successfully: {face_path}")
                    else:
                        print(f"Face quality issue: {message}")
                else:
                    print("No face detected. Please position your face properly.")
        
        cap.release()
        cv2.destroyAllWindows()
        
        if face_captured:
            return True, face_path
        else:
            return False, "Face capture cancelled"
    
    def capture_face_from_upload(self, user_id, image_data, pose='front', persist_image=True):
        """Capture face from uploaded image with quality validation"""
        try:
            # Decode base64 image data
            if image_data.startswith('data:image'):
                # Remove data URL prefix
                image_data = image_data.split(',')[1]
            
            # Decode base64
            image_bytes = base64.b64decode(image_data)
            image = Image.open(io.BytesIO(image_bytes))
            
            # Convert to OpenCV format
            opencv_image = cv2.cvtColor(np.array(image), cv2.COLOR_RGB2BGR)
            
            # Validate face quality
            is_valid, message = self.validate_face_quality(opencv_image)
            
            if not is_valid:
                return False, message
            
            # Optionally save the image
            face_path = None
            if persist_image:
                face_path = os.path.join(self.faces_dir, f'user_{user_id}.jpg')
                cv2.imwrite(face_path, opencv_image)

            # Compute and store embedding for the specified pose
            vector = self.compute_embedding_from_image(opencv_image)
            if vector is None:
                return False, "Failed to compute face embedding"
            self.store_embedding(user_id, pose, vector)
            
            return True, face_path or "embedding_saved"
            
        except Exception as e:
            return False, f"Error processing uploaded image: {str(e)}"
    
    def capture_face(self, user_id, method='camera', image_data=None, pose='front'):
        """Main face capture method - supports both camera and upload"""
        if method == 'camera':
            return self.capture_face_from_camera(user_id)
        elif method == 'upload' and image_data:
            return self.capture_face_from_upload(user_id, image_data, pose=pose)
        else:
            return False, "Invalid capture method"
    
    def recognize_face(self, user_id, max_attempts=5, distance_threshold=0.9):
        """Recognize using stored embeddings; compare live embedding to user's multi-pose embeddings"""
        stored = self.get_user_embeddings(user_id)
        if not stored:
            return False, "No embeddings found for this user"
        
        cap = cv2.VideoCapture(0)
        
        if not cap.isOpened():
            return False, "Camera not available"
        
        recognition_success = False
        attempts = 0
        
        print("Face Recognition Instructions:")
        print("1. Look directly at the camera")
        print("2. Ensure good lighting")
        print("3. Keep your face centered")
        print("4. System will automatically attempt recognition")
        
        while not recognition_success and attempts < max_attempts:
            ret, frame = cap.read()
            if not ret:
                continue
            
            # Validate face quality first
            is_valid, message = self.validate_face_quality(frame)
            
            if not is_valid:
                # Show the frame with quality message
                display_frame = frame.copy()
                cv2.putText(display_frame, f'Quality Issue: {message}', (10, 30), 
                           cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 255), 2)
                cv2.putText(display_frame, f'Attempts: {attempts + 1}/{max_attempts}', (10, 60), 
                           cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)
                cv2.imshow('Face Recognition', display_frame)
                
                if cv2.waitKey(100) & 0xFF == ord('q'):
                    break
                continue
            
            # Compute live embedding from frame
            try:
                live_vector = self.compute_embedding_from_image(frame)
                if live_vector is None:
                    attempts += 1
                    continue

                # Compare with all stored pose embeddings
                min_distance = 999.0
                for pose_key, stored_vector in stored.items():
                    # Cosine distance between unit-normalized vectors
                    a = np.array(live_vector, dtype=np.float32)
                    b = np.array(stored_vector, dtype=np.float32)
                    denom = (np.linalg.norm(a) * np.linalg.norm(b)) + 1e-8
                    dist = 1.0 - float(np.dot(a, b) / denom)
                    if dist < min_distance:
                        min_distance = dist

                if min_distance < distance_threshold:
                    recognition_success = True
                    print(f"Face recognized! Min distance: {min_distance:.3f}")
                    break
                else:
                    print(f"Recognition failed. Min distance: {min_distance:.3f}")
            except Exception as e:
                print(f"Face recognition error: {e}")
            
            attempts += 1
            
            # Show live feed with status
            display_frame = frame.copy()
            gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
            faces = self.cascade.detectMultiScale(gray, 1.3, 5)
            
            for (x, y, w, h) in faces:
                cv2.rectangle(display_frame, (x, y), (x+w, y+h), (0, 255, 0), 2)
            
            cv2.putText(display_frame, f'Attempts: {attempts}/{max_attempts}', (10, 30), 
                       cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)
            cv2.putText(display_frame, 'Face detected - Processing...', (10, 60), 
                       cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)
            cv2.imshow('Face Recognition', display_frame)
            
            if cv2.waitKey(100) & 0xFF == ord('q'):
                break
        
        cap.release()
        cv2.destroyAllWindows()
        
        if recognition_success:
            return True, "Face recognized successfully"
        else:
            return False, f"Face recognition failed after {attempts} attempts"
    
    def has_face_data(self, user_id):
        """Check if a user has embeddings stored"""
        return self.embedding_model.has_any_embeddings(user_id)
    
    def delete_face_data(self, user_id):
        """Delete face data for a user"""
        face_path = os.path.join(self.faces_dir, f'user_{user_id}.jpg')
        if os.path.exists(face_path):
            os.remove(face_path)
            return True
        return False
    
    def get_face_data_info(self, user_id):
        """Get information about stored embeddings"""
        rows = self.embedding_model.get_user_embeddings(user_id)
        if rows:
            poses = [row['pose'] for row in rows]
            return {
                'exists': True,
                'model': self.model_name,
                'poses': poses,
                'count': len(rows)
            }
        return {'exists': False}
