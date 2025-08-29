// Multi-pose guided capture
const poses = [
  { key: 'front', text: 'Front face → Look straight at the camera.' },
  { key: 'left', text: 'Left profile → Turn your head slightly left.' },
  { key: 'right', text: 'Right profile → Turn your head slightly right.' },
  { key: 'up', text: 'Upward face → Tilt your head up.' },
  { key: 'down', text: 'Downward face → Tilt your head down.' }
];

let currentIndex = 0;
window.CapturedPoses = {};

function updateInstruction(status) {
  const el = document.getElementById('pose-instruction');
  if (!el) return;
  const prefix = status ? `${status} ` : '';
  el.innerText = `${prefix}${poses[currentIndex].text}`;
}

async function captureCurrentPose(base64Image) {
  const pose = poses[currentIndex].key;
  const resp = await fetch('/api/capture-face', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ method: 'upload', image_data: base64Image, pose })
  });
  const data = await resp.json();
  if (data.success) {
    updateInstruction('✅');
    try { window.CapturedPoses[pose] = base64Image; } catch (_) {}
    currentIndex += 1;
    // Notify listeners a pose was captured
    try { window.dispatchEvent(new CustomEvent('pose-captured', { detail: { index: currentIndex, pose, image: base64Image } })); } catch (_) {}
    if (currentIndex < poses.length) {
      setTimeout(() => updateInstruction(''), 600);
    }
    if (currentIndex >= poses.length) {
      try { window.dispatchEvent(new CustomEvent('all-poses-captured', { detail: { total: poses.length, images: window.CapturedPoses } })); } catch (_) {}
    }
  } else {
    updateInstruction('❌');
  }
  return data.success;
}

// Expose init for pages
window.MultiPoseCapture = {
  getCurrentPose: () => poses[currentIndex]?.key,
  getRemaining: () => poses.slice(currentIndex).map(p => p.key),
  reset: () => { currentIndex = 0; updateInstruction(''); },
  updateInstruction,
  captureCurrentPose
};

