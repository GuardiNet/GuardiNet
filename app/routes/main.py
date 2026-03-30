import random
from flask import Blueprint, render_template, request, flash, redirect, url_for
from flask_login import login_user, logout_user, login_required, current_user
from app.models import db, User, Course, ScheduleEvent, Grade, Absence, ClassGroup, bcrypt
from datetime import datetime, timedelta, date

MOIS = ["", "janvier", "fÃ©vrier", "mars", "avril", "mai", "juin", "juillet", "aoÃ»t", "septembre", "octobre", "novembre", "dÃ©cembre"]
JOURS_COURTS = ["lun.", "mar.", "mer.", "jeu.", "ven.", "sam.", "dim."]
JOURS = ["Lundi", "Mardi", "Mercredi", "Jeudi", "Vendredi", "Samedi", "Dimanche"]

main_bp = Blueprint('main', __name__)

@main_bp.route('/')
def index():
    if current_user.is_authenticated:
        if current_user.role == 'admin':
            return redirect(url_for('main.admin_panel'))
        return redirect(url_for('main.dashboard'))
    return render_template('landing.html')

@main_bp.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        if current_user.role == 'admin':
            return redirect(url_for('main.admin_panel'))
        return redirect(url_for('main.dashboard'))
        
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
        user = User.query.filter_by(email=email).first()
        if user and user.check_password(password):
            login_user(user)
            if user.role == 'admin':
                return redirect(url_for('main.admin_panel'))
            return redirect(url_for('main.dashboard'))
        else:
            flash("Email ou mot de passe incorrect.", "error")
    return render_template('login.html')

@main_bp.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('main.index'))

@main_bp.route('/dashboard')
@login_required
def dashboard():
    # Redirections basées sur le rôle
    if current_user.role == 'admin':
        return redirect(url_for('main.admin_panel'))
    elif current_user.role == 'teacher':
        return redirect(url_for('main.teacher_panel'))

    view = request.args.get('view', 'hebdo')
    date_str = request.args.get('date')
    
    if date_str:
        try:
            ref_date = datetime.strptime(date_str, '%Y-%m-%d').date()
        except ValueError:
            ref_date = date.today()
    else:
        ref_date = date.today()
        if ref_date.weekday() == 6:
            ref_date += timedelta(days=1)
            
    if view == 'jour':
        start_date = ref_date
        end_date = ref_date
        prev_date = ref_date - timedelta(days=1)
        next_date = ref_date + timedelta(days=1)
        date_label = f"{JOURS[ref_date.weekday()]} {ref_date.day} {MOIS[ref_date.month]} {ref_date.year}"
        days_to_show = [ref_date]
    else:
        start_date = ref_date - timedelta(days=ref_date.weekday())
        end_date = start_date + timedelta(days=6)
        prev_date = ref_date - timedelta(days=7)
        next_date = ref_date + timedelta(days=7)
        
        if start_date.month == end_date.month:
            date_label = f"{start_date.day} - {end_date.day} {MOIS[start_date.month]} {start_date.year}"
        else:
            date_label = f"{start_date.day} {MOIS[start_date.month]} - {end_date.day} {MOIS[end_date.month]} {start_date.year}"
        
        days_to_show = [start_date + timedelta(days=i) for i in range(7)]

    start_dt = datetime.combine(start_date, datetime.min.time())
    end_dt = datetime.combine(end_date, datetime.max.time())

    schedules = []
    if current_user.role == 'student' and current_user.class_id:
        schedules = ScheduleEvent.query.filter(
            ScheduleEvent.class_id == current_user.class_id,
            ScheduleEvent.start_time >= start_dt,
            ScheduleEvent.start_time <= end_dt
        ).all()

    schedule_days_dict = {d: [] for d in days_to_show}

    for event in schedules:
        e_date = event.start_time.date()
        if e_date in schedule_days_dict:
            start_hour, start_min = event.start_time.hour, event.start_time.minute
            end_hour, end_min = event.end_time.hour, event.end_time.minute

            duration_mins = (end_hour * 60 + end_min) - (start_hour * 60 + start_min)
            top_px = (start_hour - 6) * 60 + start_min

            time_str = f"{event.start_time.strftime('%H:%M')} - {event.end_time.strftime('%H:%M')}"
            
            teacher_name = "Inconnu"
            if event.course and event.course.prof:
                teacher_name = f"{event.course.prof.firstname} {event.course.prof.lastname}"
            
            title = event.course.name if event.course else "Cours"
            if event.event_type:
                title += f" ({event.event_type})"

            schedule_days_dict[e_date].append({
                'time_str': time_str,
                'title': title,
                'teacher': teacher_name,
                'location': event.room or "Non défini",
                'top_px': top_px,
                'height_px': duration_mins,
                'color_class': 'event-green' # Placeholder color
            })

    ordered_schedule_days = []
    for d in days_to_show:
        if view == 'jour':
            day_name_str = f"{JOURS[d.weekday()]} {d.day:02d}/{d.month:02d}"
        else:
            day_name_str = JOURS[d.weekday()]
        d_events = schedule_days_dict[d]
        ordered_schedule_days.append({
            'name': day_name_str,
            'events': d_events
        })

    return render_template('dashboard.html', 
                           active_page='dashboard', 
                           schedule_days=ordered_schedule_days,
                           view=view,
                           date_label=date_label,
                           current_date=ref_date.strftime('%Y-%m-%d'),
                           prev_date=prev_date.strftime('%Y-%m-%d'),
                           next_date=next_date.strftime('%Y-%m-%d'))


