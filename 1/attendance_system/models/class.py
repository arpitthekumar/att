from models import db


class Class(db.Model):
    __tablename__ = "classes"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120), nullable=False)
    teacher_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)

    # Relationships
    students = db.relationship("ClassStudent", backref="class_", lazy=True)
    attendance_sheets = db.relationship("AttendanceSheet", backref="class_", lazy=True)

    def __repr__(self):
        return f"<Class {self.name}>"


class ClassStudent(db.Model):
    __tablename__ = "class_students"

    id = db.Column(db.Integer, primary_key=True)
    class_id = db.Column(db.Integer, db.ForeignKey("classes.id"), nullable=False)
    student_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)

    def __repr__(self):
        return f"<ClassStudent class={self.class_id}, student={self.student_id}>"
