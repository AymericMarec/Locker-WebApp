from extensions import db
import datetime

class Badge(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    uid = db.Column(db.String(50), unique=True, nullable=False)
    is_authorized = db.Column(db.Boolean, default=False)
    description = db.Column(db.String(200))
    created_at = db.Column(db.DateTime, default=datetime.datetime.utcnow)

    def __repr__(self):
        return f'<Badge {self.uid} - Authorized: {self.is_authorized}>' 