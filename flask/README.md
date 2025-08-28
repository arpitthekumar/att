# 🎓 AI Attendance System - Multi-Role Edition

A comprehensive Flask-based attendance management system with role-based access control, featuring AI-powered face recognition for automated attendance tracking.

## ✨ Features

### 🔐 **Multi-Role System**
- **👨‍💼 Admin Dashboard**: Full system management
- **👨‍🏫 Teacher Dashboard**: Class-specific attendance and reports
- **👨‍🎓 Student Dashboard**: Personal attendance tracking

### 🎯 **Role-Based Permissions**

#### **Admin (System Administrator)**
- ✅ Manage all users (Admin, Teachers, Students)
- ✅ Create and manage classes
- ✅ Assign teachers to classes
- ✅ View system-wide statistics
- ✅ Access all attendance records
- ✅ System configuration and maintenance

#### **Teacher**
- ✅ Take attendance for assigned classes
- ✅ View class-specific attendance reports
- ✅ Export attendance data for their classes
- ✅ View student lists in their classes
- ❌ Cannot edit other teachers' data
- ❌ Cannot access other classes

#### **Student**
- ✅ View personal attendance records
- ✅ Check attendance statistics
- ✅ Filter attendance by date/status
- ❌ Cannot edit any data
- ❌ Cannot access other students' information

### 🤖 **AI Face Recognition**
- DeepFace integration for accurate face detection
- Automatic student identification
- Real-time attendance marking
- Camera integration for live capture

### 📊 **Advanced Analytics**
- Real-time attendance statistics
- Role-specific dashboards
- Comprehensive reporting system
- Data export functionality

## 🚀 Quick Start

### 1. **Installation**
```bash
# Clone the repository
git clone <repository-url>
cd flask

# Install dependencies
pip install -r requirements.txt
```

### 2. **Run the Application**
```bash
python app_sqlite.py
```

### 3. **Access the System**
Open your browser and go to: `http://localhost:5000`

## 👥 **Default Login Credentials**

### **Admin Account**
- **Username:** `admin`
- **Password:** `admin123`
- **Access:** Full system control

### **Teacher Account**
- **Username:** `teacher1`
- **Password:** `teacher123`
- **Access:** Class management and attendance

### **Student Account**
- **Username:** `student1`
- **Password:** `student123`
- **Access:** Personal attendance view

## 🏗️ **System Architecture**

### **Database Schema**
```sql
-- Users table (supports multiple roles)
users (
    id, username, password_hash, email, role, name, created_at
)

-- Classes table
classes (
    id, name, teacher_id, created_at
)

-- Students table (linked to users)
students (
    id, user_id, roll_number, class_id, face_image, created_at
)

-- Attendance table
attendance (
    id, student_id, class_id, date, time, status, created_at
)
```

### **Role Hierarchy**
```
Admin (Full Access)
├── Manage Users
├── Manage Classes
├── System Reports
└── Configuration

Teacher (Class-Specific Access)
├── Take Attendance
├── View Class Reports
├── Export Data
└── Student Management

Student (Personal Access)
├── View Attendance
├── Check Statistics
└── Personal Reports
```

## 📱 **User Interface**

### **Admin Dashboard**
- System overview with key metrics
- User management interface
- Class administration
- Recent activity feed
- Quick action buttons

### **Teacher Dashboard**
- Assigned classes overview
- Attendance taking interface
- Class-specific reports
- Student management tools

### **Student Dashboard**
- Personal attendance statistics
- Attendance history
- Performance analytics
- Quick access to records

## 🔧 **Configuration**

### **Environment Variables**
```bash
# Database Configuration
DATABASE_URL=sqlite:///attendance.db

# Face Recognition Settings
DEEPFACE_MODEL=VGG-Face
DEEPFACE_DISTANCE_METRIC=cosine

# Security Settings
SECRET_KEY=your-secret-key-here
```

### **File Structure**
```
flask/
├── app_sqlite.py          # Main application
├── config.py              # Configuration settings
├── requirements.txt       # Python dependencies
├── templates/             # HTML templates
│   ├── admin/            # Admin-specific templates
│   ├── teacher/          # Teacher-specific templates
│   ├── student/          # Student-specific templates
│   └── layout.html       # Base template
├── faces/                # Face image storage
└── attendance.db         # SQLite database
```

## 🛡️ **Security Features**

- **Password Hashing**: Secure password storage using Werkzeug
- **Session Management**: Secure user sessions
- **Role-Based Access Control**: Granular permissions
- **SQL Injection Protection**: Parameterized queries
- **CSRF Protection**: Built-in Flask security

## 📊 **Usage Guide**

### **For Administrators**

1. **User Management**
   - Navigate to "Users" section
   - Add new users with appropriate roles
   - Assign students to classes
   - Manage teacher assignments

2. **Class Management**
   - Create new classes
   - Assign teachers to classes
   - Monitor class statistics
   - View enrollment data

3. **System Monitoring**
   - Check system statistics
   - Monitor attendance trends
   - Review recent activities
   - Export system reports

### **For Teachers**

1. **Taking Attendance**
   - Select your class
   - Start face recognition session
   - Students are automatically identified
   - Attendance is marked in real-time

2. **Viewing Reports**
   - Access class-specific reports
   - Filter by date ranges
   - Export attendance data
   - Monitor student performance

3. **Student Management**
   - View enrolled students
   - Check individual attendance
   - Generate student reports

### **For Students**

1. **Checking Attendance**
   - View personal attendance records
   - Check attendance statistics
   - Filter by date or status
   - Monitor performance trends

2. **Understanding Data**
   - Attendance percentage
   - Present/absent counts
   - Historical patterns
   - Performance insights

## 🔍 **Troubleshooting**

### **Common Issues**

1. **Camera Not Working**
   - Ensure camera permissions are granted
   - Check if camera is being used by another application
   - Verify OpenCV installation

2. **Face Recognition Issues**
   - Ensure good lighting conditions
   - Position face clearly in camera view
   - Check if face images are properly stored

3. **Database Errors**
   - Verify SQLite installation
   - Check file permissions for database
   - Ensure proper database initialization

### **Performance Optimization**

1. **Face Recognition Speed**
   - Use smaller face images
   - Optimize camera resolution
   - Consider GPU acceleration

2. **Database Performance**
   - Regular database maintenance
   - Index optimization
   - Query optimization

## 🤝 **Contributing**

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Test thoroughly
5. Submit a pull request

## 📄 **License**

This project is licensed under the MIT License - see the LICENSE file for details.

## 🙏 **Acknowledgments**

- **Flask**: Web framework
- **DeepFace**: Face recognition library
- **OpenCV**: Computer vision library
- **Tailwind CSS**: Styling framework
- **Font Awesome**: Icons

## 📞 **Support**

For support and questions:
- Create an issue in the repository
- Check the troubleshooting section
- Review the documentation

---

**🎉 Enjoy using the AI Attendance System!**
