"""Services provider module.

This module provides service instances to be used across the application.
"""

from backend.auth import Auth
from backend.services import (
    UserService,
    ClassService,
    AttendanceService,
    ClassRequestService,
    DashboardService,
    ActivityService,
    AttendanceSessionService,
    FaceRecognition
)

# Initialize services
auth = Auth()
user_service = UserService()
class_service = ClassService()
attendance_service = AttendanceService()
class_request_service = ClassRequestService()
dashboard_service = DashboardService()
activity_service = ActivityService()
attendance_session_service = AttendanceSessionService()
face_recognition_service = FaceRecognition()