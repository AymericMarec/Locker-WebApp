from flask import Flask, request, jsonify, render_template, send_from_directory, redirect, url_for, session
from flask_sqlalchemy import SQLAlchemy
import paho.mqtt.client as mqtt
import os
import secrets
import string
import datetime
from flask_sock import Sock
import json

app = Flask(__name__, 
            template_folder='templates')
app.secret_key = os.urandom(24)  # Clé secrète pour les sessions
sock = Sock(app)

# Configuration SQLAlchemy
app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql+mysqlconnector://locker:root@localhost:3306/locker'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

# Configuration MQTT
MQTT_BROKER = "localhost"
MQTT_PORT = 1883
MQTT_TOPIC_SCAN = "scan"
MQTT_TOPIC_RESPONSE = "response"

# Liste des connexions WebSocket actives
websocket_clients = set()

# Variable globale pour stocker le dernier scan
last_scan = None

# Génération d'un mot de passe aléatoire
def generate_password(length=12):
    alphabet = string.ascii_letters + string.digits
    return ''.join(secrets.choice(alphabet) for _ in range(length))

# Création du mot de passe au démarrage
PASSWORD = generate_password()
print(f"\n{'='*50}")
print(f"Mot de passe généré : {PASSWORD}")
print(f"{'='*50}\n")

# Modèle de données pour les badges
class Badge(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    uid = db.Column(db.String(50), unique=True, nullable=False)
    description = db.Column(db.String(200))
    is_authorized = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.datetime.utcnow)

    def __repr__(self):
        return f'<Badge {self.uid} - Authorized: {self.is_authorized}>'

# Configuration du dossier static pour servir les assets
@app.route('/assets/<path:path>')
def serve_assets(path):
    return send_from_directory('assets', path)

# Callbacks MQTT
def on_connect(client, userdata, flags, rc, properties=None):
    print(f"\n{'='*50}")
    print(f"[{datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] Connecté au broker MQTT avec code: {rc}")
    client.subscribe(MQTT_TOPIC_SCAN)
    print(f"[{datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] Abonné au topic '{MQTT_TOPIC_SCAN}'")
    print(f"{'='*50}\n")

def on_message(client, userdata, msg):
    global last_scan
    topic = msg.topic
    payload = msg.payload.decode()
    print(f"[{datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] Message reçu - Topic: {topic}, Payload: {payload}")

    if topic == MQTT_TOPIC_SCAN:
        last_scan = payload
        # Vérifier l'autorisation du badge dans un contexte d'application
        with app.app_context():
            badge = Badge.query.filter_by(uid=payload).first()
            if badge and badge.is_authorized:
                print(f"Badge {payload} autorisé. Envoi de 'true' sur 'response'")
                client.publish(MQTT_TOPIC_RESPONSE, "true")
            else:
                print(f"Badge {payload} non trouvé ou non autorisé. Envoi de 'false' sur 'response'")
                client.publish(MQTT_TOPIC_RESPONSE, "false")

mqtt_client = mqtt.Client(protocol=mqtt.MQTTv5)
mqtt_client.on_connect = on_connect
mqtt_client.on_message = on_message
mqtt_client.connect(MQTT_BROKER, MQTT_PORT)
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

@app.route('/badges')
def list_badges():
    if not session.get('logged_in'):
        return redirect(url_for('login'))
    badges = Badge.query.all()
    return render_template('badges.html', badges=badges)

@app.route('/badges/add', methods=['POST'])
def add_badge():
    if not session.get('logged_in'):
        return jsonify({"success": False, "error": "Non authentifié"}), 401
    
    try:
        data = request.json
        uid = data.get('uid')
        description = data.get('description')
        is_authorized = data.get('is_authorized', False)
        
        if not uid:
            return jsonify({"success": False, "error": "UID requis"}), 400
            
        badge = Badge(uid=uid, description=description, is_authorized=is_authorized)
        db.session.add(badge)
        db.session.commit()
        
        return jsonify({"success": True, "message": "Badge ajouté avec succès"})
    except Exception as e:
        db.session.rollback()
        return jsonify({"success": False, "error": str(e)}), 500

@app.route('/badges/<int:badge_id>/toggle', methods=['POST'])
def toggle_badge(badge_id):
    if not session.get('logged_in'):
        return jsonify({"success": False, "error": "Non authentifié"}), 401
    
    try:
        badge = Badge.query.get_or_404(badge_id)
        badge.is_authorized = not badge.is_authorized
        db.session.commit()
        return jsonify({"success": True, "is_authorized": badge.is_authorized})
    except Exception as e:
        db.session.rollback()
        return jsonify({"success": False, "error": str(e)}), 500

@app.route('/badges/<int:badge_id>/delete', methods=['POST'])
def delete_badge(badge_id):
    if not session.get('logged_in'):
        return jsonify({"success": False, "error": "Non authentifié"}), 401
    
    try:
        badge = Badge.query.get_or_404(badge_id)
        db.session.delete(badge)
        db.session.commit()
        return jsonify({"success": True, "message": "Badge supprimé avec succès"})
    except Exception as e:
        db.session.rollback()
        return jsonify({"success": False, "error": str(e)}), 500

@sock.route('/ws')
def websocket(ws):
    websocket_clients.add(ws)
    try:
        while True:
            # Garder la connexion active
            ws.receive()
    except Exception:
        websocket_clients.remove(ws)

@app.route('/last_scan')
def get_last_scan():
    if not session.get('logged_in'):
        return jsonify({"error": "Non authentifié"}), 401
    return jsonify({"uid": last_scan})

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
        print("Tables de la base de données vérifiées/créées.")
    print("Serveur démarré! Accédez à http://localhost:5000")
    app.run(host='0.0.0.0', port=5000, debug=False)