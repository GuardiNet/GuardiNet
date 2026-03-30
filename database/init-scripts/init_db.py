#!/usr/bin/env python
"""
Script to initialize the database with a default admin user.
Supports both SQLite (development) and MySQL (production).
Run this after first deployment.
"""

import os
import sys

# Ajouter la racine du projet au Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../../')))

from sqlalchemy import text, inspect
from app import create_app
from app.models import db, User

def init_db():
    """Initialize the database with tables and default admin user"""
    app = create_app()
    
    with app.app_context():
        # Display database info
        db_uri = app.config['SQLALCHEMY_DATABASE_URI']
        if 'sqlite' in db_uri:
            db_type = "SQLite (development)"
        elif 'mysql' in db_uri:
            db_type = "MySQL (production)"
        else:
            db_type = "Unknown"
        
        print(f"📊 Database: {db_type}")
        print(f"   URI: {db_uri.replace(app.config.get('DB_PASSWORD', ''), '***')}")
        
        # Step 1: Create all tables from SQL script (clear schema in human-readable SQL)
        print("\n📝 Initialisation de la base via guardinet_init.sql...")
        sql_file = os.path.join(os.path.dirname(__file__), 'guardinet_init.sql')
        if os.path.exists(sql_file):
            with open(sql_file, 'r', encoding='utf-8') as f:
                content = f.read()

            # For SQLite and MySQL, split by semicolon and execute.
            statements = [s.strip() for s in content.split(';') if s.strip()]
            for statement in statements:
                try:
                    db.session.execute(text(statement))
                except Exception as e:
                    # Ignore duplicate index/table errors
                    msg = str(e).lower()
                    if 'already exists' in msg or 'duplicate' in msg or 'exist' in msg:
                        continue
                    raise
            db.session.commit()
            print("✓ Script SQL exécuté avec succès")
        else:
            print(f"⚠️  Le fichier SQL {sql_file} est introuvable. Création par SQLAlchemy fallback...")
            try:
                db.create_all()
                print("✓ Tables créées avec SQLAlchemy")
            except Exception as e:
                print(f"✗ Error creating tables: {e}")
                print("\n⚠️  Troubleshooting:")
                if 'mysql' in db_uri:
                    print("  • Ensure MySQL is running")
                    print("  • Check DATABASE_URL in .env")
                    print("  • For MySQL: mysql -u root -p")
                    print("    CREATE DATABASE guardinet;")
                return

        # Step 2: Check and add missing columns BEFORE using ORM queries
        # This prevents SQLAlchemy from trying to access columns that don't exist yet
        print("\n🔍 Verification du schema de la base de donnees...")
        inspector = inspect(db.engine)
        columns = [c['name'] for c in inspector.get_columns('users')] if 'users' in inspector.get_table_names() else []
        
        # Add missing columns one by one
        if 'user_id' not in columns:
            print("🛠️  Ajout de la colonne user_id dans users...")
            try:
                db.session.execute(text('ALTER TABLE users ADD COLUMN user_id VARCHAR(12)'))
                db.session.commit()
                print('✓ user_id ajouté')
            except Exception as e:
                print(f'✗ Echec de l\'ajout de la colonne user_id : {e}')
                db.session.rollback()
                
        if 'is_password_temporary' not in columns:
            print("🛠️  Ajout de la colonne is_password_temporary dans users...")
            try:
                db.session.execute(text('ALTER TABLE users ADD COLUMN is_password_temporary BOOLEAN DEFAULT 0'))
                db.session.commit()
                print('✓ is_password_temporary ajouté')
            except Exception as e:
                print(f"✗ Echec de l\'ajout de is_password_temporary : {e}")
                db.session.rollback()

        # Step 3: NOW it's safe to use ORM since all columns exist
        print("\n🔄 Mise a jour des utilisateurs existants...")
        
        # For compatibility, fill missing user_id for existing users
        users_without_user_id = User.query.filter((User.user_id == None) | (User.user_id == '')).all()
        if users_without_user_id:
            print(f"🛠️  Mise à jour de {len(users_without_user_id)} utilisateurs existants avec user_id...")
            for u in users_without_user_id:
                generated = User.generate_user_id()
                while User.query.filter_by(user_id=generated).first():
                    generated = User.generate_user_id()
                u.user_id = generated
            db.session.commit()
            print('✓ user_id rempli pour les utilisateurs existants')
        
        # Check if admin user exists
        admin = User.query.filter_by(email='admin@guardia.fr').first()
        
        if admin:
            print("\nℹ️  Default admin user already exists")
            return
        
        # Create default admin user
        print("\n👤 Creating default admin user...")
        admin = User(
            firstname='Admin',
            lastname='GuardiNet',
            email='admin@guardia.fr',
            role='admin',
            is_active=True
        )
        admin.set_password('Admin123!')  # CHANGE THIS DEFAULT PASSWORD
        
        try:
            db.session.add(admin)
            db.session.commit()
            print("✓ Default admin user created successfully")
            print(f"  📧 Email: admin@guardia.fr")
            print(f"  🔑 Password: Admin123!")
            print(f"\n⚠️  IMPORTANT: Change the default admin password after first login!")
        except Exception as e:
            print(f"✗ Error creating admin user: {e}")
            db.session.rollback()
            return

if __name__ == '__main__':
    try:
        init_db()
        print("\n✓ Database initialization completed!")
    except Exception as e:
        print(f"\n✗ Error initializing database: {e}")
        import traceback
        traceback.print_exc()
