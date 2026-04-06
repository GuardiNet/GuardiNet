# Application entry point
from dotenv import load_dotenv
load_dotenv()

from app import create_app
from app.models import db, User

app = create_app()

def initialize_database():
    """Crée la base de données et un compte test par défaut si elle est vide."""
    with app.app_context():
        # Créer toutes les tables si elles n'existent pas
        db.create_all()
        
        # Vérifier s'il y a déjà des utilisateurs
        if not User.query.first():
            print("Base de données vide détectée. Création d'un utilisateur par défaut...")
            try:
                # Créer un utilisateur test par défaut
                test_user = User(
                    firstname='Test',
                    lastname='User',
                    email='test@guardinet.fr',
                    role='student',
                    is_active=True
                )
                test_user.set_password('TestUser1234!')
                db.session.add(test_user)
                db.session.commit()
                print("=====================================================")
                print("Base de données initialisée avec succès ! ✅")
                print("Compte utilisateur test par défaut :")
                print("Email : test@guardinet.fr")
                print("Mot de passe : TestUser1234!")
                print("=====================================================")
            except Exception as e:
                print(f"Erreur lors de la création de l'utilisateur : {e}")
                db.session.rollback()

if __name__ == '__main__':
    initialize_database()
    app.run(host='0.0.0.0', port=5000)
