let stream = null;
let currentStudentId = null;
let currentStudentName = null;
let attendanceData = {};

// Initialize page
document.addEventListener('DOMContentLoaded', function() {
    setupEventListeners();
    updateAttendanceSummary();
    loadExistingAttendance();
    
    // Set default dates
    const today = new Date().toISOString().split('T')[0];
    document.getElementById('start-date').value = today;
    document.getElementById('end-date').value = today;
});

function setupEventListeners() {
    const startCameraBtn = document.getElementById('start-camera');
    const stopCameraBtn = document.getElementById('stop-camera');
    const markAttendanceBtn = document.getElementById('mark-attendance');
    const exportAttendanceBtn = document.getElementById('export-attendance');
    const refreshAttendanceBtn = document.getElementById('refresh-attendance');
    const loadDateRangeBtn = document.getElementById('load-date-range');

    if (startCameraBtn) startCameraBtn.addEventListener('click', startCamera);
    if (stopCameraBtn) stopCameraBtn.addEventListener('click', stopCamera);
    if (markAttendanceBtn) markAttendanceBtn.addEventListener('click', markAttendanceWithFace);
    if (exportAttendanceBtn) exportAttendanceBtn.addEventListener('click', exportAttendance);
    if (refreshAttendanceBtn) refreshAttendanceBtn.addEventListener('click', refreshAttendance);
    if (loadDateRangeBtn) loadDateRangeBtn.addEventListener('click', loadDateRangeAttendance);

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
    
    // Get attendance type and remarks
    const attendanceType = document.getElementById('attendance-type').value;
    const remarks = document.getElementById('attendance-remarks').value;
    
    try {
        const response = await fetch('/teacher/attendance/start', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                class_id: getClassId(),
                student_id: currentStudentId,
                attendance_type: attendanceType,
                remarks: remarks
            })
        });
        
        const result = await response.json();
        
        if (result.success) {
            updateStudentAttendance(currentStudentId, 'present', new Date().toLocaleTimeString(), attendanceType, remarks);
            showNotification('Attendance marked successfully!', 'success');
            
            // Clear remarks field after successful attendance marking
            document.getElementById('attendance-remarks').value = '';
        } else {
            showNotification('Failed to mark attendance: ' + result.message, 'error');
        }
    } catch (error) {
        showNotification('Error marking attendance: ' + error.message, 'error');
    }
}

async function markAttendance(studentId, status) {
    // Get attendance type and remarks
    const attendanceType = document.getElementById('attendance-type').value;
    const remarks = document.getElementById('attendance-remarks').value;
    
    try {
        const response = await fetch('/api/mark-attendance-manual', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                student_id: studentId,
                class_id: getClassId(),
                status: status,
                attendance_type: attendanceType,
                remarks: remarks
            })
        });
        
        const result = await response.json();
        
        if (result.success) {
            updateStudentAttendance(studentId, status, new Date().toLocaleTimeString(), attendanceType, remarks);
            showNotification(`Attendance marked as ${status}`, 'success');
            
            // Clear remarks field after successful attendance marking
            document.getElementById('attendance-remarks').value = '';
        } else {
            showNotification('Failed to mark attendance: ' + result.message, 'error');
        }
    } catch (error) {
        showNotification('Error marking attendance: ' + error.message, 'error');
    }
}

