# 🔧 Configuration de Base de Données - GuardiNet

## 📊 Support des Bases de Données

GuardiNet supporte **deux bases de données** selon l'environnement :

### 🟢 Development : SQLite (Par défaut)

**Avantages :**
- ✅ Aucune installation requise
- ✅ Fichier local (`guardinet.db`)
- ✅ Parfait pour les tests et le développement
- ✅ Tout fonctionne "out of the box"

**Configuration :**
```bash
# Aucune configuration requise !
# L'app utilise SQLite par défaut en développement
FLASK_ENV=development
```

**Fichier créé :**
```
guardinet.db  # Base de données SQLite (créée automatiquement)
```

### 🔴 Production : MySQL

**Avantages :**
- ✅ Multi-utilisateurs concurrent
- ✅ Meilleure performance
- ✅ Sauvegardes et replications
- ✅ Conforme aux exigences DevSecOps

**Configuration requise :**
```bash
FLASK_ENV=production
DATABASE_URL=mysql+pymysql://user:password@localhost:3306/guardinet
```

---

## 🚀 Guide Rapide de Démarrage

### 1️⃣ Pour le Développement (SQLite)

```bash
# Aucune configuration MySQL requise !

# 1. Initialiser la base de données
python init_db.py

# 2. Lancer l'app
python run.py

# 3. Accéder à http://localhost:5000
```

**C'est tout !** Aucune installation MySQL n'est nécessaire pour développer.

---

### 2️⃣ Pour la Production (MySQL)

#### Étape 1 : Installer MySQL
```bash
# Sur Ubuntu/Debian
sudo apt-get install mysql-server

# Sur macOS
brew install mysql
```

#### Étape 2 : Créer la base de données
```bash
mysql -u root -p
CREATE DATABASE guardinet;
CREATE USER 'guardinet'@'localhost' IDENTIFIED BY 'SecurePassword123!';
GRANT ALL PRIVILEGES ON guardinet.* TO 'guardinet'@'localhost';
FLUSH PRIVILEGES;
EXIT;
```

#### Étape 3 : Configurer `.env`
```env
FLASK_ENV=production
DATABASE_URL=mysql+pymysql://guardinet:SecurePassword123!@localhost:3306/guardinet
```

#### Étape 4 : Initialiser la base de données
```bash
python init_db.py
```

#### Étape 5 : Lancer l'app
```bash
python run.py
```

---

## 📝 Fichiers de Configuration

### `.env` (Non versionné)
```env
FLASK_ENV=development           # development ou production
DATABASE_URL=...                # Optionnel - auto-détectialisé selon FLASK_ENV
MAIL_USERNAME=your_email@gmail.com
MAIL_PASSWORD=app_password
```

### `.env.example` (Modèle - versionné)
```
Sert de template pour créer `.env`
Met à jour avec votre configuration
```

### `.gitignore`
```
.env                # Ne pas commiter !
*.db               # Fichiers SQLite locaux
```

---

## 🔄 Migration SQLite → MySQL

Si vous avez commencé avec SQLite et voulez passer à MySQL :

### Étape 1 : Exporter les données SQLite
```bash
# Depuis SQLite
sqlite3 guardinet.db .dump > backup.sql
```

### Étape 2 : Créer la base MySQL
```bash
# Créer la base MySQL vide avec init_db.py
FLASK_ENV=production python init_db.py
```

### Étape 3 : Importer les données
```bash
# Adapter le dump SQLite pour MySQL
# Les schémas SQLite et MySQL diffèrent légèrement
mysql -u guardinet -p guardinet < backup.sql
```

### Étape 4 : Vérifier les données
```bash
# Vérifier que les utilisateurs sont présents
mysql -u guardinet -p guardinet -e "SELECT * FROM users;"
```

---

## 🛡️ Sécurité

### Development (SQLite)
- ✅ OK pour développement local
- ⚠️ Ne pas utiliser en production
- 🔒 Fichier `.db` dans `.gitignore`

### Production (MySQL)
- ✅ Utiliser des credentials forts
- ✅ Configuration pas dans le code
- ✅ Variables d'environnement sécurisées
- ✅ Connections chiffrées (SSL/TLS)

**Exemple de credentials forts :**
```
Utilisateur: guardinet_prod
Mot de passe: $(openssl rand -base64 16)
Base de données : production_guardinet
```

---

## 🐛 Dépannage

### ❌ "No module named 'pymysql'"
**Solution :**
```bash
pip install PyMySQL
# Déjà dans requirements.txt, faire : pip install -r requirements.txt
```

### ❌ "Access denied for user 'root'@'localhost'"
**Causes :**
- MySQL pas installé
- MySQL pas en cours d'exécution
- Mauvais password

**Solutions :**
```bash
# Vérifier MySQL
mysql -u root -p -e "SELECT VERSION();"

# Pour développement: utiliser SQLite (par défaut)
# Pas besoin de MySQL !

# Créer un utilisateur MySQL
mysql -u root -p
CREATE DATA guardinet;
CREATE USER 'dev'@'localhost' IDENTIFIED BY 'password';
GRANT ALL PRIVILEGES ON guardinet.* TO 'dev'@'localhost';
```

### ❌ "sqlite database is locked"
**Solution :**
```bash
# Arrêter l'app et relancer
# SQLite a des limitations en concurrence
# Pour multi-utilisateurs: passer à MySQL
```

---

## 📊 Comparaison

| Critère | SQLite | MySQL |
|---------|--------|-------|
| **Installation** | Intégrée | Requise |
| **Fichier** | `guardinet.db` | Network/TCP |
| **Utilisateurs concurrent** | 1 | Plusieurs |
| **Performance** | Bonne (local) | Excellente |
| **Backup** | Fichier | mysqldump |
| **Recommandé pour** | Développement | Production |

---

## 🎯 Recommandations

### 📱 Développement Local
```bash
# Utiliser SQLite = Aucune configuration
FLASK_ENV=development
# C'est automatique !
```

### 🏢 Production Guardia
```bash
# Utiliser MySQL
FLASK_ENV=production
DATABASE_URL=mysql+pymysql://prod_user:secure_pass@db.guardiana.fr/guardinet_prod
```

### 🚀 Déploiement Cloud
```bash
# MySQL Cloud (AWS RDS, Google Cloud SQL, etc.)
DATABASE_URL=mysql+pymysql://user:pass@db-instance.region.rds.amazonaws.com/guardinet
```

---

## 📚 Liens Utiles

- SQLAlchemy Docs: https://docs.sqlalchemy.org
- MySQL Documentation: https://dev.mysql.com/doc
- PyMySQL: https://github.com/PyMySQL/PyMySQL
- Flask-SQLAlchemy: https://flask-sqlalchemy.palletsprojects.com
