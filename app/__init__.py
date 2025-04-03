import os
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from flask_migrate import Migrate
from flask_bootstrap import Bootstrap
from dotenv import load_dotenv

# Charger les variables d'environnement depuis le fichier .env
load_dotenv()

# Initialiser les extensions
db = SQLAlchemy()
migrate = Migrate()
login_manager = LoginManager()
login_manager.login_view = 'auth.login'
bootstrap = Bootstrap()

def create_app(test_config=None):
    # Créer et configurer l'app
    app = Flask(__name__, instance_relative_config=True)
    
    # Créer le chemin absolu vers la base de données
    basedir = os.path.abspath(os.path.dirname(__file__))
    instance_path = os.path.join(os.path.dirname(basedir), 'instance')
    os.makedirs(instance_path, exist_ok=True)
    db_path = os.path.join(instance_path, 'app.db')
    db_uri = f'sqlite:///{db_path}'
    
    # Configuration par défaut
    app.config.from_mapping(
        SECRET_KEY=os.environ.get('SECRET_KEY', 'dev_key_for_testing'),
        SQLALCHEMY_DATABASE_URI=os.environ.get('DATABASE_URL', db_uri),
        SQLALCHEMY_TRACK_MODIFICATIONS=False,
    )

    if test_config is None:
        # Charger la config d'instance, si elle existe
        app.config.from_pyfile('config.py', silent=True)
    else:
        # Charger la config de test
        app.config.from_mapping(test_config)

    # S'assurer que le dossier instance existe
    try:
        os.makedirs(app.instance_path)
    except OSError:
        pass

    # Initialiser les extensions avec l'app
    db.init_app(app)
    migrate.init_app(app, db)
    login_manager.init_app(app)
    bootstrap.init_app(app)

    # Importer et enregistrer les blueprints
    from app.routes import main, auth, api
    app.register_blueprint(main.bp)
    app.register_blueprint(auth.bp)
    app.register_blueprint(api.bp)

    return app

# Importer les modèles pour que Flask-Migrate puisse les détecter
from app.models import user, rfid, access_log 