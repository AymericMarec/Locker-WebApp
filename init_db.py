from app import create_app, db
from app.models.user import User
import os

def init_database():
    # Créer l'application
    app = create_app()
    
    with app.app_context():
        # S'assurer que le répertoire instance existe
        os.makedirs(os.path.join(os.getcwd(), 'instance'), exist_ok=True)
        
        # Créer toutes les tables
        db.create_all()
        print("Base de données créée avec succès")
        
        # Vérifier si un utilisateur admin existe déjà
        admin = User.query.filter_by(username='admin').first()
        if not admin:
            # Créer l'utilisateur admin
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
            print("Utilisateur admin créé avec succès")
            print("Username: admin")
            print("Password: admin123")
        else:
            print("L'utilisateur admin existe déjà")

if __name__ == "__main__":
    init_database() 