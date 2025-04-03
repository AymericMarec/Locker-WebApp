import os
from flask import Blueprint, jsonify, request, current_app
from functools import wraps
from datetime import datetime

from app import db
from app.models.rfid import RFIDBadge
from app.models.access_log import AccessLog

bp = Blueprint('api', __name__, url_prefix='/api')

def require_api_key(f):
    """Décorateur pour vérifier la clé API."""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        api_key = request.headers.get('X-API-KEY')
        expected_key = os.environ.get('IOT_API_KEY')
        
        if not api_key or api_key != expected_key:
            return jsonify({"status": "error", "message": "Clé API invalide"}), 401
        
        return f(*args, **kwargs)
    return decorated_function

@bp.route('/rfid/check', methods=['POST'])
@require_api_key
def check_rfid():
    """Point d'entrée pour vérifier un badge RFID."""
    data = request.get_json()
    
    if not data or 'badge_id' not in data:
        return jsonify({
            "status": "error",
            "message": "Le badge_id est requis"
        }), 400
    
    badge_id = data['badge_id']
    device_info = data.get('device_info', '')
    
    # Recherche du badge dans la base de données
    badge = RFIDBadge.query.filter_by(badge_id=badge_id).first()
    
    if not badge:
        # Journaliser la tentative d'accès échouée
        AccessLog.log_access(
            success=False,
            message="Badge inconnu",
            badge_id=None,
            ip_address=request.remote_addr,
            device_info=device_info
        )
        
        return jsonify({
            "status": "error",
            "message": "Badge inconnu",
            "access_granted": False
        }), 404
    
    # Vérifier si le badge est actif
    if not badge.is_active:
        # Journaliser la tentative d'accès échouée
        AccessLog.log_access(
            success=False,
            message="Badge inactif",
            badge_id=badge.id,
            user_id=badge.user_id,
            ip_address=request.remote_addr,
            device_info=device_info
        )
        
        return jsonify({
            "status": "error",
            "message": "Badge inactif",
            "access_granted": False
        }), 403
    
    # Mettre à jour la date de dernière utilisation
    badge.update_last_used()
    
    # Journaliser l'accès réussi
    AccessLog.log_access(
        success=True,
        message="Accès autorisé",
        badge_id=badge.id,
        user_id=badge.user_id,
        ip_address=request.remote_addr,
        device_info=device_info
    )
    
    return jsonify({
        "status": "success",
        "message": "Accès autorisé",
        "access_granted": True,
        "user_id": badge.user_id,
        "badge_name": badge.name
    })

@bp.route('/rfid/logs', methods=['GET'])
@require_api_key
def get_logs():
    """Récupérer les derniers logs d'accès."""
    limit = request.args.get('limit', 10, type=int)
    
    logs = AccessLog.query.order_by(AccessLog.timestamp.desc()).limit(limit).all()
    
    log_list = []
    for log in logs:
        log_data = {
            "id": log.id,
            "timestamp": log.timestamp.isoformat(),
            "success": log.success,
            "message": log.message,
            "user_id": log.user_id,
            "badge_id": log.badge_id,
            "ip_address": log.ip_address,
            "device_info": log.device_info
        }
        log_list.append(log_data)
    
    return jsonify({
        "status": "success",
        "count": len(log_list),
        "logs": log_list
    }) 