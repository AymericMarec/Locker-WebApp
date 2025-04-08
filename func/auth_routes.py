from flask import render_template, request, session, redirect, url_for, jsonify
from app import app
import secrets
import string

PASSWORD = "IjqgVZldHWol"

print(f"Mot de passe : {PASSWORD}")


@app.route('/')
def index():
    if not session.get('logged_in'):
        return redirect(url_for('login'))
    return render_template('index.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        user_id = request.form.get('userId')
        print(f"\nTentative de connexion:")
        print(f"Mot de passe saisi: {user_id}")
        print(f"Mot de passe attendu: {PASSWORD}")
        print(f"Les mots de passe correspondent: {user_id == PASSWORD}\n")
        
        if user_id == PASSWORD:
            session['logged_in'] = True
            print("Connexion réussie!")
            return redirect(url_for('index'))
        else:
            print("Échec de la connexion!")
            return render_template('login.html', error="Mot de passe incorrect")
    return render_template('login.html')

@app.route('/logout')
def logout():
    session.pop('logged_in', None)
    return redirect(url_for('login')) 