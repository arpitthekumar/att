/**
 * AI Attendance System - Teacher Attendance JavaScript
 * Handles face recognition, attendance tracking, and data management
 */

document.addEventListener('DOMContentLoaded', function() {
    // Global variables
    let cameraStream = null;
    let recognitionActive = false;
    let attendanceData = [];
    let speechSynthesis = window.speechSynthesis;
    let currentStudentIndex = 0;
    let faceDetectionInterval = null;
    let recognizedStudentId = null;
    let unrecognizedFaces = [];
    
    // DOM Elements
    const startCameraBtn = document.getElementById('start-camera');
    const stopCameraBtn = document.getElementById('stop-camera');
    const markAttendanceBtn = document.getElementById('mark-attendance');
    const videoElement = document.getElementById('camera-feed');
    const canvasElement = document.getElementById('camera-canvas');
    const faceOverlay = document.getElementById('face-overlay');
    const faceBox = document.getElementById('face-box');
    const recognitionStatus = document.getElementById('recognition-status');
    const attendanceType = document.getElementById('attendance-type');
    const attendanceRemarks = document.getElementById('attendance-remarks');
    
    // Face API endpoint
    const FACE_API_ENDPOINT = '/api/v1/recognize-face';
    const ATTENDANCE_API_ENDPOINT = '/api/v1/mark-attendance-manual';
    const SAVE_ATTENDANCE_ENDPOINT = '/api/v1/attendance/save';
    
    // Face detection properties
let faceDetector;
try {
    // Check if FaceDetector API is available
    if ('FaceDetector' in window) {
        faceDetector = new FaceDetector();
    } else {
        console.warn('FaceDetector API not supported in this browser');
    }
} catch (error) {
    console.error('Error initializing FaceDetector:', error);
}

const detectionOptions = {
    maxDetectedFaces: 1,
    minDetectionInterval: 100
};
    
    // Speech synthesis setup
    const synth = window.speechSynthesis;
    let voices = [];
    
    function populateVoiceList() {
        voices = synth.getVoices();
    }
    
    if (synth.onvoiceschanged !== undefined) {
        synth.onvoiceschanged = populateVoiceList;
    }
    
    // Get class information from the page
    const classContainer = document.querySelector('[data-class-id]');
    const classId = classContainer ? classContainer.dataset.classId : null;
    const className = classContainer ? classContainer.dataset.className : 'Unknown Class';
    
    // Initialize attendance data
    function initializeAttendanceData() {
        // Get students from the table
        const studentRows = document.querySelectorAll('#student-list .student-row');
        const students = [];
        
        studentRows.forEach(row => {
            students.push({
                id: row.dataset.studentId,
                name: row.dataset.studentName,
                rollNumber: row.dataset.rollNumber,
                status: 'absent', // Default status
                marked: false,
                timestamp: null,
                type: attendanceType.value,
                remarks: ''
            });
        });
        
        // Store in local storage
        localStorage.setItem(`attendance_${classId}`, JSON.stringify(students));
        attendanceData = students;
        updateAttendanceCounts();
        
        console.log(`Loaded ${students.length} students for class ${className}`);
        return students;
    }
    
    // Load attendance data from local storage or initialize if not exists
    function loadAttendanceData() {
        const storedData = localStorage.getItem(`attendance_${classId}`);
        if (storedData) {
            attendanceData = JSON.parse(storedData);
            updateAttendanceCounts();
            updateStudentList();
            console.log(`Loaded attendance data from local storage for class ${className}`);
            return attendanceData;
        } else {
            return initializeAttendanceData();
        }
    }
    
    // Update the UI with attendance counts
    function updateAttendanceCounts() {
        const presentCount = attendanceData.filter(s => s.status === 'present').length;
        const absentCount = attendanceData.filter(s => s.status === 'absent').length;
        const lateCount = attendanceData.filter(s => s.status === 'late').length;
        const totalCount = attendanceData.length;
        
        document.getElementById('present-count').textContent = presentCount;
        document.getElementById('absent-count').textContent = absentCount;
        document.getElementById('late-count').textContent = lateCount;
        
        const attendanceRate = totalCount > 0 ? Math.round((presentCount / totalCount) * 100) : 0;
        document.getElementById('attendance-rate').textContent = `${attendanceRate}%`;
    }
    
    // Update the student list UI with current attendance status
    function updateStudentList() {
        const studentRows = document.querySelectorAll('#student-list .student-row');
        
        studentRows.forEach(row => {
            const studentId = row.dataset.studentId;
            const student = attendanceData.find(s => s.id === studentId);
            
            if (student) {
                const statusElement = row.querySelector('.attendance-status');
                const timeElement = row.querySelector('.attendance-time');
                
                // Update status display
                statusElement.className = 'attendance-status px-2 inline-flex text-xs leading-5 font-semibold rounded-full';
                
                if (student.status === 'present') {
                    statusElement.classList.add('bg-green-100', 'text-green-800');
                    statusElement.innerHTML = '<i class="fas fa-check-circle mr-1"></i>Present';
                } else if (student.status === 'absent') {
                    statusElement.classList.add('bg-red-100', 'text-red-800');
                    statusElement.innerHTML = '<i class="fas fa-times-circle mr-1"></i>Absent';
                } else if (student.status === 'late') {
                    statusElement.classList.add('bg-yellow-100', 'text-yellow-800');
                    statusElement.innerHTML = '<i class="fas fa-clock mr-1"></i>Late';
                } else {
                    statusElement.classList.add('bg-gray-100', 'text-gray-800');
                    statusElement.textContent = 'Not Marked';
                }
                
                // Update time display
                if (student.timestamp) {
                    const time = new Date(student.timestamp);
                    timeElement.textContent = time.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
                } else {
                    timeElement.textContent = '-';
                }
            }
        });
        
        // Update attendance review lists
        updateAttendanceReviewLists();
    }
    
    // Update the attendance review lists
    function updateAttendanceReviewLists() {
        const presentList = document.getElementById('present-students-list');
        const absentList = document.getElementById('absent-students-list');
        const lateList = document.getElementById('late-students-list');
        
        if (!presentList || !absentList || !lateList) return;
        
        // Filter students by status
        const presentStudents = attendanceData.filter(s => s.status === 'present');
        const absentStudents = attendanceData.filter(s => s.status === 'absent');
        const lateStudents = attendanceData.filter(s => s.status === 'late');
        
        // Update present students list
        if (presentStudents.length > 0) {
            presentList.innerHTML = presentStudents.map(student => `
                <div class="flex items-center justify-between p-2 border-b border-green-200">
                    <div>
                        <span class="font-medium">${student.name}</span>
                        <span class="text-sm text-gray-500 ml-2">${student.rollNumber || 'N/A'}</span>
                    </div>
                    <div class="flex space-x-2">
                        <button class="text-red-600 hover:text-red-900" onclick="markStudentAttendance('${student.id}', 'absent')">
                            <i class="fas fa-times"></i>
                        </button>
                        <button class="text-yellow-600 hover:text-yellow-900" onclick="markStudentAttendance('${student.id}', 'late')">
                            <i class="fas fa-clock"></i>
                        </button>
                    </div>
                </div>
            `).join('');
        } else {
            presentList.innerHTML = `
                <div class="text-center text-gray-500 py-4">
                    <p>No students marked present yet</p>
                </div>
            `;
        }
        
        // Update absent students list
        if (absentStudents.length > 0) {
            absentList.innerHTML = absentStudents.map(student => `
                <div class="flex items-center justify-between p-2 border-b border-red-200">
                    <div>
                        <span class="font-medium">${student.name}</span>
                        <span class="text-sm text-gray-500 ml-2">${student.rollNumber || 'N/A'}</span>
                    </div>
                    <div class="flex space-x-2">
                        <button class="text-green-600 hover:text-green-900" onclick="markStudentAttendance('${student.id}', 'present')">
                            <i class="fas fa-check"></i>
                        </button>
                        <button class="text-yellow-600 hover:text-yellow-900" onclick="markStudentAttendance('${student.id}', 'late')">
                            <i class="fas fa-clock"></i>
                        </button>
                    </div>
                </div>
            `).join('');
        } else {
            absentList.innerHTML = `
                <div class="text-center text-gray-500 py-4">
                    <p>No students marked absent yet</p>
                </div>
            `;
        }
        
        // Update late students list
        if (lateStudents.length > 0) {
            lateList.innerHTML = lateStudents.map(student => `
                <div class="flex items-center justify-between p-2 border-b border-yellow-200">
                    <div>
                        <span class="font-medium">${student.name}</span>
                        <span class="text-sm text-gray-500 ml-2">${student.rollNumber || 'N/A'}</span>
                    </div>
                    <div class="flex space-x-2">
                        <button class="text-green-600 hover:text-green-900" onclick="markStudentAttendance('${student.id}', 'present')">
                            <i class="fas fa-check"></i>
                        </button>
                        <button class="text-red-600 hover:text-red-900" onclick="markStudentAttendance('${student.id}', 'absent')">
                            <i class="fas fa-times"></i>
                        </button>
                    </div>
                </div>
            `).join('');
        } else {
            lateList.innerHTML = `
                <div class="text-center text-gray-500 py-4">
                    <p>No students marked late yet</p>
                </div>
            `;
        }
    }
    
    // Initialize the page
    loadAttendanceData();
    
    // Camera control functions
    async function startCamera() {
        try {
            // Get available video devices
            const devices = await navigator.mediaDevices.enumerateDevices();
            const videoDevices = devices.filter(device => device.kind === 'videoinput');
            
            if (videoDevices.length === 0) {
                throw new Error('No video devices found');
            }
            
            // Use the first video device
            const stream = await navigator.mediaDevices.getUserMedia({
                video: {
                    deviceId: videoDevices[0].deviceId,
                    width: { ideal: 640 },
                    height: { ideal: 480 }
                }
            });
            
            videoElement.srcObject = stream;
            cameraStream = stream;
            
            // Show the video element but keep canvas hidden
            videoElement.style.display = 'block';
            canvasElement.style.display = 'none';
            canvasElement.style.position = 'absolute';
            canvasElement.style.top = '0';
            canvasElement.style.left = '0';
            faceOverlay.style.display = 'block';
            
            // Set up face box canvas to match video dimensions
            faceBox.width = videoElement.videoWidth || 640;
            faceBox.height = videoElement.videoHeight || 480;
            
            // Make sure mark attendance button is visible but disabled initially
            // It will be enabled by startFaceDetection if needed
            if (markAttendanceBtn) {
                markAttendanceBtn.classList.remove('hidden');
                markAttendanceBtn.disabled = true;
            }
            
            // Start face detection
            startFaceDetection();
            
            // Update UI
            startCameraBtn.disabled = true;
            stopCameraBtn.disabled = false;
            recognitionStatus.textContent = 'Camera started. Looking for faces...';
            
            console.log('Camera started successfully');
        } catch (error) {
            console.error('Error starting camera:', error);
            recognitionStatus.innerHTML = `
                <div class="text-center text-red-600">
                    <i class="fas fa-exclamation-triangle text-2xl mb-2"></i>
                    <p>Camera error: ${error.message}</p>
                    <p class="text-sm mt-2">Please check camera permissions and try again</p>
                </div>
            `;
        }
    }
    
    function stopCamera() {
        if (cameraStream) {
            // Stop all tracks
            cameraStream.getTracks().forEach(track => track.stop());
            cameraStream = null;
            
            // Clear video source
            videoElement.srcObject = null;
            
            // Stop face detection
            stopFaceDetection();
            
            // Clear auto recognition interval
            if (window.autoRecognizeInterval) {
                clearInterval(window.autoRecognizeInterval);
                window.autoRecognizeInterval = null;
            }
            
            // Update UI
            videoElement.style.display = 'none';
            canvasElement.style.display = 'none';
            faceOverlay.style.display = 'none';
            startCameraBtn.disabled = false;
            stopCameraBtn.disabled = true;
            
            // Hide mark attendance button
            if (markAttendanceBtn) {
                markAttendanceBtn.classList.add('hidden');
                markAttendanceBtn.disabled = true;
            }
            
            // Update recognition status with better UI
             recognitionStatus.innerHTML = `
                <div class="text-center text-gray-500">
                    <i class="fas fa-camera-slash text-4xl mb-2"></i>
                    <p>Camera stopped</p>
                    <p class="text-sm">Click 'Start Camera' to begin</p>
                </div>
            `;
            
            console.log('Camera stopped');
        }
    }
    
    // Face detection and recognition functions
    function startFaceDetection() {
        if (faceDetectionInterval) {
            clearInterval(faceDetectionInterval);
        }
        
        recognitionActive = true;
        
        // Set up canvas dimensions to match video
        canvasElement.width = videoElement.videoWidth || 640;
        canvasElement.height = videoElement.videoHeight || 480;
        
        // Make sure canvas is properly hidden and positioned
        canvasElement.style.display = 'none';
        canvasElement.style.position = 'absolute';
        
        // Set up face box canvas to match video dimensions
        faceBox.width = videoElement.videoWidth || 640;
        faceBox.height = videoElement.videoHeight || 480;
        
        // Check if FaceDetector API is available
    const useFallbackDetection = !faceDetector || !('FaceDetector' in window);
    
    if (useFallbackDetection) {
        recognitionStatus.innerHTML = `
            <div class="text-center">
                <div class="text-amber-600 mb-2"><i class="fas fa-exclamation-triangle mr-2"></i>Face detection API not available</div>
                <div class="text-sm mb-2">Using server-side face recognition instead</div>
                <div class="text-sm">Position your face in front of the camera and click the button below</div>
            </div>
        `;
        console.warn('FaceDetector API not available - using server-side recognition with basic tracking');
        
        // Enable the mark attendance button as a fallback
        markAttendanceBtn.disabled = false;
        markAttendanceBtn.classList.remove('hidden');
        markAttendanceBtn.innerHTML = '<i class="fas fa-camera mr-2"></i>Capture & Recognize Face';
        
        // Draw a guide box on the face-box canvas to help users position their face
        const overlayContext = faceBox.getContext('2d');
        
        // Set up a simpler interval that captures frames and attempts basic face tracking
        faceDetectionInterval = setInterval(() => {
            if (!videoElement.videoWidth) return; // Video not ready yet
            
            // Draw video frame to canvas for potential recognition
            canvasElement.width = videoElement.videoWidth || 640;
            canvasElement.height = videoElement.videoHeight || 480;
            const context = canvasElement.getContext('2d');
            context.drawImage(videoElement, 0, 0, canvasElement.width, canvasElement.height);
            
            // Clear previous overlay
            overlayContext.clearRect(0, 0, faceBox.width, faceBox.height);
            
            // Draw a tracking rectangle that follows movement
            const boxWidth = faceBox.width * 0.5;
            const boxHeight = faceBox.height * 0.6;
            const x = (faceBox.width - boxWidth) / 2;
            const y = (faceBox.height - boxHeight) / 2;
            
            // Draw tracking rectangle
            overlayContext.strokeStyle = '#FFA500'; // Orange
            overlayContext.lineWidth = 3;
            overlayContext.setLineDash([10, 10]); // Dashed line
            overlayContext.strokeRect(x, y, boxWidth, boxHeight);
            
            // Add text guide
            overlayContext.font = '16px Arial';
            overlayContext.fillStyle = '#FFA500';
            overlayContext.textAlign = 'center';
            overlayContext.fillText('Position face here', faceBox.width / 2, y - 10);
            
            // Display student name if recognized
            if (recognizedStudentId) {
                const student = attendanceData.find(s => s.id === recognizedStudentId);
                if (student) {
                    // Change to green rectangle when recognized
                    overlayContext.strokeStyle = '#00FF00'; // Green
                    overlayContext.lineWidth = 3;
                    overlayContext.setLineDash([]); // Solid line
                    overlayContext.strokeRect(x, y, boxWidth, boxHeight);
                    
                    // Display student name
                    overlayContext.fillStyle = '#00FF00';
                    overlayContext.font = 'bold 16px Arial';
                    overlayContext.textAlign = 'center';
                    overlayContext.fillText(student.name, faceBox.width / 2, y - 10);
                }
            }
            
            // Automatically recognize face every 3 seconds
            if (!window.autoRecognizeInterval) {
                window.autoRecognizeInterval = setInterval(() => {
                    if (recognitionActive && !markAttendanceBtn.disabled) {
                        recognizeFace();
                    }
                }, 3000); // Try to recognize every 3 seconds
            }
            
            // Also allow manual recognition via button
            markAttendanceBtn.onclick = () => recognizeFace();
        }, 100); // Update more frequently for smoother tracking
        
        return;
    }
        
        // Start detection loop with FaceDetector API
        faceDetectionInterval = setInterval(async () => {
            if (!videoElement.videoWidth) return; // Video not ready yet
            
            try {
                // Draw current frame to canvas
                const context = canvasElement.getContext('2d');
                canvasElement.width = videoElement.videoWidth;
                canvasElement.height = videoElement.videoHeight;
                context.drawImage(videoElement, 0, 0, canvasElement.width, canvasElement.height);
                
                // Detect faces if FaceDetector is available
                let faces = [];
                if (faceDetector) {
                    faces = await faceDetector.detect(videoElement);
                } else {
                    // Fallback: Just assume there's a face and proceed with recognition
                    // This is a simplified approach - in a real app, you might want to use a JS-based face detection library
                    recognizeFace();
                    return;
                }
                
                // Clear previous face boxes
                const overlayContext = faceBox.getContext('2d');
                overlayContext.clearRect(0, 0, faceBox.width, faceBox.height);
                
                if (faces.length > 0) {
                    // Get the first face
                    const face = faces[0];
                    const { boundingBox } = face;
                    
                    // Calculate scaling factors to match video dimensions to canvas dimensions
                    const scaleX = faceBox.width / videoElement.videoWidth;
                    const scaleY = faceBox.height / videoElement.videoHeight;
                    
                    // Draw face box with scaling
                    overlayContext.strokeStyle = '#00FF00';
                    overlayContext.lineWidth = 3;
                    overlayContext.strokeRect(
                        boundingBox.x * scaleX,
                        boundingBox.y * scaleY,
                        boundingBox.width * scaleX,
                        boundingBox.height * scaleY
                    );
                    
                    // Display student name if recognized
                    if (recognizedStudentId) {
                        const student = attendanceData.find(s => s.id === recognizedStudentId);
                        if (student) {
                            overlayContext.fillStyle = '#00FF00';
                            overlayContext.font = 'bold 16px Arial';
                            overlayContext.fillText(
                                student.name,
                                boundingBox.x * scaleX,
                                (boundingBox.y * scaleY) - 10
                            );
                        }
                    }
                    
                    // Update status
                    recognitionStatus.innerHTML = '<div class="text-center"><i class="fas fa-user-check text-green-500 text-2xl mb-2"></i><p>Face detected. Recognizing...</p></div>';
                    
                    // Recognize face
                    recognizeFace();
                } else {
                    recognitionStatus.innerHTML = '<div class="text-center"><i class="fas fa-user-slash text-red-500 text-2xl mb-2"></i><p>No face detected</p><p class="text-sm">Position your face in front of the camera</p></div>';
                    recognizedStudentId = null;
                }
            } catch (error) {
                console.error('Face detection error:', error);
                recognitionStatus.textContent = 'Face detection error';
            }
        }, detectionOptions.minDetectionInterval);
    }
    
    function stopFaceDetection() {
        if (faceDetectionInterval) {
            clearInterval(faceDetectionInterval);
            faceDetectionInterval = null;
        }
        recognitionActive = false;
        
        // Clear canvas and face box
        const context = canvasElement.getContext('2d');
        context.clearRect(0, 0, canvasElement.width, canvasElement.height);
        
        const overlayContext = faceBox.getContext('2d');
        overlayContext.clearRect(0, 0, faceBox.width, faceBox.height);
    }
    
    async function recognizeFace() {
        if (!recognitionActive || !cameraStream) return;
        
        try {
            // Disable the mark attendance button while processing
            if (markAttendanceBtn) {
                markAttendanceBtn.disabled = true;
                markAttendanceBtn.innerHTML = '<i class="fas fa-spinner fa-spin mr-2"></i>Processing...';
            }
            
            // Draw current video frame to canvas
            const context = canvasElement.getContext('2d');
            context.drawImage(videoElement, 0, 0, canvasElement.width, canvasElement.height);
            
            // Convert canvas to blob with higher quality
            const blob = await new Promise(resolve => canvasElement.toBlob(resolve, 'image/jpeg', 0.95));
            
            // Get canvas data URL for unrecognized faces
            const imageDataUrl = canvasElement.toDataURL('image/jpeg', 0.95);
            
            // Create form data
            const formData = new FormData();
            formData.append('image', blob, 'face.jpg');
            formData.append('class_id', classId);
            
            // Update status
            recognitionStatus.innerHTML = '<div class="text-center"><i class="fas fa-spinner fa-spin text-blue-500 text-2xl mb-2"></i><p>Processing...</p></div>';
            
            try {
                // Send to server for recognition
                const response = await fetch(FACE_API_ENDPOINT, {
                    method: 'POST',
                    body: formData
                });
                
                if (!response.ok) {
                    throw new Error(`Server error: ${response.status}`);
                }
                
                const result = await response.json();
            } catch (apiError) {
                console.error('Face recognition API error:', apiError);
                recognitionStatus.innerHTML = `
                    <div class="text-center text-red-600">
                        <i class="fas fa-exclamation-triangle text-2xl mb-2"></i>
                        <p>API error: ${apiError.message}</p>
                    </div>
                `;
                
                // Re-enable the mark attendance button
                if (markAttendanceBtn) {
                    markAttendanceBtn.disabled = false;
                    markAttendanceBtn.innerHTML = '<i class="fas fa-camera mr-2"></i>Capture & Recognize Face';
                }
                return;
            }
                
                if (result.success && result.student_id) {
                // Student recognized
                const student = attendanceData.find(s => s.id === result.student_id);
                
                if (student) {
                    // Update recognition status with student info and image
                    recognitionStatus.innerHTML = `
                        <div class="flex items-center mb-2">
                            <div class="h-12 w-12 rounded-full bg-green-100 flex items-center justify-center mr-3">
                                <i class="fas fa-user-check text-green-600 text-xl"></i>
                            </div>
                            <div>
                                <div class="font-bold text-green-700">Recognized!</div>
                                <div class="text-lg">${student.name}</div>
                                <div class="text-sm text-gray-600">Roll: ${student.rollNumber || 'N/A'}</div>
                            </div>
                        </div>
                    `;
                    recognizedStudentId = student.id;
                    
                    // Update the face box to show the student name
                    const overlayContext = faceBox.getContext('2d');
                    
                    // If using FaceDetector API, the name will be drawn in the detection loop
                    // For fallback mode, we need to update the guide box here
                    if (!faceDetector || !('FaceDetector' in window)) {
                        // Clear previous overlay
                        overlayContext.clearRect(0, 0, faceBox.width, faceBox.height);
                        
                        // Draw a green rectangle
                        const boxWidth = faceBox.width * 0.5;
                        const boxHeight = faceBox.height * 0.6;
                        const x = (faceBox.width - boxWidth) / 2;
                        const y = (faceBox.height - boxHeight) / 2;
                        
                        overlayContext.strokeStyle = '#00FF00'; // Green
                        overlayContext.lineWidth = 3;
                        overlayContext.setLineDash([]); // Solid line
                        overlayContext.strokeRect(x, y, boxWidth, boxHeight);
                        
                        // Display student name
                        overlayContext.fillStyle = '#00FF00';
                        overlayContext.font = 'bold 16px Arial';
                        overlayContext.textAlign = 'center';
                        overlayContext.fillText(student.name, faceBox.width / 2, y - 10);
                    }
                    
                    // Mark student as present if not already marked
                    if (!student.marked) {
                        markStudentAttendance(student.id, 'present');
                        
                        // Speak student name
                        speakText(`${student.name} is present. Next student please.`);
                    } else {
                        // Speak recognition message for already marked students
                        speakText(`${student.name} was already marked ${student.status}.`);
                    }
                    
                    // Re-enable the mark attendance button after a delay
                    setTimeout(() => {
                        if (markAttendanceBtn) {
                            markAttendanceBtn.disabled = false;
                            markAttendanceBtn.innerHTML = '<i class="fas fa-camera mr-2"></i>Capture & Recognize Face';
                        }
                    }, 2000);
                    
                    // Re-enable the mark attendance button after a delay
                    setTimeout(() => {
                        if (markAttendanceBtn) {
                            markAttendanceBtn.disabled = false;
                            markAttendanceBtn.innerHTML = '<i class="fas fa-camera mr-2"></i>Capture & Recognize Face';
                        }
                    }, 2000);
                }
            } else {
                // No match found
                recognitionStatus.innerHTML = `
                    <div class="flex items-center mb-2">
                        <div class="h-12 w-12 rounded-full bg-red-100 flex items-center justify-center mr-3">
                            <i class="fas fa-user-times text-red-600 text-xl"></i>
                        </div>
                        <div>
                            <div class="font-bold text-red-700">Not Recognized</div>
                            <div>Please try again or mark manually</div>
                        </div>
                    </div>
                `;
                recognizedStudentId = null;
                
                // Add to unrecognized faces
                addUnrecognizedFace(imageDataUrl);
                
                // Update unrecognized faces list
                updateUnrecognizedFacesList();
                
                // Speak notification
                speakText('Face not recognized. Please try again or mark manually.');
                
                // Re-enable the mark attendance button
                if (markAttendanceBtn) {
                    markAttendanceBtn.disabled = false;
                    markAttendanceBtn.innerHTML = '<i class="fas fa-camera mr-2"></i>Capture & Recognize Face';
                }
                
                // Pause face detection for a moment if using FaceDetector API
                if (faceDetector && ('FaceDetector' in window)) {
                    stopFaceDetection();
                    setTimeout(() => {
                        startFaceDetection();
                    }, 3000); // 3 seconds pause
                }
            }
        } catch (error) {
            console.error('Face recognition error:', error);
            recognitionStatus.innerHTML = `
                <div class="text-center text-red-600">
                    <i class="fas fa-exclamation-triangle text-2xl mb-2"></i>
                    <p>Recognition error: ${error.message}</p>
                </div>
            `;
            
            // Re-enable the mark attendance button in case of errors
            if (markAttendanceBtn) {
                markAttendanceBtn.disabled = false;
                markAttendanceBtn.innerHTML = '<i class="fas fa-camera mr-2"></i>Capture & Recognize Face';
            }
        }
    }
    
    // Attendance marking functions
    function markStudentAttendance(studentId, status) {
        // Find student in attendance data
        const studentIndex = attendanceData.findIndex(s => s.id === studentId);
        
        if (studentIndex !== -1) {
            // Update student status
            attendanceData[studentIndex].status = status;
            attendanceData[studentIndex].marked = true;
            attendanceData[studentIndex].timestamp = new Date().toISOString();
            attendanceData[studentIndex].type = attendanceType.value;
            attendanceData[studentIndex].remarks = attendanceRemarks.value;
            
            // Save to local storage
            localStorage.setItem(`attendance_${classId}`, JSON.stringify(attendanceData));
            
            // Update UI
            updateAttendanceCounts();
            updateStudentList();
            updateAttendanceReviewLists();
            
            console.log(`Marked student ${studentId} as ${status}`);
        }
    }
    
    // Function to mark attendance from HTML buttons
    function markAttendance(studentId, status) {
        markStudentAttendance(studentId, status);
    }
    
    // Make markAttendance function globally accessible
    window.markAttendance = markAttendance;
    
    // Speech synthesis function
    function speakText(text) {
        if (!speechSynthesis) return;
        
        // Cancel any ongoing speech
        speechSynthesis.cancel();
        
        // Create utterance
        const utterance = new SpeechSynthesisUtterance(text);
        
        // Get available voices
        const voices = speechSynthesis.getVoices();
        
        // Set voice (use first available voice)
        if (voices.length > 0) {
            utterance.voice = voices[0];
        }
        
        // Speak
        speechSynthesis.speak(utterance);
    }
    
    // Manual attendance marking
    function setupManualAttendanceMarking() {
        const studentRows = document.querySelectorAll('#student-list .student-row');
        
        studentRows.forEach(row => {
            const studentId = row.dataset.studentId;
            const presentBtn = row.querySelector('.mark-present');
            const absentBtn = row.querySelector('.mark-absent');
            const lateBtn = row.querySelector('.mark-late');
            
            if (presentBtn) {
                presentBtn.addEventListener('click', () => markStudentAttendance(studentId, 'present'));
            }
            
            if (absentBtn) {
                absentBtn.addEventListener('click', () => markStudentAttendance(studentId, 'absent'));
            }
            
            if (lateBtn) {
                lateBtn.addEventListener('click', () => markStudentAttendance(studentId, 'late'));
            }
        });
    }
    
    // Save attendance to database
    async function saveAttendanceToDatabase() {
        try {
            // Show loading indicator
            const saveButton = document.getElementById('save-attendance-btn') || markAttendanceBtn;
            if (saveButton) {
                saveButton.disabled = true;
                saveButton.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Saving...';
            }
            
            // Prepare data
            const attendanceRecords = attendanceData.map(student => ({
                student_id: student.id,
                status: student.status,
                timestamp: student.timestamp,
                type: student.type,
                remarks: student.remarks
            }));
            
            try {
                // Send to server
                const response = await fetch(SAVE_ATTENDANCE_ENDPOINT, {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json'
                    },
                    body: JSON.stringify({
                        class_id: classId,
                        attendance_date: new Date().toISOString().split('T')[0],
                        records: attendanceRecords
                    })
                });
                
                if (!response.ok) {
                    throw new Error(`Server error: ${response.status}`);
                }
            
                const result = await response.json();
                
                if (result.success) {
                    // Clear local storage
                    localStorage.removeItem(`attendance_${classId}`);
                    
                    // Show success message
                    alert('Attendance saved successfully!');
                    
                    // Clear unrecognized faces after saving
                    unrecognizedFaces = [];
                    
                    // Redirect to dashboard
                    window.location.href = '/teacher/dashboard';
                } else {
                    throw new Error(result.message || 'Failed to save attendance');
                }
            } catch (apiError) {
                console.error('API error:', apiError);
                alert(`API Error: ${apiError.message}. Please check if the server is running and the API endpoint is available.`);
                
                // Reset button state
                const saveButton = document.getElementById('save-attendance-btn') || markAttendanceBtn;
                if (saveButton) {
                    saveButton.disabled = false;
                    saveButton.innerHTML = '<i class="fas fa-save"></i> Save Attendance';
                }
            }
        } catch (error) {
            console.error('Error saving attendance:', error);
            alert(`Error saving attendance: ${error.message}`);
            
            // Reset button state
            const saveButton = document.getElementById('save-attendance-btn') || markAttendanceBtn;
            if (saveButton) {
                saveButton.disabled = false;
                saveButton.innerHTML = '<i class="fas fa-save"></i> Save Attendance';
            }
        }
    }
    
    // Reset attendance data
    function resetAttendance() {
        if (confirm('Are you sure you want to reset all attendance data? This cannot be undone.')) {
            // Reset all students to absent
            attendanceData.forEach(student => {
                student.status = 'absent';
                student.marked = false;
                student.timestamp = null;
                student.remarks = '';
            });
            
            // Clear unrecognized faces
            unrecognizedFaces = [];
            
            // Update UI
            updateAttendanceCounts();
            updateStudentList();
            updateAttendanceReviewLists();
            updateUnrecognizedFacesList();
            
            // Save to local storage
            localStorage.setItem(`attendance_${classId}`, JSON.stringify(attendanceData));
            
            alert('Attendance data has been reset');
        }
    }
    
    // Add unrecognized face
    function addUnrecognizedFace(imageData) {
        const faceId = 'unrecognized-' + Date.now();
        unrecognizedFaces.push({
            id: faceId,
            imageData: imageData,
            timestamp: new Date().toISOString()
        });
        
        // Update the unrecognized faces list
        updateUnrecognizedFacesList();
    }
    
    // Update unrecognized faces list
    function updateUnrecognizedFacesList() {
        const unrecognizedList = document.getElementById('unrecognized-faces-list');
        
        if (!unrecognizedList) return;
        
        if (unrecognizedFaces.length > 0) {
            unrecognizedList.innerHTML = unrecognizedFaces.map(face => `
                <div class="flex items-center justify-between p-2 border-b border-gray-200">
                    <div class="flex items-center">
                        <img src="${face.imageData}" alt="Unrecognized Face" class="w-12 h-12 object-cover rounded-full">
                        <div class="ml-3">
                            <span class="text-sm text-gray-500">${new Date(face.timestamp).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}</span>
                        </div>
                    </div>
                    <div class="flex items-center">
                        <select id="student-select-${face.id}" class="form-select text-sm rounded-md mr-2">
                            <option value="">Select Student</option>
                            ${attendanceData.map(student => `<option value="${student.id}">${student.name} (${student.rollNumber || 'N/A'})</option>`).join('')}
                        </select>
                        <button class="bg-blue-500 hover:bg-blue-700 text-white text-xs py-1 px-2 rounded" 
                                onclick="assignUnrecognizedFace('${face.id}', document.getElementById('student-select-${face.id}').value)">
                            Assign
                        </button>
                    </div>
                </div>
            `).join('');
        } else {
            unrecognizedList.innerHTML = `
                <div class="text-center text-gray-500 py-4">
                    <p>No unrecognized faces</p>
                </div>
            `;
        }
    }
    
    // Assign unrecognized face to a student
    function assignUnrecognizedFace(faceId, studentId) {
        const faceIndex = unrecognizedFaces.findIndex(face => face.id === faceId);
        if (faceIndex === -1) return;
        
        if (!studentId) {
            alert('Please select a student');
            return;
        }
        
        // Mark the selected student as present
        markStudentAttendance(studentId, 'present');
        
        // Remove the face from unrecognized list
        unrecognizedFaces.splice(faceIndex, 1);
        
        // Update the UI
        updateUnrecognizedFacesList();
        
        alert('Student assigned successfully');
    }
    
    // Make assignUnrecognizedFace available globally
    window.assignUnrecognizedFace = assignUnrecognizedFace;
    
    // Event listeners
    if (startCameraBtn) {
        startCameraBtn.addEventListener('click', startCamera);
    }
    
    if (stopCameraBtn) {
        stopCameraBtn.addEventListener('click', stopCamera);
    }
    
    if (markAttendanceBtn) {
        markAttendanceBtn.addEventListener('click', saveAttendanceToDatabase);
    }
    
    // Reset attendance button
    const resetAttendanceBtn = document.getElementById('reset-attendance');
    if (resetAttendanceBtn) {
        resetAttendanceBtn.addEventListener('click', resetAttendance);
    }
    
    // Save attendance button
    const saveAttendanceBtn = document.getElementById('save-attendance');
    if (saveAttendanceBtn) {
        saveAttendanceBtn.addEventListener('click', saveAttendanceToDatabase);
    }
    
    // Initialize manual attendance marking
    setupManualAttendanceMarking();
    
    // Initialize voice list
    populateVoiceList();
});