from datetime import datetime
from app import db

class AccessLog(db.Model):
    __tablename__ = 'access_logs'
    
    id = db.Column(db.Integer, primary_key=True)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow, index=True)
    success = db.Column(db.Boolean, default=False)
    message = db.Column(db.String(256))
    
    # Clés étrangères
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)
    badge_id = db.Column(db.Integer, db.ForeignKey('rfid_badges.id'), nullable=True)
    
    # Info additionnelle
    ip_address = db.Column(db.String(45))
    device_info = db.Column(db.String(256))
    
    def __init__(self, success, message=None, user_id=None, badge_id=None, ip_address=None, device_info=None):
        self.success = success
        self.message = message
        self.user_id = user_id
        self.badge_id = badge_id
        self.ip_address = ip_address
        self.device_info = device_info
    
    @classmethod
    def log_access(cls, success, message=None, user_id=None, badge_id=None, ip_address=None, device_info=None):
        log = cls(
            success=success,
            message=message,
            user_id=user_id,
            badge_id=badge_id,
            ip_address=ip_address,
            device_info=device_info
        )
        db.session.add(log)
        db.session.commit()
        return log
    
    def __repr__(self):
        status = "SUCCÈS" if self.success else "ÉCHEC"
        return f'<AccessLog {self.id} - {status} - {self.timestamp}>' 