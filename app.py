from flask import Flask, send_from_directory
import os
from flask_sock import Sock
from extensions import db

app = Flask(__name__, 
            template_folder='templates')
app.secret_key = os.urandom(24)
sock = Sock(app)

app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql+mysqlconnector://locker:root@localhost:3306/locker'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db.init_app(app)

@app.route('/assets/<path:path>')
def serve_assets(path):
    return send_from_directory('assets', path)

from func.auth_routes import *
from func.badge_routes import *

from func.mqtt_service import init_mqtt_client
mqtt_client = init_mqtt_client()

@app.route('/dashboard')
def dashboard():
    if not session.get('logged_in'):
        return redirect(url_for('login'))
    return render_template('dashboard.html')

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
        print("Tables de la base de données vérifiées/créées.")
    print("Serveur démarré! Accédez à http://localhost:5000")
    app.run(host='0.0.0.0', port=5000, debug=False)