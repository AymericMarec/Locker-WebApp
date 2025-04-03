from datetime import datetime
from app import db

class RFIDBadge(db.Model):
    __tablename__ = 'rfid_badges'
    
    id = db.Column(db.Integer, primary_key=True)
    badge_id = db.Column(db.String(64), unique=True, index=True)
    name = db.Column(db.String(64))
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    last_used = db.Column(db.DateTime, nullable=True)
    
    # Clé étrangère vers l'utilisateur
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    
    # Relation avec les logs d'accès
    access_logs = db.relationship('AccessLog', backref='badge', lazy='dynamic')
    
    def __init__(self, badge_id, name, user_id=None):
        self.badge_id = badge_id
        self.name = name
        self.user_id = user_id
    
    def update_last_used(self):
        self.last_used = datetime.utcnow()
        db.session.commit()
    
    def __repr__(self):
        return f'<RFIDBadge {self.badge_id}>' 