// Wire up existing UI if present
document.addEventListener('DOMContentLoaded', () => {
  updateInstruction('');

  const video = document.getElementById('camera-feed');
  const canvas = document.getElementById('camera-canvas');
  const startBtn = document.getElementById('start-camera');
  const stopBtn = document.getElementById('stop-camera');
  const captureBtn = document.getElementById('capture-photo');
  const statusBox = document.querySelector('#camera-status p');
  const cameraSelect = document.getElementById('camera-select');
  const refreshBtn = document.getElementById('refresh-cameras');

  const uploadInput = document.getElementById('photo-upload');
  const uploadBtn = document.getElementById('upload-photo');
  const previewImg = document.getElementById('preview-image');
  const uploadPreview = document.getElementById('upload-preview');

  let streamRef = null;
  let currentDeviceId = null;

  function setStatus(text, ok = true) {
    if (!statusBox) return;
    statusBox.parentElement.classList.remove('hidden');
    statusBox.innerText = text;
    statusBox.parentElement.className = ok
      ? 'mt-4 p-3 rounded-lg bg-green-50 text-green-700'
      : 'mt-4 p-3 rounded-lg bg-red-50 text-red-700';
  }

  function snapshotBase64() {
    if (!canvas || !video) return null;
    canvas.width = video.videoWidth || 640;
    canvas.height = video.videoHeight || 480;
    const ctx = canvas.getContext('2d');
    ctx.drawImage(video, 0, 0, canvas.width, canvas.height);
    return canvas.toDataURL('image/jpeg');
  }

  async function startCameraAuto() {
    try {
      const constraints = currentDeviceId ? { video: { deviceId: { exact: currentDeviceId } } } : { video: true };
      streamRef = await navigator.mediaDevices.getUserMedia(constraints);
      if (video) video.srcObject = streamRef;
      if (captureBtn) captureBtn.classList.add('hidden');
      if (stopBtn) stopBtn.classList.remove('hidden');
      if (startBtn) startBtn.classList.add('hidden');
      setStatus('Camera started. Follow instructions.');
      runAutoCaptureLoop();
    } catch (e) {
      setStatus('Camera error: ' + e.message, false);
    }
  }
  // Expose for external calls (e.g., modal auto-start)
  window.startCameraAuto = startCameraAuto;

  if (startBtn) {
    startBtn.addEventListener('click', startCameraAuto);
  }

  if (stopBtn) {
    stopBtn.addEventListener('click', () => {
      if (streamRef) {
        streamRef.getTracks().forEach(t => t.stop());
        streamRef = null;
      }
      if (video) video.srcObject = null;
      if (captureBtn) captureBtn.classList.add('hidden');
      stopBtn.classList.add('hidden');
      if (startBtn) startBtn.classList.remove('hidden');
      setStatus('Camera stopped.');
    });
  }

  async function populateCameras() {
    try {
      const devices = await navigator.mediaDevices.enumerateDevices();
      const videoInputs = devices.filter(d => d.kind === 'videoinput');
      if (cameraSelect) {
        cameraSelect.innerHTML = '';
        videoInputs.forEach((d, idx) => {
          const opt = document.createElement('option');
          opt.value = d.deviceId;
          opt.textContent = d.label || `Camera ${idx + 1}`;
          cameraSelect.appendChild(opt);
        });
        if (videoInputs.length > 0) {
          currentDeviceId = videoInputs[0].deviceId;
        }
      }
    } catch (e) {
      // Ignore
    }
  }

  if (refreshBtn) {
    refreshBtn.addEventListener('click', async () => {
      await populateCameras();
      setStatus('Camera list refreshed.');
    });
  }

  if (cameraSelect) {
    cameraSelect.addEventListener('change', (e) => {
      currentDeviceId = e.target.value;
    });
  }

  // Try to get permission once to populate labels
  (async () => {
    try {
      const tmp = await navigator.mediaDevices.getUserMedia({ video: true });
      tmp.getTracks().forEach(t => t.stop());
    } catch (e) { /* ignore */ }
    await populateCameras();
  })();

  // Auto-capture loop: checks quality for current pose and captures automatically
  async function validatePose(image, pose) {
    try {
      const resp = await fetch('/api/validate-face-quality', {
        method: 'POST', headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ image_data: image, pose })
      });
      const data = await resp.json();
      return data;
    } catch (e) {
      return { success: false, message: e.message };
    }
  }

  let autoLoopRunning = false;
  async function runAutoCaptureLoop() {
    if (autoLoopRunning) return;
    autoLoopRunning = true;
    updateInstruction('');
    while (autoLoopRunning && window.MultiPoseCapture.getRemaining().length > 0) {
      const currentPose = window.MultiPoseCapture.getCurrentPose();
      const img = snapshotBase64();
      if (!img) { await new Promise(r => setTimeout(r, 300)); continue; }
      const check = await validatePose(img, currentPose);
      if (check.success) {
        setStatus('Good! Capturing ' + currentPose + '...');
        const saved = await captureCurrentPose(img);
        if (saved && window.MultiPoseCapture.getRemaining().length === 0) {
          setStatus('All poses captured!', true);
          break;
        }
        await new Promise(r => setTimeout(r, 400));
      } else {
        setStatus(check.message || ('Adjust for ' + currentPose), false);
        await new Promise(r => setTimeout(r, 400));
      }
    }
    autoLoopRunning = false;
  }

  if (captureBtn) {
    captureBtn.addEventListener('click', async () => {
      const img = snapshotBase64();
      if (!img) return;
      const ok = await captureCurrentPose(img);
      setStatus(ok ? 'Pose saved.' : 'Failed to save pose.', ok);
      if (ok && window.MultiPoseCapture.getRemaining().length === 0) {
        setStatus('All poses captured!', true);
      }
    });
  }

  if (uploadInput) {
    uploadInput.addEventListener('change', (e) => {
      const file = e.target.files?.[0];
      if (!file) return;
      const reader = new FileReader();
      reader.onload = () => {
        if (previewImg) previewImg.src = reader.result;
        if (uploadPreview) uploadPreview.classList.remove('hidden');
        if (uploadBtn) uploadBtn.classList.remove('hidden');
      };
      reader.readAsDataURL(file);
    });
  }

  if (uploadBtn) {
    uploadBtn.addEventListener('click', async () => {
      const src = previewImg ? previewImg.src : null;
      if (!src) return;
      const ok = await captureCurrentPose(src);
      const box = document.querySelector('#upload-status p');
      if (box) {
        box.parentElement.classList.remove('hidden');
        box.innerText = ok ? 'Pose saved and processed.' : 'Failed to save pose.';
        box.parentElement.className = ok
          ? 'mt-4 p-3 rounded-lg bg-green-50 text-green-700'
          : 'mt-4 p-3 rounded-lg bg-red-50 text-red-700';
      }
    });
  }
});

