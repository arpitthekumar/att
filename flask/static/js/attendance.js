let stream = null;
let currentStudentId = null;
let currentStudentName = null;
let attendanceData = {};

// Initialize page
document.addEventListener('DOMContentLoaded', function() {
    setupEventListeners();
    updateAttendanceSummary();
    loadExistingAttendance();
});

function setupEventListeners() {
    const startCameraBtn = document.getElementById('start-camera');
    const stopCameraBtn = document.getElementById('stop-camera');
    const markAttendanceBtn = document.getElementById('mark-attendance');
    const exportAttendanceBtn = document.getElementById('export-attendance');
    const refreshAttendanceBtn = document.getElementById('refresh-attendance');

    if (startCameraBtn) startCameraBtn.addEventListener('click', startCamera);
    if (stopCameraBtn) stopCameraBtn.addEventListener('click', stopCamera);
    if (markAttendanceBtn) markAttendanceBtn.addEventListener('click', markAttendanceWithFace);
    if (exportAttendanceBtn) exportAttendanceBtn.addEventListener('click', exportAttendance);
    if (refreshAttendanceBtn) refreshAttendanceBtn.addEventListener('click', refreshAttendance);

    // Student selection for face recognition
    document.querySelectorAll('.student-row').forEach(row => {
        row.addEventListener('click', function() {
            // Remove previous selection
            document.querySelectorAll('.student-row').forEach(r => r.classList.remove('bg-blue-50'));
            
            // Add selection to current row
            this.classList.add('bg-blue-50');
            
            // Set current student
            currentStudentId = this.dataset.studentId;
            currentStudentName = this.dataset.studentName;
            
            // Update recognition status
            if (stream) {
                document.getElementById('recognition-status').innerHTML = `
                    <div class="text-center text-blue-600">
                        <i class="fas fa-user text-4xl mb-2"></i>
                        <p class="font-medium">Selected: ${currentStudentName}</p>
                        <p class="text-sm">Ready for face recognition</p>
                    </div>
                `;
                document.getElementById('mark-attendance').disabled = false;
            }
        });
    });
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
        document.getElementById('stop-camera').classList.remove('hidden');
        
        // Start face detection
        startFaceDetection();
        
    } catch (error) {
        alert('Error accessing camera: ' + error.message);
    }
}

function stopCamera() {
    if (stream) {
        stream.getTracks().forEach(track => track.stop());
        stream = null;
    }
    
    document.getElementById('start-camera').classList.remove('hidden');
    document.getElementById('stop-camera').classList.add('hidden');
    
    // Clear recognition status
    document.getElementById('recognition-status').innerHTML = `
        <div class="text-center text-gray-500">
            <i class="fas fa-user-slash text-4xl mb-2"></i>
            <p>No face detected</p>
            <p class="text-sm">Position your face in front of the camera</p>
        </div>
    `;
    
    document.getElementById('mark-attendance').disabled = true;
    currentStudentId = null;
    currentStudentName = null;
}

function startFaceDetection() {
    const video = document.getElementById('camera-feed');
    const canvas = document.getElementById('camera-canvas');
    const context = canvas.getContext('2d');
    
    function detectFaces() {
        if (!stream) return;
        
        canvas.width = video.videoWidth;
        canvas.height = video.videoHeight;
        context.drawImage(video, 0, 0);
        
        // Here you would integrate with face detection API
        // For now, we'll simulate face detection
        setTimeout(() => {
            // Simulate face detection result
            const hasFace = Math.random() > 0.3; // 70% chance of detecting a face
            
            if (hasFace) {
                showFaceDetected();
            } else {
                showNoFace();
            }
            
            if (stream) {
                requestAnimationFrame(detectFaces);
            }
        }, 1000);
    }
    
    detectFaces();
}

function showFaceDetected() {
    document.getElementById('recognition-status').innerHTML = `
        <div class="text-center text-green-600">
            <i class="fas fa-user-check text-4xl mb-2"></i>
            <p class="font-medium">Face Detected</p>
            <p class="text-sm">Ready for recognition</p>
        </div>
    `;
    
    document.getElementById('mark-attendance').disabled = false;
}

function showNoFace() {
    document.getElementById('recognition-status').innerHTML = `
        <div class="text-center text-gray-500">
            <i class="fas fa-user-slash text-4xl mb-2"></i>
            <p>No face detected</p>
            <p class="text-sm">Position your face in front of the camera</p>
        </div>
    `;
    
    document.getElementById('mark-attendance').disabled = true;
}

async function markAttendanceWithFace() {
    if (!currentStudentId) {
        alert('Please select a student first');
        return;
    }
    
    try {
        const response = await fetch('/teacher/attendance/start', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                class_id: getClassId(),
                student_id: currentStudentId
            })
        });
        
        const result = await response.json();
        
        if (result.success) {
            updateStudentAttendance(currentStudentId, 'present', new Date().toLocaleTimeString());
            showNotification('Attendance marked successfully!', 'success');
        } else {
            showNotification('Failed to mark attendance: ' + result.message, 'error');
        }
    } catch (error) {
        showNotification('Error marking attendance: ' + error.message, 'error');
    }
}

