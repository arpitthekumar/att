from datetime import datetime
from models import db


class AttendanceSheet(db.Model):
    __tablename__ = "attendance_sheets"

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    class_id = db.Column(db.Integer, db.ForeignKey("classes.id"), nullable=False)
    teacher_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    date = db.Column(db.Date, nullable=False, default=datetime.utcnow().date)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    # Relationships
    records = db.relationship("AttendanceRecord", backref="sheet", cascade="all, delete-orphan")
    teacher = db.relationship("User", backref="sheets", foreign_keys=[teacher_id])

    def __repr__(self):
        return f"<AttendanceSheet id={self.id}, class_id={self.class_id}, date={self.date}>"


class AttendanceRecord(db.Model):
    __tablename__ = "attendance_records"

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    sheet_id = db.Column(db.Integer, db.ForeignKey("attendance_sheets.id"), nullable=False)
    student_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    status = db.Column(db.String(20), nullable=False)  # Present / Absent / Late / Excused
    marked_at = db.Column(db.DateTime, default=datetime.utcnow)

    # Relationships
    student = db.relationship("User", backref="attendance_records", foreign_keys=[student_id])

    def __repr__(self):
        return f"<AttendanceRecord student_id={self.student_id}, status={self.status}, marked_at={self.marked_at}>"