let stream = null;
let capturedImageData = null;

// Initialize page
document.addEventListener('DOMContentLoaded', function() {
    checkCurrentFaceData();
    setupEventListeners();
});

function setupEventListeners() {
    // Camera controls
    const startCameraBtn = document.getElementById('start-camera');
    const capturePhotoBtn = document.getElementById('capture-photo');
    const stopCameraBtn = document.getElementById('stop-camera');
    
    // Upload controls
    const photoUploadBtn = document.getElementById('photo-upload');
    const uploadPhotoBtn = document.getElementById('upload-photo');
    
    // Submit controls
    const saveFaceDataBtn = document.getElementById('save-face-data');
    const retryCaptureBtn = document.getElementById('retry-capture');
    
    // Download controls
    const downloadFaceImageBtn = document.getElementById('download-face-image');
    const updateFaceImageBtn = document.getElementById('update-face-image');

    if (startCameraBtn) startCameraBtn.addEventListener('click', startCamera);
    if (capturePhotoBtn) capturePhotoBtn.addEventListener('click', capturePhoto);
    if (stopCameraBtn) stopCameraBtn.addEventListener('click', stopCamera);
    if (photoUploadBtn) photoUploadBtn.addEventListener('change', handleFileUpload);
    if (uploadPhotoBtn) uploadPhotoBtn.addEventListener('click', useUploadedPhoto);
    if (saveFaceDataBtn) saveFaceDataBtn.addEventListener('click', saveFaceData);
    if (retryCaptureBtn) retryCaptureBtn.addEventListener('click', resetCapture);
    if (downloadFaceImageBtn) downloadFaceImageBtn.addEventListener('click', downloadFaceImage);
    if (updateFaceImageBtn) updateFaceImageBtn.addEventListener('click', updateFaceImage);
}

async function startCamera() {
    try {
        stream = await navigator.mediaDevices.getUserMedia({ 
            video: { 
                width: { ideal: 640 },
                height: { ideal: 480 },
                facingMode: 'user'
            } 
        });
        
        const video = document.getElementById('camera-feed');
        video.srcObject = stream;
        
        document.getElementById('start-camera').classList.add('hidden');
        document.getElementById('capture-photo').classList.remove('hidden');
        document.getElementById('stop-camera').classList.remove('hidden');
        
        showStatus('camera-status', 'Camera started. Position your face in the center.', 'info');
    } catch (error) {
        showStatus('camera-status', 'Error accessing camera: ' + error.message, 'error');
    }
}