async function markAttendance(studentId, status) {
    try {
        const response = await fetch('/api/mark-attendance-manual', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                student_id: studentId,
                class_id: getClassId(),
                status: status
            })
        });
        
        const result = await response.json();
        
        if (result.success) {
            updateStudentAttendance(studentId, status, new Date().toLocaleTimeString());
            showNotification(`Attendance marked as ${status}`, 'success');
        } else {
            showNotification('Failed to mark attendance: ' + result.message, 'error');
        }
    } catch (error) {
        showNotification('Error marking attendance: ' + error.message, 'error');
    }
}

function updateStudentAttendance(studentId, status, time) {
    const row = document.querySelector(`[data-student-id="${studentId}"]`);
    if (!row) return;
    
    const statusCell = row.querySelector('.attendance-status');
    const timeCell = row.querySelector('.attendance-time');
    
    // Update status
    statusCell.className = `attendance-status px-2 inline-flex text-xs leading-5 font-semibold rounded-full ${
        status === 'present' ? 'bg-green-100 text-green-800' :
        status === 'absent' ? 'bg-red-100 text-red-800' :
        'bg-yellow-100 text-yellow-800'
    }`;
    statusCell.textContent = status.charAt(0).toUpperCase() + status.slice(1);
    
    // Update time
    timeCell.textContent = time;
    
    // Update attendance data
    attendanceData[studentId] = { status, time };
    
    updateAttendanceSummary();
}

function updateAttendanceSummary() {
    const present = Object.values(attendanceData).filter(a => a.status === 'present').length;
    const absent = Object.values(attendanceData).filter(a => a.status === 'absent').length;
    const late = Object.values(attendanceData).filter(a => a.status === 'late').length;
    const total = getStudentCount();
    const rate = total > 0 ? Math.round((present / total) * 100) : 0;
    
    const presentCount = document.getElementById('present-count');
    const absentCount = document.getElementById('absent-count');
    const lateCount = document.getElementById('late-count');
    const attendanceRate = document.getElementById('attendance-rate');
    
    if (presentCount) presentCount.textContent = present;
    if (absentCount) absentCount.textContent = absent;
    if (lateCount) lateCount.textContent = late;
    if (attendanceRate) attendanceRate.textContent = rate + '%';
}

function loadExistingAttendance() {
    // Load existing attendance data from the server
    const existingAttendance = getExistingAttendance();
    existingAttendance.forEach(record => {
        if (record.student_id) {
            updateStudentAttendance(record.student_id, record.status, record.time);
        }
    });
}

function refreshAttendance() {
    location.reload();
}

function exportAttendance() {
    // Create CSV data
    const csvData = [
        ['Student Name', 'Roll Number', 'Status', 'Time', 'Date'],
        ...Object.entries(attendanceData).map(([studentId, data]) => {
            const student = getStudentById(studentId);
            return [
                student ? student.name : 'Unknown',
                student ? (student.roll_number || 'N/A') : 'N/A',
                data.status,
                data.time,
                getCurrentDate()
            ];
        })
    ];
    
    const csvContent = csvData.map(row => row.join(',')).join('\n');
    const blob = new Blob([csvContent], { type: 'text/csv' });
    const url = window.URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `attendance_${getClassName()}_${getCurrentDate()}.csv`;
    a.click();
    window.URL.revokeObjectURL(url);
}

function showNotification(message, type) {
    // Create notification element
    const notification = document.createElement('div');
    notification.className = `fixed top-4 right-4 p-4 rounded-lg shadow-lg z-50 ${
        type === 'success' ? 'bg-green-500 text-white' : 'bg-red-500 text-white'
    }`;
    notification.innerHTML = `
        <div class="flex items-center">
            <i class="fas ${type === 'success' ? 'fa-check-circle' : 'fa-exclamation-circle'} mr-2"></i>
            <span>${message}</span>
        </div>
    `;
    
    document.body.appendChild(notification);
    
    // Remove after 3 seconds
    setTimeout(() => {
        notification.remove();
    }, 3000);
}

// Helper functions to get data from the page
function getClassId() {
    return document.querySelector('[data-class-id]')?.dataset.classId || '';
}

function getClassName() {
    return document.querySelector('[data-class-name]')?.dataset.className || 'Class';
}

function getStudentCount() {
    return document.querySelectorAll('.student-row').length;
}

function getCurrentDate() {
    return new Date().toISOString().split('T')[0];
}

function getExistingAttendance() {
    const attendanceElement = document.getElementById('existing-attendance-data');
    return attendanceElement ? JSON.parse(attendanceElement.textContent || '[]') : [];
}

function getStudentById(studentId) {
    const studentRow = document.querySelector(`[data-student-id="${studentId}"]`);
    if (!studentRow) return null;
    
    return {
        id: studentId,
        name: studentRow.dataset.studentName,
        roll_number: studentRow.dataset.rollNumber
    };
}
