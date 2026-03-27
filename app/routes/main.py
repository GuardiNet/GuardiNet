from flask import Blueprint, render_template

main_bp = Blueprint('main', __name__)

@main_bp.route('/')
def index():
    # Page de présentation de GuardiNet (Landing Page)
    return render_template('landing.html')

@main_bp.route('/dashboard')
def dashboard():
    # Le tableau de bord interne (l'intranet) - Emploi du temps
    return render_template('dashboard.html', active_page='dashboard')

@main_bp.route('/devoirs')
def devoirs():
    # Page des devoirs
    return render_template('devoirs.html', active_page='devoirs')

@main_bp.route('/annonces')
def annonces():
    # Page des annonces
    return render_template('annonces.html', active_page='annonces', nb_annonces=1)

@main_bp.route('/notes')
def notes():
    # Page des notes
    return render_template('notes.html', active_page='notes')

@main_bp.route('/chat')
def chat():
    # Page du chat privé
    return render_template('chat.html', active_page='chat')

@main_bp.route('/login')
def login():
    # Placeholder pour la future page de connexion
    return "Page de connexion (à implémenter)"