function capturePhoto() {
    const video = document.getElementById('camera-feed');
    const canvas = document.getElementById('camera-canvas');
    const context = canvas.getContext('2d');
    
    canvas.width = video.videoWidth;
    canvas.height = video.videoHeight;
    context.drawImage(video, 0, 0);
    
    capturedImageData = canvas.toDataURL('image/jpeg', 0.8);
    
    // Automatically stop camera after capture
    stopCamera();
    
    // Show captured photo preview
    const cameraContainer = document.getElementById('camera-container');
    if (cameraContainer) {
        cameraContainer.innerHTML = `
            <div class="relative">
                <img src="${capturedImageData}" class="w-full h-48 object-cover rounded-lg" alt="Captured Photo">
                <div class="absolute top-2 right-2">
                    <button type="button" onclick="retryCapture()" class="bg-red-600 text-white p-2 rounded-full hover:bg-red-700">
                        <i class="fas fa-redo"></i>
                    </button>
                </div>
            </div>
        `;
    }
    
    // Show status
    showStatus('camera-status', 'Photo captured! Checking quality...', 'success');
    
    // Automatically validate quality after a short delay
    setTimeout(() => {
        validateImageQuality(capturedImageData);
    }, 500);
}

function stopCamera() {
    if (stream) {
        stream.getTracks().forEach(track => track.stop());
        stream = null;
    }
    
    document.getElementById('start-camera').classList.remove('hidden');
    document.getElementById('capture-photo').classList.add('hidden');
    document.getElementById('stop-camera').classList.add('hidden');
    
    showStatus('camera-status', 'Camera stopped.', 'info');
}

function handleFileUpload(event) {
    const file = event.target.files[0];
    if (!file) return;
    
    const reader = new FileReader();
    reader.onload = function(e) {
        capturedImageData = e.target.result;
        
        // Show preview
        const previewImage = document.getElementById('preview-image');
        if (previewImage) {
            previewImage.src = capturedImageData;
            document.getElementById('upload-preview').classList.remove('hidden');
            document.getElementById('upload-photo').classList.remove('hidden');
        }
        
        showStatus('upload-status', 'Photo selected. Click "Use This Photo" to validate.', 'info');
    };
    reader.readAsDataURL(file);
}

function useUploadedPhoto() {
    validateImageQuality(capturedImageData);
    showStatus('upload-status', 'Photo selected! Checking quality...', 'success');
}

async function validateImageQuality(imageData) {
    try {
        const response = await fetch('/api/validate-face-quality', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({ image_data: imageData })
        });
        
        const result = await response.json();
        
        if (result.success) {
            showQualityResults(result.message, true);
            
            // Show the submit section with save button
            showSubmitSection();
            
            // Automatically save face data to form input if we're in add_user form
            const faceDataInput = document.getElementById('face-data');
            if (faceDataInput) {
                faceDataInput.value = capturedImageData;
                
                // Update face data status if it exists
                const faceDataStatus = document.getElementById('face-data-status');
                if (faceDataStatus) {
                    faceDataStatus.innerHTML = `
                        <div class="text-center">
                            <i class="fas fa-check-circle text-3xl text-green-500 mb-2"></i>
                            <p class="text-green-600 font-medium">Face Data Ready!</p>
                            <p class="text-sm text-gray-500">Face data captured and ready for form submission!</p>
                        </div>
                    `;
                    faceDataStatus.className = 'mt-4 p-4 rounded-lg bg-green-50';
                }
                
                // Enable submit button if it exists
                const submitBtn = document.getElementById('submit-btn');
                if (submitBtn) {
                    submitBtn.disabled = false;
                    submitBtn.classList.remove('opacity-50', 'cursor-not-allowed');
                }
                
                console.log('Face data automatically saved to form input');
                
                // Show success message
                showStatus('camera-status', '✅ Face data ready! You can now submit the form.', 'success');
            }
            
            // Also call the global function if it exists
            if (window.autoSaveFaceDataForForm) {
                window.autoSaveFaceDataForForm();
            }
        } else {
            showQualityResults(result.message, false);
            showStatus('camera-status', '❌ Quality check failed. Please try again.', 'error');
        }
    } catch (error) {
        showQualityResults('Error validating image quality: ' + error.message, false);
        showStatus('camera-status', '❌ Error checking quality. Please try again.', 'error');
    }
}

