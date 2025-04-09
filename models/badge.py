from extensions import db
from datetime import datetime

class Badge(db.Model):
    __tablename__ = 'badges'
    
    id = db.Column(db.Integer, primary_key=True)
    uid = db.Column(db.String(50), unique=True, nullable=False)
    name = db.Column(db.String(100), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def to_dict(self):
        return {
            'id': self.id,
            'uid': self.uid,
            'name': self.name,
            'created_at': self.created_at.isoformat()
        }

    def __repr__(self):
        return f'<Badge {self.uid} - Name: {self.name}>' 