from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_user, logout_user, login_required, current_user
from werkzeug.urls import url_parse
from werkzeug.security import generate_password_hash

from app import db
from app.models.user import User
from app.models.access_log import AccessLog
from app.forms.auth import LoginForm, ProfileForm, PasswordChangeForm

bp = Blueprint('auth', __name__, url_prefix='/auth')

@bp.route('/login', methods=['GET', 'POST'])
def login():
    """Page de connexion."""
    if current_user.is_authenticated:
        return redirect(url_for('main.dashboard'))
    
    form = LoginForm()
    
    if form.validate_on_submit():
        user = User.query.filter_by(username=form.username.data).first()
        
        if user is None or not user.check_password(form.password.data):
            flash('Nom d\'utilisateur ou mot de passe incorrect', 'danger')
            return redirect(url_for('auth.login'))
        
        if not user.is_active:
            flash('Ce compte est désactivé. Contactez l\'administrateur.', 'danger')
            return redirect(url_for('auth.login'))
        
        # Connexion de l'utilisateur
        login_user(user, remember=form.remember_me.data)
        user.update_last_login()
        
        # Journalisation de l'accès
        ip = request.remote_addr
        device = request.headers.get('User-Agent', '')
        AccessLog.log_access(
            success=True,
            message="Connexion réussie à l'interface web",
            user_id=user.id,
            ip_address=ip,
            device_info=device
        )
        
        # Redirection vers la page demandée ou la page d'accueil
        next_page = request.args.get('next')
        if not next_page or url_parse(next_page).netloc != '':
            next_page = url_for('main.dashboard')
        
        flash('Connexion réussie!', 'success')
        return redirect(next_page)
    
    return render_template('auth/login.html', form=form)

@bp.route('/logout')
@login_required
def logout():
    """Déconnexion de l'utilisateur."""
    # Journalisation de la déconnexion
    ip = request.remote_addr
    device = request.headers.get('User-Agent', '')
    AccessLog.log_access(
        success=True,
        message="Déconnexion de l'interface web",
        user_id=current_user.id,
        ip_address=ip,
        device_info=device
    )
    
    logout_user()
    flash('Vous avez été déconnecté.', 'info')
    return redirect(url_for('main.index'))

@bp.route('/profile', methods=['GET', 'POST'])
@login_required
def profile():
    """Affiche et met à jour le profil de l'utilisateur courant."""
    profile_form = ProfileForm(obj=current_user)
    password_form = PasswordChangeForm()
    
    if profile_form.validate_on_submit() and 'update_profile' in request.form:
        current_user.email = profile_form.email.data
        current_user.first_name = profile_form.first_name.data
        current_user.last_name = profile_form.last_name.data
        
        db.session.commit()
        flash('Profil mis à jour avec succès !', 'success')
        return redirect(url_for('auth.profile'))
    
    if password_form.validate_on_submit() and 'change_password' in request.form:
        if not current_user.check_password(password_form.current_password.data):
            flash('Mot de passe actuel incorrect.', 'danger')
        else:
            current_user.password_hash = generate_password_hash(password_form.new_password.data)
            db.session.commit()
            flash('Mot de passe mis à jour avec succès !', 'success')
        return redirect(url_for('auth.profile'))
    
    return render_template('auth/profile.html', 
                          user=current_user, 
                          profile_form=profile_form,
                          password_form=password_form) 