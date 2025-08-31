from models import db


class FaceEncoding(db.Model):
    __tablename__ = "face_encodings"

    id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False, unique=True)
    encoding = db.Column(db.LargeBinary, nullable=False)  # serialized numpy array

    def __repr__(self):
        return f"<FaceEncoding student_id={self.student_id}>"