@main_bp.route('/notes')
@login_required
def notes():
    # Notes depuis BDD
    grades = []
    if current_user.role == 'student':
        grades = Grade.query.filter_by(student_id=current_user.id).all()
    return render_template('notes.html', active_page='notes', grades=grades)

@main_bp.route('/absences')
@login_required
def absences():
    absences_list = []
    if current_user.role == 'student':
        absences_list = Absence.query.filter_by(student_id=current_user.id).all()
    return render_template('absences.html', active_page='absences', absences=absences_list)

@main_bp.route('/devoirs')
@login_required
def devoirs():
    return render_template('devoirs.html', active_page='devoirs')

@main_bp.route('/annonces')
@login_required
def annonces():
    return render_template('annonces.html', active_page='annonces', nb_annonces=1)

@main_bp.route('/chat')
@login_required
def chat():
    return render_template('chat.html', active_page='chat')

@main_bp.route('/prof')
@login_required
def teacher_panel():
    if current_user.role != 'teacher':
        return redirect(url_for('main.dashboard'))
    return "<h1>Bienvenue sur le panel Professeur !</h1><p>Cette page est en cours de construction.</p><br><a href='/logout'>Se dÃ©connecter</a>"

# ==========================================
# ROUTES ADMIN
# ==========================================

from functools import wraps
from flask import abort

def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated or current_user.role != 'admin':
            abort(403) # STOP! Ce n'est pas pour toi, retourne Ã  tes devoirs bogoss
        return f(*args, **kwargs)
    return decorated_function

@main_bp.route('/admin', methods=['GET', 'POST'])
@login_required
@admin_required
def admin_panel():
    active_tab = 'create'
    if request.method == 'POST':
        firstname = request.form.get('firstname')
        lastname = request.form.get('lastname')
        email = request.form.get('email')
        role = request.form.get('role', 'student')
        
        if User.query.filter_by(email=email).first():
            flash("Cet e-mail est dÃ©jÃ  utilisÃ©.", "error")
        else:
            new_user = User(
                firstname=firstname,
                lastname=lastname,
                email=email,
                role=role
            )
            new_user.set_password("GuardiNet2026!") 
            new_user.is_password_temporary = True # On force Ã  changer
            
            db.session.add(new_user)
            db.session.commit()
            flash(f"Compte {role} crÃ©Ã© pour {firstname} {lastname}. (Mot de passe: GuardiNet2026!)", "success")
            
    classes = ClassGroup.query.all()
    students = User.query.filter_by(role='student').all()
    teachers = User.query.filter_by(role='teacher').all()
    courses = Course.query.all()
            
    return render_template('admin.html', active_tab=active_tab, classes=classes, students=students, teachers=teachers, courses=courses)

@main_bp.route('/admin/users')
@login_required
@admin_required
def admin_users():
    users = User.query.all()
    return render_template('admin_users.html', users=users, active_tab='users')

@main_bp.route('/admin/delete_user/<int:user_id>', methods=['POST'])
@login_required
@admin_required
def delete_user(user_id):
    if current_user.id == user_id:
        flash("Vous ne pouvez pas supprimer votre propre compte administratif.", "error")
        return redirect(url_for('main.admin_users'))
        
    user = User.query.get_or_404(user_id)
    db.session.delete(user)
    db.session.commit()
    flash(f"L'utilisateur {user.firstname} {user.lastname} a Ã©tÃ© supprimÃ© avec succÃ¨s.", "success")
    return redirect(url_for('main.admin_users'))

@main_bp.route('/admin/infrastructure', methods=['GET', 'POST'])
@login_required
@admin_required
def admin_infrastructure():
    from datetime import datetime
    if request.method == 'POST':
        action = request.form.get('action')
        
        if action == 'create_class':
            name = request.form.get('name')
            if name:
                new_class = ClassGroup(name=name)
                db.session.add(new_class)
                db.session.commit()
                flash(f"Classe {name} crÃ©Ã©e avec succÃ¨s.", "success")
                
        elif action == 'assign_user_class':
            user_id = request.form.get('user_id')
            class_id = request.form.get('class_id')
            if user_id and class_id:
                user = User.query.get(user_id)
                if user:
                    user.class_id = class_id
                    db.session.commit()
                    flash("Utilisateur assignÃ© Ã  la classe.", "success")
                    
        elif action == 'create_course':
            name = request.form.get('name')
            prof_id = request.form.get('prof_id')
            if name:
                new_course = Course(name=name, prof_id=prof_id if prof_id else None)
                db.session.add(new_course)
                db.session.commit()
                flash(f"Cours {name} crÃ©Ã© avec succÃ¨s.", "success")
                
        elif action == 'create_schedule':
            course_id = request.form.get('course_id')
            class_id = request.form.get('class_id')
            start_time_str = request.form.get('start_time')
            end_time_str = request.form.get('end_time')
            room = request.form.get('room')
            event_type = request.form.get('event_type')
            
            if course_id and class_id and start_time_str and end_time_str:
                try:
                    start_time = datetime.fromisoformat(start_time_str)
                    end_time = datetime.fromisoformat(end_time_str)
                    
                    new_event = ScheduleEvent(
                        course_id=course_id,
                        class_id=class_id,
                        start_time=start_time,
                        end_time=end_time,
                        room=room,
                        event_type=event_type
                    )
                    db.session.add(new_event)
                    db.session.commit()
                    flash("Ã‰vÃ©nement ajoutÃ© Ã  l'emploi du temps.", "success")
                except ValueError:
                    flash("Erreur dans le format des dates.", "error")
                    
        return redirect(url_for('main.admin_panel'))

    return redirect(url_for('main.admin_panel'))

@main_bp.app_errorhandler(404)
def page_not_found(e):
    # Memes droles car on est des fun guys
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

