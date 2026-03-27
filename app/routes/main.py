import random
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

@main_bp.route('/absences')
def absences():
    # Page des absences
    return render_template('absences.html', active_page='absences')

@main_bp.route('/chat')
def chat():
    # Page du chat privé
    return render_template('chat.html', active_page='chat')

@main_bp.route('/login')
def login():
    # Placeholder pour la future page de connexion
    return "Page de connexion (à implémenter)"

@main_bp.app_errorhandler(404)
def page_not_found(e):
    # Liste de mèmes drôles sur le développement ou l'absence de page
    memes = [
        "https://media.giphy.com/media/14uQ3cOFteDaU/giphy.gif", # IT crowd "Did you try turning it off"
        "https://media.giphy.com/media/V80llXf734WzK/giphy.gif", # Monkey looking away
        "https://media.giphy.com/media/NTur7XlVDUdqM/giphy.gif", # This is fine
        "https://media.giphy.com/media/11rqJGteaNDOow/giphy.gif", # Confused Travolta
        "https://media.giphy.com/media/YyKPbc5OOTSQE/giphy.gif", # Homer Simpson retreating into bushes
        "https://media.giphy.com/media/jWexOOlPu6jq8/giphy.gif", # Computer smash
        "https://media.giphy.com/media/fVqW1Hnpe6m8U/giphy.gif" # Magic programming cat
    ]
    meme_url = random.choice(memes)
    return render_template('404.html', meme_url=meme_url), 404