function updateStudentAttendance(studentId, status, time, attendanceType = 'regular', remarks = '') {
    const row = document.querySelector(`[data-student-id="${studentId}"]`);
    if (!row) return;
    
    const statusCell = row.querySelector('.attendance-status');
    const timeCell = row.querySelector('.attendance-time');
    const typeCell = row.querySelector('.attendance-type');
    const remarksCell = row.querySelector('.attendance-remarks');
    
    // Update status
    statusCell.className = `attendance-status px-2 inline-flex text-xs leading-5 font-semibold rounded-full ${
        status === 'present' ? 'bg-green-100 text-green-800' :
        status === 'absent' ? 'bg-red-100 text-red-800' :
        'bg-yellow-100 text-yellow-800'
    }`;
    statusCell.textContent = status.charAt(0).toUpperCase() + status.slice(1);
    
    // Update time
    timeCell.textContent = time;
    
    // Update attendance type
    if (typeCell) {
        typeCell.textContent = attendanceType.charAt(0).toUpperCase() + attendanceType.slice(1);
    }
    
    // Update remarks
    if (remarksCell) {
        remarksCell.textContent = remarks || '-';
    }
    
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

function loadDateRangeAttendance() {
    const startDate = document.getElementById('start-date').value;
    const endDate = document.getElementById('end-date').value;
    const classId = document.querySelector('[data-class-id]').dataset.classId;
    
    if (!startDate || !endDate) {
        showNotification('Please select both start and end dates', 'error');
        return;
    }
    
    if (new Date(startDate) > new Date(endDate)) {
        showNotification('Start date cannot be after end date', 'error');
        return;
    }
    
    // Show loading state
    document.getElementById('student-list').innerHTML = '<tr><td colspan="7" class="px-6 py-4 text-center">Loading attendance data...</td></tr>';
    
    // Fetch attendance data for date range
    fetch(`/api/attendance/class/${classId}/range?start_date=${startDate}&end_date=${endDate}`)
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                // Update the student list with the date range data
                updateStudentListWithDateRange(data.attendance);
                showNotification('Attendance data loaded for selected date range', 'success');
            } else {
                showNotification(data.message || 'Failed to load attendance data', 'error');
                document.getElementById('student-list').innerHTML = '<tr><td colspan="7" class="px-6 py-4 text-center">No attendance data available</td></tr>';
            }
        })
        .catch(error => {
            console.error('Error loading date range attendance:', error);
            showNotification('An error occurred while loading attendance data', 'error');
            document.getElementById('student-list').innerHTML = '<tr><td colspan="7" class="px-6 py-4 text-center">Error loading attendance data</td></tr>';
        });
}

function updateStudentListWithDateRange(attendanceData) {
    const studentList = document.getElementById('student-list');
    studentList.innerHTML = '';
    
    if (!attendanceData || attendanceData.length === 0) {
        studentList.innerHTML = '<tr><td colspan="7" class="px-6 py-4 text-center">No attendance data available for this date range</td></tr>';
        return;
    }
    
    // Group attendance by student
    const studentAttendance = {};
    attendanceData.forEach(record => {
        if (!studentAttendance[record.id]) {
            studentAttendance[record.id] = {
                id: record.id,
                name: record.name,
                roll_number: record.roll_number || 'N/A',
                dates: {}
            };
        }
        
        if (record.date) {
            studentAttendance[record.id].dates[record.date] = {
                status: record.status || 'absent',
                time: record.time || 'N/A',
                remarks: record.remarks || '',
                attendance_type: record.attendance_type || 'regular'
            };
        }
    });
    
    // Create a row for each student with their attendance data
    Object.values(studentAttendance).forEach(student => {
        const row = document.createElement('tr');
        row.className = 'hover:bg-gray-50';
        row.dataset.studentId = student.id;
        
        // Calculate attendance statistics
        const totalDays = Object.keys(student.dates).length;
        const presentDays = Object.values(student.dates).filter(d => d.status === 'present').length;
        const lateDays = Object.values(student.dates).filter(d => d.status === 'late').length;
        const absentDays = totalDays - presentDays - lateDays;
        const attendanceRate = totalDays > 0 ? Math.round((presentDays + lateDays) / totalDays * 100) : 0;
        
        row.innerHTML = `
            <td class="px-6 py-4 whitespace-nowrap">
                <div class="flex items-center">
                    <div class="ml-4">
                        <div class="text-sm font-medium text-gray-900">${student.name}</div>
                    </div>
                </div>
            </td>
            <td class="px-6 py-4 whitespace-nowrap">
                <div class="text-sm text-gray-900">${student.roll_number}</div>
            </td>
            <td class="px-6 py-4 whitespace-nowrap">
                <div class="text-sm">
                    <span class="font-medium">Present:</span> ${presentDays}<br>
                    <span class="font-medium">Late:</span> ${lateDays}<br>
                    <span class="font-medium">Absent:</span> ${absentDays}<br>
                    <span class="font-medium">Rate:</span> ${attendanceRate}%
                </div>
            </td>
            <td class="px-6 py-4 whitespace-nowrap">
                <div class="text-sm text-gray-900">Multiple</div>
            </td>
            <td class="px-6 py-4 whitespace-nowrap">
                <div class="text-sm text-gray-900">Multiple dates</div>
            </td>
            <td class="px-6 py-4 whitespace-nowrap">
                <div class="text-sm text-gray-900">Various</div>
            </td>
            <td class="px-6 py-4 whitespace-nowrap text-right text-sm font-medium">
                <button class="text-blue-600 hover:text-blue-900 view-details" data-student-id="${student.id}">
                    <i class="fas fa-eye mr-1"></i>Details
                </button>
            </td>
        `;
        
        studentList.appendChild(row);
    });
    
    // Add event listeners for the view details buttons
    document.querySelectorAll('.view-details').forEach(button => {
        button.addEventListener('click', function() {
            const studentId = this.dataset.studentId;
            const student = studentAttendance[studentId];
            showAttendanceDetails(student);
        });
    });
    
    // Update attendance summary
    updateAttendanceSummaryForDateRange(studentAttendance);
}

