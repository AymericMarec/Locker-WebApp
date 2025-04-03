from app import create_app, db
from app.models.user import User
from flask_migrate import Migrate, upgrade

app = create_app()
migrate = Migrate(app, db)

def create_admin_user():
    with app.app_context():
        # Initialisation de la base de données avec Flask-Migrate
        try:
            # Create the database tables
            db.create_all()
            print("Base de données initialisée.")
        except Exception as e:
            print(f"Erreur lors de l'initialisation de la base de données: {e}")
            return
        
        # Vérifier si un administrateur existe déjà
        admin = User.query.filter_by(username='admin').first()
        
        if admin is None:
            # Créer l'administrateur
            admin = User(
                username='admin',
                email='admin@locker.com',
                password='admin123',
                first_name='Admin',
                last_name='User',
                is_admin=True
            )
            
            db.session.add(admin)
            db.session.commit()
            print("Utilisateur administrateur créé avec succès !")
            print("Nom d'utilisateur: admin")
            print("Mot de passe: admin123")
        else:
            print("Un administrateur existe déjà dans la base de données.")

if __name__ == '__main__':
    create_admin_user() 