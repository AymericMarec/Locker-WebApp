from flask import Blueprint, render_template, redirect, url_for, flash, request, current_app
from flask_login import login_required, current_user
from datetime import datetime, timedelta

from app import db
from app.models.access_log import AccessLog
from app.models.rfid import RFIDBadge

bp = Blueprint('main', __name__)

@bp.route('/')
def index():
    """Page d'accueil de l'application."""
    if current_user.is_authenticated:
        return redirect(url_for('main.dashboard'))
    return render_template('index.html')

@bp.route('/dashboard')
@login_required
def dashboard():
    """Tableau de bord principal pour les utilisateurs connectés."""
    # Récupérer les statistiques pour le tableau de bord
    
    # Logs des 24 dernières heures
    since = datetime.utcnow() - timedelta(days=1)
    recent_logs = AccessLog.query.filter(AccessLog.timestamp >= since).order_by(AccessLog.timestamp.desc()).limit(10).all()
    
    # Nombre d'accès par jour (7 derniers jours)
    daily_stats = []
    for i in range(7, 0, -1):
        day = datetime.utcnow() - timedelta(days=i)
        next_day = datetime.utcnow() - timedelta(days=i-1)
        count = AccessLog.query.filter(
            AccessLog.timestamp >= day,
            AccessLog.timestamp < next_day
        ).count()
        daily_stats.append({
            'date': day.strftime('%d/%m'),
            'count': count
        })
    
    # Statistiques des badges RFID
    total_badges = RFIDBadge.query.count()
    active_badges = RFIDBadge.query.filter_by(is_active=True).count()
    
    # Statistiques d'accès
    total_access = AccessLog.query.count()
    successful_access = AccessLog.query.filter_by(success=True).count()
    failed_access = AccessLog.query.filter_by(success=False).count()
    
    success_rate = 0
    if total_access > 0:
        success_rate = (successful_access / total_access) * 100
    
    return render_template('dashboard.html',
                          recent_logs=recent_logs,
                          daily_stats=daily_stats,
                          total_badges=total_badges,
                          active_badges=active_badges,
                          total_access=total_access,
                          successful_access=successful_access,
                          failed_access=failed_access,
                          success_rate=success_rate)

@bp.route('/logs')
@login_required
def logs():
    """Affiche les journaux d'accès."""
    page = request.args.get('page', 1, type=int)
    per_page = 20
    
    logs = AccessLog.query.order_by(AccessLog.timestamp.desc()).paginate(
        page=page, per_page=per_page, error_out=False)
    
    return render_template('logs.html', logs=logs)

@bp.route('/badges')
@login_required
def badges():
    """Affiche la liste des badges RFID."""
    page = request.args.get('page', 1, type=int)
    per_page = 20
    
    badges = RFIDBadge.query.order_by(RFIDBadge.badge_id).paginate(
        page=page, per_page=per_page, error_out=False)
    
    return render_template('badges.html', badges=badges) 