function showQualityResults(message, isGood) {
    const qualityCheck = document.getElementById('quality-check');
    const qualityResults = document.getElementById('quality-results');
    
    if (qualityCheck) qualityCheck.classList.remove('hidden');
    
    const statusClass = isGood ? 'text-green-600 bg-green-50' : 'text-red-600 bg-red-50';
    const icon = isGood ? 'fa-check-circle' : 'fa-exclamation-circle';
    
    if (qualityResults) {
        qualityResults.innerHTML = `
            <div class="p-3 rounded-lg ${statusClass}">
                <i class="fas ${icon} mr-2"></i>
                <span class="font-medium">${message}</span>
            </div>
        `;
    }
}

function showSubmitSection() {
    const submitSection = document.getElementById('submit-section');
    if (submitSection) submitSection.classList.remove('hidden');
}

async function saveFaceData() {
    if (!capturedImageData) {
        alert('No image data to save');
        return;
    }
    
    try {
        const response = await fetch('/api/capture-face', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({ 
                image_data: capturedImageData,
                method: 'upload'
            })
        });
        
        const result = await response.json();
        
        if (result.success) {
            showStatus('upload-status', 'Face data saved successfully!', 'success');
            checkCurrentFaceData();
            resetCapture();
        } else {
            showStatus('upload-status', 'Error saving face data: ' + result.message, 'error');
        }
    } catch (error) {
        showStatus('upload-status', 'Error saving face data: ' + error.message, 'error');
    }
}

function resetCapture() {
    capturedImageData = null;
    const qualityCheck = document.getElementById('quality-check');
    const submitSection = document.getElementById('submit-section');
    const uploadPreview = document.getElementById('upload-preview');
    const uploadPhoto = document.getElementById('upload-photo');
    const photoUpload = document.getElementById('photo-upload');
    
    if (qualityCheck) qualityCheck.classList.add('hidden');
    if (submitSection) submitSection.classList.add('hidden');
    if (uploadPreview) uploadPreview.classList.add('hidden');
    if (uploadPhoto) uploadPhoto.classList.add('hidden');
    if (photoUpload) photoUpload.value = '';
    
    // Reset camera container to show video feed again
    const cameraContainer = document.getElementById('camera-container');
    if (cameraContainer) {
        cameraContainer.innerHTML = `
            <video id="camera-feed" class="w-full h-48 bg-gray-100 rounded-lg" autoplay playsinline></video>
            <canvas id="camera-canvas" class="hidden"></canvas>
        `;
    }
    
    if (stream) {
        stopCamera();
    }
    
    // Reset buttons
    const startCameraBtn = document.getElementById('start-camera');
    const capturePhotoBtn = document.getElementById('capture-photo');
    const stopCameraBtn = document.getElementById('stop-camera');
    
    if (startCameraBtn) startCameraBtn.classList.remove('hidden');
    if (capturePhotoBtn) capturePhotoBtn.classList.add('hidden');
    if (stopCameraBtn) stopCameraBtn.classList.add('hidden');
}