function updateAttendanceSummaryForDateRange(studentAttendance) {
    // Calculate overall statistics
    let totalPresent = 0;
    let totalLate = 0;
    let totalAbsent = 0;
    let totalDays = 0;
    
    Object.values(studentAttendance).forEach(student => {
        Object.values(student.dates).forEach(date => {
            totalDays++;
            if (date.status === 'present') totalPresent++;
            else if (date.status === 'late') totalLate++;
            else totalAbsent++;
        });
    });
    
    const attendanceRate = totalDays > 0 ? Math.round((totalPresent + totalLate) / totalDays * 100) : 0;
    
    // Update the UI
    document.getElementById('present-count').textContent = totalPresent;
    document.getElementById('late-count').textContent = totalLate;
    document.getElementById('absent-count').textContent = totalAbsent;
    document.getElementById('attendance-rate').textContent = `${attendanceRate}%`;
}

function showAttendanceDetails(student) {
    // Create a modal to show detailed attendance for the student
    const modal = document.createElement('div');
    modal.className = 'fixed inset-0 bg-gray-600 bg-opacity-50 overflow-y-auto h-full w-full flex items-center justify-center';
    modal.style.zIndex = '100';
    
    // Sort dates in descending order
    const sortedDates = Object.keys(student.dates).sort((a, b) => new Date(b) - new Date(a));
    
    let dateRows = '';
    sortedDates.forEach(date => {
        const attendance = student.dates[date];
        const statusClass = attendance.status === 'present' ? 'text-green-600' : 
                           attendance.status === 'late' ? 'text-yellow-600' : 'text-red-600';
        
        dateRows += `
            <tr class="border-b">
                <td class="py-2 px-4">${formatDate(date)}</td>
                <td class="py-2 px-4"><span class="${statusClass} font-medium">${capitalizeFirstLetter(attendance.status)}</span></td>
                <td class="py-2 px-4">${attendance.attendance_type}</td>
                <td class="py-2 px-4">${attendance.time}</td>
                <td class="py-2 px-4">${attendance.remarks || '-'}</td>
            </tr>
        `;
    });
    
    modal.innerHTML = `
        <div class="bg-white rounded-lg shadow-xl p-6 m-4 max-w-4xl w-full">
            <div class="flex justify-between items-center mb-4">
                <h3 class="text-xl font-bold text-gray-900">Attendance Details: ${student.name}</h3>
                <button class="text-gray-400 hover:text-gray-500" id="close-details-modal">
                    <i class="fas fa-times"></i>
                </button>
            </div>
            <div class="mb-4">
                <p class="text-sm text-gray-600">Roll Number: ${student.roll_number}</p>
            </div>
            <div class="overflow-x-auto">
                <table class="min-w-full bg-white">
                    <thead class="bg-gray-100">
                        <tr>
                            <th class="py-2 px-4 text-left">Date</th>
                            <th class="py-2 px-4 text-left">Status</th>
                            <th class="py-2 px-4 text-left">Type</th>
                            <th class="py-2 px-4 text-left">Time</th>
                            <th class="py-2 px-4 text-left">Remarks</th>
                        </tr>
                    </thead>
                    <tbody>
                        ${dateRows}
                    </tbody>
                </table>
            </div>
        </div>
    `;
    
    document.body.appendChild(modal);
    
    // Add event listener to close the modal
    document.getElementById('close-details-modal').addEventListener('click', function() {
        document.body.removeChild(modal);
    });
}

function formatDate(dateString) {
    const date = new Date(dateString);
    return date.toLocaleDateString('en-US', { year: 'numeric', month: 'short', day: 'numeric' });
}

function capitalizeFirstLetter(string) {
    return string.charAt(0).toUpperCase() + string.slice(1);
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
