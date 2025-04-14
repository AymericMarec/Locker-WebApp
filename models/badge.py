from extensions import db
from datetime import datetime

class Locker(db.Model):
    __tablename__ = 'lockers'
    
    id = db.Column(db.Integer, primary_key=True)
    mac_address = db.Column(db.String(17), unique=True, nullable=False)
    name = db.Column(db.String(100))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    badges = db.relationship('Badge', backref='locker', lazy=True)
    
    def to_dict(self):
        return {
            'id': self.id,
            'mac_address': self.mac_address,
            'name': self.name,
            'created_at': self.created_at.isoformat()
        }

    def __repr__(self):
        return f'<Locker {self.mac_address}>'

class Badge(db.Model):
    __tablename__ = 'badges'
    
    id = db.Column(db.Integer, primary_key=True)
    uid = db.Column(db.String(50), unique=True, nullable=False)
    name = db.Column(db.String(100), nullable=False)
    is_authorized = db.Column(db.Boolean, default=True, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    locker_id = db.Column(db.Integer, db.ForeignKey('lockers.id'), nullable=True)
    
    def to_dict(self):
        return {
            'id': self.id,
            'uid': self.uid,
            'name': self.name,
            'is_authorized': self.is_authorized,
            'created_at': self.created_at.isoformat(),
            'locker_id': self.locker_id
        }

    def __repr__(self):
        return f'<Badge {self.uid} - Name: {self.name}>' 