async function checkCurrentFaceData() {
    try {
        const response = await fetch('/api/face-data-info');
        const result = await response.json();
        
        const statusDiv = document.getElementById('face-data-status');
        const saveImageSection = document.getElementById('save-image-section');
        if (!statusDiv) return;
        
        if (result.exists) {
            statusDiv.innerHTML = `
                <div class="text-center">
                    <i class="fas fa-check-circle text-3xl text-green-500 mb-2"></i>
                    <p class="text-green-600 font-medium">Face data exists</p>
                    <p class="text-sm text-gray-500">Size: ${(result.size / 1024).toFixed(1)} KB</p>
                    <p class="text-sm text-gray-500">Created: ${new Date(result.created).toLocaleDateString()}</p>
                    <button onclick="deleteFaceData()" class="mt-3 bg-red-600 text-white py-1 px-3 rounded text-sm hover:bg-red-700">
                        <i class="fas fa-trash mr-1"></i>Delete Face Data
                    </button>
                </div>
            `;
            
            // Show save image section
            if (saveImageSection) saveImageSection.classList.remove('hidden');
        } else {
            statusDiv.innerHTML = `
                <div class="text-center">
                    <i class="fas fa-user-slash text-3xl text-gray-400 mb-2"></i>
                    <p class="text-gray-500">No face data found</p>
                    <p class="text-sm text-gray-400">Please capture your face data above</p>
                </div>
            `;
            
            // Hide save image section
            if (saveImageSection) saveImageSection.classList.add('hidden');
        }
    } catch (error) {
        const statusDiv = document.getElementById('face-data-status');
        if (statusDiv) {
            statusDiv.innerHTML = `
                <div class="text-center">
                    <i class="fas fa-exclamation-triangle text-3xl text-red-400 mb-2"></i>
                    <p class="text-red-500">Error checking face data</p>
                </div>
            `;
        }
    }
}

async function deleteFaceData() {
    if (!confirm('Are you sure you want to delete your face data? You will need to capture it again.')) {
        return;
    }
    
    try {
        const response = await fetch('/api/delete-face-data', { method: 'DELETE' });
        const result = await response.json();
        
        if (result.success) {
            checkCurrentFaceData();
        } else {
            alert('Error deleting face data: ' + result.message);
        }
    } catch (error) {
        alert('Error deleting face data: ' + error.message);
    }
}

function showStatus(elementId, message, type) {
    const statusElement = document.getElementById(elementId);
    if (!statusElement) return;
    
    statusElement.classList.remove('hidden');
    
    const statusClass = type === 'success' ? 'text-green-600 bg-green-50' : 
                        type === 'error' ? 'text-red-600 bg-red-50' : 
                        type === 'info' ? 'text-blue-600 bg-blue-50' :
                        'text-blue-600 bg-blue-50';
    
    const icon = type === 'success' ? 'fa-check-circle' : 
                type === 'error' ? 'fa-exclamation-circle' : 
                type === 'info' ? 'fa-info-circle' :
                'fa-info-circle';
    
    statusElement.innerHTML = `
        <div class="p-3 rounded-lg ${statusClass}">
            <i class="fas ${icon} mr-2"></i>
            <span class="font-medium">${message}</span>
        </div>
    `;
}

async function downloadFaceImage() {
    try {
        const response = await fetch('/api/face-image');
        const blob = await response.blob();
        
        // Create download link
        const url = window.URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.style.display = 'none';
        a.href = url;
        a.download = 'face-image.jpg';
        document.body.appendChild(a);
        a.click();
        
        // Clean up
        window.URL.revokeObjectURL(url);
        document.body.removeChild(a);
        
        showStatus('download-status', 'Image downloaded successfully!', 'success');
    } catch (error) {
        showStatus('download-status', 'Error downloading image: ' + error.message, 'error');
    }
}

function updateFaceImage() {
    // Reset the capture interface to allow taking a new photo
    resetCapture();
    
    // Scroll to the top of the page to show the camera/upload options
    window.scrollTo({ top: 0, behavior: 'smooth' });
    
    // Show a message to guide the user
    showStatus('camera-status', 'Please capture a new photo to update your face data', 'info');
    showStatus('upload-status', 'Or upload a new photo to update your face data', 'info');
    
    // Start the camera automatically
    setTimeout(() => {
        const startCameraBtn = document.getElementById('start-camera');
        if (startCameraBtn) startCameraBtn.click();
    }, 500);
}

// Make functions globally available for onclick handlers
window.deleteFaceData = deleteFaceData;
window.retryCapture = resetCapture;
window.updateFaceImage = updateFaceImage;
