# PROJECT CONTEXT — GUARDINET

## Présentation du projet
Nous sommes une équipe de 4 étudiants et nous réalisons un projet de **DevSecOps** dans le cadre des cours.

Le projet consiste à développer un **intranet scolaire sécurisé** nommé **GuardiNet**.

L’objectif n’est pas seulement de faire une application web, mais aussi d’appliquer une vraie logique **DevSecOps** :
- développement sécurisé
- contrôle d’accès par rôles
- intégration continue
- scans de sécurité
- conteneurisation Docker
- base de données MySQL
- pipeline GitHub Actions

---

## Stack technique imposée / prévue
- **Backend** : Flask (Python)
- **Base de données** : MySQL
- **Conteneurisation** : Docker / Docker Compose
- **CI/CD** : GitHub Actions
- **Qualité / sécurité** :
  - Flake8
  - Sonar / SAST
  - pip-audit ou safety
  - OWASP ZAP
  - Build Docker
  - Déploiement plus tard

---

## Objectif fonctionnel
Développer un intranet avec plusieurs rôles :

- **Administrateur**
- **Professeur**
- **Étudiant**

Le système doit intégrer une logique **RBAC** (Role Based Access Control), avec contrôle d’accès côté serveur.

Exemples de fonctionnalités attendues :
- authentification
- gestion des utilisateurs
- tableau de bord
- gestion des classes
- notes / évaluations
- emploi du temps
- séparation stricte des accès selon le rôle

---

## Exigences sécurité
Le projet doit suivre une logique de sécurisation applicative, avec notamment :
- mots de passe hashés
- protection CSRF
- validation des entrées
- limitation des injections SQL
- gestion de session
- headers HTTP de sécurité
- séparation des privilèges
- scans automatisés dans la pipeline

---

## Organisation GitHub choisie
Nous utilisons GitHub avec cette logique de branches :

- `main` = branche stable / version propre
- `dev` = branche d’intégration
- branches de travail par feature

Exemples de branches :
- `feature/auth-rbac`
- `feature/admin-module`
- `feature/teacher-student-module`
- `feature/docker-ci-security`

Workflow :
1. créer une branche depuis `dev`
2. développer la feature
3. push
4. Pull Request vers `dev`
5. validation
6. merge
7. quand `dev` est stable → PR vers `main`

---

## État actuel du projet
Pour le moment, la structure existante ressemble à ceci :

```text
GUARDINET/
├── .github/
│   └── workflows/
│       └── ci-cd.yml
├── app/
├── database/
├── README.md
└── requirements.txt