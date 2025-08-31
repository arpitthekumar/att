from models import db


class User(db.Model):
    __tablename__ = "users"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    role = db.Column(db.String(20), nullable=False)  # admin, teacher, student
    password = db.Column(db.String(200), nullable=False)
    phone_number = db.Column(db.String(20))
    parent_contact = db.Column(db.String(120))
    address = db.Column(db.String(255))

    # Relationships
    classes = db.relationship("Class", backref="teacher", lazy=True)
    activities = db.relationship("Activity", backref="user", lazy=True)
    face_encoding = db.relationship("FaceEncoding", backref="student", uselist=False)

    def __repr__(self):
        return f"<User {self.name} ({self.role})>"
