import random
import string
from flask_mail import Message
from app import mail
from flask import current_app
import string
from flask_mail import Message
from app import mail
from flask import current_app
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
            

            colors = ["event-blue", "event-green", "event-red", "event-yellow", "event-purple", "event-orange"]
            color_idx = event.course_id % len(colors) if event.course_id else 0
            color_class = colors[color_idx]
            

            colors = ["event-blue", "event-green", "event-red", "event-yellow", "event-purple", "event-orange"]
            color_idx = event.course_id % len(colors) if event.course_id else 0
            color_class = colors[color_idx]
            
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
                'color_class': color_class
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
    total_hours = 0
    non_justified_hours = 0

    if current_user.role == 'student':
        # Get absences and sort by schedule start_time descending
        absences_list = Absence.query.join(ScheduleEvent).filter(Absence.student_id == current_user.id).order_by(ScheduleEvent.start_time.desc()).all()
        
        for absence in absences_list:
            # Calculate duration in hours
            duration = (absence.schedule.end_time - absence.schedule.start_time).total_seconds() / 3600
            total_hours += duration
            if not absence.is_justified:
                non_justified_hours += duration

    return render_template('absences.html', 
                           active_page='absences', 
                           absences=absences_list,
                           total_hours=int(total_hours) if total_hours.is_integer() else round(total_hours, 1),
                           non_justified_hours=int(non_justified_hours) if non_justified_hours.is_integer() else round(non_justified_hours, 1))

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
    active_tab = request.args.get('tab', 'create')
    if request.method == 'POST':
        firstname = request.form.get('firstname')
        lastname = request.form.get('lastname')
        email = request.form.get('email')
        role = request.form.get('role', 'student')
        
        if User.query.filter_by(email=email).first():
            flash("Cet e-mail est déjà utilisé.", "error")
        else:
            new_user = User(
                firstname=firstname,
                lastname=lastname,
                email=email,
                role=role
            )
            import string
            import random
            from flask_mail import Message
            from app import mail
            from flask import current_app
            
            # Generate temporary password
            temp_password = "".join(random.choices(string.ascii_letters + string.digits, k=10)) + "!"
            new_user.set_password(temp_password)
            new_user.is_password_temporary = True
            
            db.session.add(new_user)
            db.session.commit()
            
            # Check if we should send email
            send_email = request.form.get("send_email") == "on"
            if send_email:
                try:
                    msg = Message(subject="Bienvenue sur GuardiNet",
                                  sender=current_app.config.get("MAIL_DEFAULT_SENDER"),
                                  recipients=[new_user.email])
                    msg.html = render_template("email_new_account.html", 
                                             user=new_user, 
                                             password=temp_password, 
                                             login_url=url_for("main.login", _external=True))
                    mail.send(msg)
                    flash(f"Compte {role} créé pour {firstname} {lastname} et email envoyé.", "success")
                except Exception as e:
                    print("Erreur envoi email:", e)
                    flash(f"Compte {role} créé avec mot de passe {temp_password}. Échec de l'envoi de l'email : vérifiez la config SMTP.", "warning")
            else:
                flash(f"Compte {role} créé avec succès (Aucun e-mail envoyé).", "success")
            
    classes = ClassGroup.query.all()
    students = User.query.filter_by(role='student').all()
    teachers = User.query.filter_by(role='teacher').all()
    courses = Course.query.all()
    
    # Schedule logic for EDT tab
    view = request.args.get('view', 'hebdo')
    date_str = request.args.get('date')
    selected_class_id = request.args.get('class_id', type=int)
    
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
    if not selected_class_id and classes:
        selected_class_id = classes[0].id

    if selected_class_id:
        schedules = ScheduleEvent.query.filter(
            ScheduleEvent.class_id == selected_class_id,
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
            

            colors = ["event-blue", "event-green", "event-red", "event-yellow", "event-purple", "event-orange"]
            color_idx = event.course_id % len(colors) if event.course_id else 0
            color_class = colors[color_idx]
            

            colors = ["event-blue", "event-green", "event-red", "event-yellow", "event-purple", "event-orange"]
            color_idx = event.course_id % len(colors) if event.course_id else 0
            color_class = colors[color_idx]
            
            teacher_name = "Inconnu"
            if event.course and event.course.prof:
                teacher_name = f"{event.course.prof.firstname} {event.course.prof.lastname}"
            
            title = event.course.name if event.course else "Cours"
            if event.event_type:
                title += f" ({event.event_type})"

            schedule_days_dict[e_date].append({
                'id': event.id,
                'course_id': event.course_id,
                'time_str': time_str,
                'title': title,
                'teacher': teacher_name,
                'location': event.room or "Non défini",
                'top_px': top_px,
                'height_px': duration_mins,
                'color_class': color_class,
                'start_time': event.start_time.strftime('%Y-%m-%dT%H:%M'),
                'end_time': event.end_time.strftime('%Y-%m-%dT%H:%M'),
                'event_type': event.event_type or '',
                'room': event.room or ''
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
            
    all_users = User.query.all()
    all_absences = Absence.query.all()
    return render_template('admin.html', users=all_users, active_tab=active_tab, classes=classes, students=students, teachers=teachers, courses=courses, absences=all_absences,
                           schedule_days=ordered_schedule_days, view=view, date_label=date_label,
                           current_date=ref_date.strftime('%Y-%m-%d'), prev_date=prev_date.strftime('%Y-%m-%d'),
                           next_date=next_date.strftime('%Y-%m-%d'), selected_class_id=selected_class_id)


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
                flash(f"Cours {name} créé avec succès.", "success")
                
        elif action == 'edit_course':
            course_id = request.form.get('course_id')
            name = request.form.get('name')
            prof_id = request.form.get('prof_id')
            course = Course.query.get(course_id)
            if course and name:
                course.name = name
                course.prof_id = prof_id if prof_id else None
                db.session.commit()
                flash(f"Cours {name} modifié avec succès.", "success")
        
        elif action == 'delete_course':
            course_id = request.form.get('course_id')
            course = Course.query.get(course_id)
            if course:
                for schedule in course.schedules:
                    db.session.delete(schedule)
                for grade in course.grades:
                    db.session.delete(grade)
                db.session.delete(course)
                db.session.commit()
                flash("Cours supprimé avec succès.", "success")

        elif action == 'edit_schedule':
            event_id = request.form.get('event_id')
            course_id = request.form.get('course_id')
            start_time_str = request.form.get('start_time')
            end_time_str = request.form.get('end_time')
            room = request.form.get('room')
            event_type = request.form.get('event_type')
            
            event = ScheduleEvent.query.get(event_id)
            if event and course_id and start_time_str and end_time_str:
                try:
                    event.course_id = course_id
                    event.start_time = datetime.fromisoformat(start_time_str)
                    event.end_time = datetime.fromisoformat(end_time_str)
                    event.room = room
                    event.event_type = event_type
                    db.session.commit()
                    flash("Événement modifié avec succès.", "success")
                except ValueError:
                    flash("Format de date invalide.", "error")
            return redirect(url_for('main.admin_panel', tab='edt'))

        elif action == 'delete_schedule':
            event_id = request.form.get('event_id')
            event = ScheduleEvent.query.get(event_id)
            if event:
                db.session.delete(event)
                db.session.commit()
                flash("Événement supprimé avec succès.", "success")
            return redirect(url_for('main.admin_panel', tab='edt'))

        elif action == 'edit_schedule':
            event_id = request.form.get('event_id')
            course_id = request.form.get('course_id')
            start_time_str = request.form.get('start_time')
            end_time_str = request.form.get('end_time')
            room = request.form.get('room')
            event_type = request.form.get('event_type')
            
            event = ScheduleEvent.query.get(event_id)
            if event and course_id and start_time_str and end_time_str:
                try:
                    event.course_id = course_id
                    event.start_time = datetime.fromisoformat(start_time_str)
                    event.end_time = datetime.fromisoformat(end_time_str)
                    event.room = room
                    event.event_type = event_type
                    db.session.commit()
                    flash("Événement modifié avec succès.", "success")
                except ValueError:
                    flash("Format de date invalide.", "error")
            return redirect(url_for('main.admin_panel', tab='edt'))

        elif action == 'delete_schedule':
            event_id = request.form.get('event_id')
            event = ScheduleEvent.query.get(event_id)
            if event:
                db.session.delete(event)
                db.session.commit()
                flash("Événement supprimé avec succès.", "success")
            return redirect(url_for('main.admin_panel', tab='edt'))

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


@main_bp.route('/admin/users/change-class', methods=['POST'])
@login_required
@admin_required
def admin_change_class():
    user_id = request.form.get('user_id')
    class_id = request.form.get('class_id')
    
    if user_id and class_id:
        user = User.query.get(user_id)
        if user and user.role == 'student':
            user.class_id = class_id
            db.session.commit()
            flash(f"La classe de {user.firstname} {user.lastname} a été mise à jour.", "success")
            
    return redirect(url_for('main.admin_panel', tab='users'))


@main_bp.route('/admin/absences/update/<int:absence_id>', methods=['POST'])
@login_required
def admin_update_absence(absence_id):
    if current_user.role != 'admin':
        flash("Accès non autorisé.", "error")
        return redirect(url_for('main.dashboard'))
        
    absence = Absence.query.get_or_404(absence_id)
    action = request.form.get('action') # "justify", "unjustify", "delete"
    
    student = absence.student
    course_name = absence.schedule.course.name if absence.schedule and absence.schedule.course else "Inconnu"
    absence_date = absence.schedule.start_time.strftime('%d/%m/%Y %H:%M') if absence.schedule else "Inconnue"
    
    if action == 'delete':
        db.session.delete(absence)
        db.session.commit()
        flash("Absence supprimée avec succès.", "success")
        status = "supprimée"
    else:
        if action == 'justify':
            absence.is_justified = True
            status = "justifiée"
            flash("Absence marquée comme justifiée.", "success")
        elif action == 'unjustify':
            absence.is_justified = False
            status = "injustifiée"
            flash("Absence marquée comme injustifiée.", "success")
            
        db.session.commit()
        
    # Envoyer un e-mail à l'étudiant
    try:
        msg = Message(subject="Mise à jour de votre absence",
                      sender=current_app.config.get("MAIL_DEFAULT_SENDER"),
                      recipients=[student.email])
        msg.html = render_template("email_absence_update.html", 
                                 user=student, 
                                 course_name=course_name,
                                 absence_date=absence_date,
                                 status=status)
        mail.send(msg)
    except Exception as e:
        print("Erreur envoi email absence:", e)
        flash("Mise à jour réussie mais échec de l'envoi de l'e-mail.", "warning")

    return redirect(url_for('main.admin_panel', tab='absences'))


@main_bp.route("/profile", methods=["GET", "POST"])
@login_required
def profile():
    if request.method == "POST":
        action = request.form.get("action")
        
        # 1. Mettre à jour le mot de passe
        if action == "update_password":
            current_password = request.form.get("current_password")
            new_password = request.form.get("new_password")
            confirm_password = request.form.get("confirm_password")
            
            if not current_user.check_password(current_password):
                flash("Le mot de passe actuel est incorrect.", "error")
            elif new_password != confirm_password:
                flash("Les nouveaux mots de passe ne correspondent pas.", "error")
            elif len(new_password) < 6:
                flash("Le mot de passe doit contenir au moins 6 caractères.", "error")
            else:
                current_user.set_password(new_password)
                current_user.is_password_temporary = False
                db.session.commit()
                flash("Votre mot de passe a été mis à jour avec succès.", "success")
                
        # 2. Mettre à jour la photo de profil
        elif action == "update_picture":
            if "profile_pic" not in request.files:
                flash("Aucun fichier sélectionné.", "error")
            else:
                file = request.files["profile_pic"]
                if file.filename == "":
                    flash("Aucun fichier sélectionné.", "error")
                elif file:
                    filename = secure_filename(f"{current_user.id}_{file.filename}")
                    
                    # Make sure dir exists
                    save_path = os.path.join(current_app.root_path, "static", "img", "profiles")
                    os.makedirs(save_path, exist_ok=True)
                    
                    file_path = os.path.join(save_path, filename)
                    file.save(file_path)
                    
                    current_user.profile_pic = filename
                    db.session.commit()
                    flash("Votre photo de profil a été mise à jour.", "success")
        
        return redirect(url_for("main.profile"))
        
    return render_template("profile.html")
