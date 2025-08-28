# Backend Structure Documentation

## Overview
The application now uses a clean, modular backend structure with separate concerns and proper separation of layers.

## Backend Folder Structure

```
flask/
├── backend/
│   ├── __init__.py              # Package initialization
│   ├── database.py              # Database connection and initialization
│   ├── models.py                # Data models and database operations
│   ├── auth.py                  # Authentication and authorization
│   ├── face_recognition.py      # Face recognition functionality
│   └── services.py              # Business logic layer
├── templates/                   # HTML templates
├── app.py                       # Main Flask application (routes only)
├── requirements.txt             # Python dependencies
└── README.md                    # Main documentation
```

## Backend Modules

### 1. `backend/database.py`
- **Purpose**: Database connection and schema initialization
- **Key Classes**: `Database`
- **Responsibilities**:
  - SQLite database connection management
  - Table creation and schema definition
  - Default data insertion

### 2. `backend/models.py`
- **Purpose**: Data models and database operations
- **Key Classes**: `User`, `Class`, `ClassAssignment`, `Attendance`, `ClassRequest`
- **Responsibilities**:
  - CRUD operations for all entities
  - Database queries and data manipulation
  - Data validation and integrity

### 3. `backend/auth.py`
- **Purpose**: Authentication and authorization
- **Key Classes**: `Auth`
- **Key Functions**: `login_required`, `admin_required`, `teacher_required`, `student_required`
- **Responsibilities**:
  - User authentication
  - Session management
  - Role-based access control
  - Authorization decorators

### 4. `backend/face_recognition.py`
- **Purpose**: Face recognition functionality
- **Key Classes**: `FaceRecognition`
- **Responsibilities**:
  - Face capture and storage
  - Face recognition using DeepFace
  - Camera management
  - Face data management

### 5. `backend/services.py`
- **Purpose**: Business logic layer
- **Key Classes**: `UserService`, `ClassService`, `AttendanceService`, `ClassRequestService`, `DashboardService`
- **Responsibilities**:
  - Business logic implementation
  - Service orchestration
  - Data aggregation for dashboards
  - Complex operations coordination

## Main Application (`app.py`)

The main Flask application is now clean and focused only on:
- Route definitions
- Request/response handling
- Template rendering
- Service coordination

## Key Features

### Multi-Role System
- **Admin**: Full system access, user management, class management, request approval
- **Teacher**: Class management, attendance taking, reports, class requests
- **Student**: View own attendance, personal dashboard

### Class Management
- Multiple teachers per class
- Multiple students per class
- Class request system for teachers
- Admin approval workflow

### Face Recognition
- Face capture for students
- Face verification for attendance
- Secure face data storage

### Attendance System
- Face-based attendance marking
- Class-specific attendance tracking
- Attendance statistics and reports
- CSV export functionality

## Files That Are No Longer Needed

The following files have been removed and their functionality moved to the backend:

1. `models.py` (root) → `backend/models.py`
2. `auth.py` (root) → `backend/auth.py`
3. `app_sqlite.py` → `app.py` (refactored)
4. `config.py` → Integrated into `backend/database.py`

## Benefits of This Structure

1. **Separation of Concerns**: Each module has a specific responsibility
2. **Maintainability**: Easy to modify and extend individual components
3. **Testability**: Services can be tested independently
4. **Scalability**: Easy to add new features without affecting existing code
5. **Clean Code**: Main app file is focused only on routing
6. **Reusability**: Services can be reused across different routes

## Usage

To run the application:
```bash
cd flask
python app.py
```

The application will automatically:
1. Initialize the database with proper schema
2. Create default users (admin, teacher, student)
3. Set up default class and assignments
4. Start the Flask development server

## Default Credentials

- **Admin**: username: `admin`, password: `admin123`
- **Teacher**: username: `teacher1`, password: `teacher123`
- **Student**: username: `student1`, password: `student123`
