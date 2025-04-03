from flask import Flask, request, jsonify, render_template, send_from_directory, redirect, url_for, session
import paho.mqtt.client as mqtt
import os
import secrets
import string

app = Flask(__name__, 
            template_folder='templates')
app.secret_key = os.urandom(24)  # Clé secrète pour les sessions

# Génération d'un mot de passe aléatoire
def generate_password(length=12):
    alphabet = string.ascii_letters + string.digits
    return ''.join(secrets.choice(alphabet) for _ in range(length))

# Création du mot de passe au démarrage
PASSWORD = generate_password()
print(f"\n{'='*50}")
print(f"Mot de passe généré : {PASSWORD}")
print(f"{'='*50}\n")

# Configuration du dossier static pour servir les assets
@app.route('/assets/<path:path>')
def serve_assets(path):
    return send_from_directory('assets', path)

mqtt_client = mqtt.Client(protocol=mqtt.MQTTv5)
mqtt_client.connect("localhost", 1883, 60)
mqtt_client.loop_start()

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

@app.route('/publish', methods=['POST'])
def publish_message():
    if not session.get('logged_in'):
        return jsonify({"success": False, "error": "Non authentifié"}), 401
        
    try:
        data = request.json
        topic = data.get('topic')
        message = data.get('message')
        
        if not topic or not message:
            return jsonify({"success": False, "error": "Topic et message requis"}), 400
        
        result = mqtt_client.publish(topic, message)
        
        if result.rc == mqtt.MQTT_ERR_SUCCESS:
            return jsonify({"success": True})
        else:
            return jsonify({"success": False, "error": f"Erreur MQTT: {result.rc}"}), 500
    
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

if __name__ == '__main__':
    print("Serveur démarré! Accédez à http://localhost:5000")
    app.run(host='0.0.0.0', port=5000, debug=True)