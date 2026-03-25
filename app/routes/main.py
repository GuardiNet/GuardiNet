from flask import Blueprint, render_template

main_bp = Blueprint('main', __name__)

@main_bp.route('/')
def index():
    # Page de présentation de GuardiNet (Landing Page)
    return render_template('landing.html')

@main_bp.route('/dashboard')
def dashboard():
    # Le tableau de bord interne (l'intranet)
    return render_template('dashboard.html', logo_url='/static/img/logo.png')

@main_bp.route('/login')
def login():
    # Placeholder pour la future page de connexion
    return "Page de connexion (à implémenter)"
