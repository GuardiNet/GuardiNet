# GuardiNet

GuardiNet est une plateforme web développée en Python (Flask) dédiée à la gestion scolaire et au suivi des élèves (notes, devoirs, absences). Le projet met un fort accent sur la sécurité et intègre une infrastructure DevSecOps complète.

## Fonctionnalités principales

* **Espace utilisateur** : Tableau de bord, suivi des notes, des devoirs à faire et de l'historique des absences.
* **Authentification sécurisée** : Connexion, récupération et changement de mot de passe, protection contre les attaques par force brute (limitation de requêtes).
* **Espace d'administration** : Interface dédiée pour la gestion des utilisateurs et l'administration générale de la plateforme.
* **Communication** : Système d'annonces et module de chat/messagerie.

## Technologies & Architecture

* **Backend** : Python 3.11, Flask, Flask-Login.
* **Frontend** : HTML, CSS (styles modulaires), JS, intégration via le moteur de templates Jinja2.
* **Base de données** : SQLite.
* **Sécurité & CI/CD** : GitHub Actions (Flake8), SonarCloud (SAST), pip-audit (SCA), Trivy (Scan de conteneurs), Gitleaks (Scan de secrets), OWASP ZAP (DAST) et Pytest.

## Prérequis

* Python 3.10 ou supérieur
* Git

## Installation locale (Développement)

1. Cloner le dépôt :
```bash
git clone https://github.com/GuardiNet/GuardiNet.git
cd GuardiNet
```

2. Créer l'environnement virtuel et l'activer :
```bash
python -m venv .venv

# Sur Windows :
.venv\Scripts\activate
# Sur Linux/Mac :
source .venv/bin/activate
```

3. Installer les dépendances :
```bash
pip install -r requirements.txt
```

4. Configuration :
Assurez-vous de créer un fichier `.env` à la racine pour stocker de façon sécurisée vos variables d'environnement (comme `SECRET_KEY`). Un environnement par défaut se chargera si aucun fichier n'est présent, mais le `.env` est requis pour la production (ignoré par git).

5. Initialiser et lancer le serveur :
```bash
python run.py
```
L'application sera disponible sur `http://127.0.0.1:5000`.

## Scripts et Tests

Les tests unitaires sont prévus avec `pytest`. Pour lancer localement la suite de tests et vérifier la couverture de code :
```bash
pytest tests/ --cov=app
```

## Déploiement avec Docker

Pour exécuter l'application de manière isolée via Docker :

1. Construire l'image localement :
```bash
docker build -t guardinet-app .
```

2. Lancer le conteneur (en exposant le port 5000) :
```bash
docker run -d -p 5000:5000 --name guardinet-live --env FLASK_ENV=development --env-file .env guardinet-app
```

L'application sera directement accessible sur `http://localhost:5000`.
