import random
import string
import os
from werkzeug.utils import secure_filename
from flask_mail import Message as MailMessage
from app import mail
from flask import current_app
from flask import Blueprint, render_template, request, flash, redirect, url_for
from flask_login import login_user, logout_user, login_required, current_user
from app.models import db, User, Course, ScheduleEvent, Grade, Absence, ClassGroup, bcrypt, Message as ChatMessage, GroupChat, GroupChatMember, GroupMessage, Homework
from datetime import datetime, timedelta, date
from flask import jsonify

MOIS = ["", "janvier", "fÃ©vrier", "mars", "avril", "mai", "juin", "juillet", "aoÃ»t", "septembre", "octobre", "novembre", "dÃ©cembre"]
JOURS_COURTS = ["lun.", "mar.", "mer.", "jeu.", "ven.", "sam.", "dim."]
JOURS = ["Lundi", "Mardi", "Mercredi", "Jeudi", "Vendredi", "Samedi", "Dimanche"]

main_bp = Blueprint('main', __name__)

@main_bp.app_context_processor
def inject_unread_announcements():
    from flask_login import current_user
    from app.models import Announcement, Course, ScheduleEvent, db
    unread_count = 0
    latest_ann = None
    if current_user.is_authenticated:
        base_query = Announcement.query
        last_read = current_user.last_announcements_read_at
        
        query = base_query
        if last_read:
            query = query.filter(Announcement.created_at > last_read)
            
        if current_user.role == 'admin':
            unread_count = query.count()
            latest_ann = base_query.order_by(Announcement.created_at.desc()).first()
        elif current_user.role == 'teacher':
            courses = Course.query.filter_by(prof_id=current_user.id).all()
            class_ids = set()
            for c in courses:
                scheds = db.session.query(ScheduleEvent.class_id).filter_by(course_id=c.id).distinct().all()
                for s in scheds:
                    class_ids.add(s[0])
            class_ids = list(class_ids)
            
            condition = (Announcement.class_id == None) | (Announcement.class_id.in_(class_ids)) | (Announcement.author_id == current_user.user_id)
            unread_count = query.filter(condition).count()
            latest_ann = base_query.filter(condition).order_by(Announcement.created_at.desc()).first()
        else:
            condition = (Announcement.class_id == None) | (Announcement.class_id == current_user.class_id)
            unread_count = query.filter(condition).count()
            latest_ann = base_query.filter(condition).order_by(Announcement.created_at.desc()).first()
            
    return dict(unread_announcements_count=unread_count, latest_announcement=latest_ann)

@main_bp.before_request
def require_password_change():
    from flask_login import current_user
    from flask import request, redirect, url_for
    if current_user.is_authenticated:
        allowed_endpoints = ['main.force_change_password', 'main.logout', 'static']
        # We ensure request.endpoint isn't starting with static as well just in case flask static gets weird
        if current_user.is_password_temporary and hasattr(request, 'endpoint') and request.endpoint and request.endpoint not in allowed_endpoints and not request.endpoint.startswith('static'):
            return redirect(url_for('main.force_change_password'))

@main_bp.route('/force-change-password', methods=['GET', 'POST'])
@login_required
def force_change_password():
    if not current_user.is_password_temporary:
        return redirect(url_for('main.dashboard'))
        
    if request.method == 'POST':
        new_password = request.form.get('new_password')
        new_password_confirm = request.form.get('new_password_confirm')
        
        if not new_password or not new_password_confirm:
            flash("Veuillez remplir tous les champs.", "error")
        elif new_password != new_password_confirm:
            flash("Les mots de passe ne correspondent pas.", "error")
        elif len(new_password) < 6:
            flash("Le mot de passe doit contenir au moins 6 caractères.", "error")
        else:
            current_user.set_password(new_password)
            current_user.is_password_temporary = False
            db.session.commit()
            flash("Votre mot de passe a été mis à jour. Bienvenue !", "success")
            if current_user.role == 'admin':
                return redirect(url_for('main.admin_panel'))
            return redirect(url_for('main.dashboard'))
            
    return render_template('change_password.html')




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
    elif current_user.role == 'teacher':
        course_ids = [c.id for c in current_user.courses_taught]
        if course_ids:
            schedules = ScheduleEvent.query.filter(
                ScheduleEvent.course_id.in_(course_ids),
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
            
            if current_user.role == 'teacher':
                teacher_name = event.class_group.name if event.class_group else "Classe"
            else:
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
    if current_user.role == 'teacher':
        courses = Course.query.filter_by(prof_id=current_user.id).all()
        # Get schedules to find which classes they teach for API
        schedules = ScheduleEvent.query.filter(ScheduleEvent.course_id.in_([c.id for c in courses])).all()
        class_ids = list(set([s.class_id for s in schedules]))
        classes = ClassGroup.query.filter(ClassGroup.id.in_(class_ids)).all()
        return render_template('teacher_grades.html', active_page='notes', courses=courses, classes=classes)

    final_data = []
    if current_user.role == 'student':
        grades = Grade.query.filter_by(student_id=current_user.id).all()
        courses_data = {}
        for g in grades:
            c_name = g.course.name if g.course else "Autre"
            if c_name not in courses_data:
                courses_data[c_name] = {'name': c_name, 'details': [], 'sum_notes': 0, 'sum_coeffs': 0}
            
            courses_data[c_name]['details'].append({
                'label': g.exam_name or 'Contrôle continu',
                'note': g.value,
                'coeff': g.coefficient or 1.0
            })
            courses_data[c_name]['sum_notes'] += g.value * (g.coefficient or 1.0)
            courses_data[c_name]['sum_coeffs'] += (g.coefficient or 1.0)
        
        for c in courses_data.values():
            avg = round(c['sum_notes'] / c['sum_coeffs'], 2) if c['sum_coeffs'] > 0 else 0
            final_data.append({
                'name': c['name'],
                'avg': avg,
                'details': c['details']
            })
            
    return render_template('notes.html', active_page='notes', grades_data=final_data)

@main_bp.route('/absences')
@login_required
def absences():
    if current_user.role == 'teacher':
        courses = Course.query.filter_by(prof_id=current_user.id).all()
        course_ids = [c.id for c in courses]
        from sqlalchemy import func
        # Find classes the teacher teaches
        schedules = ScheduleEvent.query.filter(ScheduleEvent.course_id.in_(course_ids)).all()
        class_ids = list(set([s.class_id for s in schedules]))
        classes = ClassGroup.query.filter(ClassGroup.id.in_(class_ids)).all()
        return render_template('teacher_absences.html', active_page='absences', classes=classes, courses=courses)

    absences_list = []
    total_hours = 0
    non_justified_hours = 0

    if current_user.role == 'student':
        absences_list = Absence.query.filter(Absence.student_id == current_user.id).order_by(Absence.date.desc()).all()
        
        for absence in absences_list:
            if absence.schedule:
                duration = (absence.schedule.end_time - absence.schedule.start_time).total_seconds() / 3600
            else:
                duration = 2.0
            
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
    if current_user.role == 'teacher':
        courses = Course.query.filter_by(prof_id=current_user.id).all()
        schedules = ScheduleEvent.query.filter(ScheduleEvent.course_id.in_([c.id for c in courses])).all()
        class_ids = list(set([s.class_id for s in schedules]))
        classes = ClassGroup.query.filter(ClassGroup.id.in_(class_ids)).all()
        return render_template('teacher_homeworks.html', active_page='devoirs', classes=classes, courses=courses)

    homeworks = []
    if current_user.role == 'student' and current_user.class_id:
        homeworks = Homework.query.filter_by(class_id=current_user.class_id).order_by(Homework.due_date.asc()).all()

    return render_template('devoirs.html', active_page='devoirs', homeworks=homeworks)

@main_bp.route('/annonces', methods=['GET', 'POST'])
@login_required
def annonces():
    from app.models import Announcement, ClassGroup, Course, ScheduleEvent, db
    
    if request.method == 'POST' and current_user.role in ['admin', 'teacher']:
        title = request.form.get('title')
        content = request.form.get('content')
        class_id = request.form.get('class_id')
        
        if title and content:
            new_ann = Announcement(
                author_id=current_user.user_id,
                title=title,
                content=content,
                class_id=class_id if class_id and class_id != 'global' else None
            )
            db.session.add(new_ann)
            db.session.commit()
            flash('Annonce publiée avec succès !', 'success')
            return redirect(url_for('main.annonces'))
            
    if current_user.role == 'admin':
        annonces_list = Announcement.query.order_by(Announcement.created_at.desc()).all()
    elif current_user.role == 'teacher':
        courses = Course.query.filter_by(prof_id=current_user.id).all()
        class_ids = set()
        for c in courses:
            scheds = db.session.query(ScheduleEvent.class_id).filter_by(course_id=c.id).distinct().all()
            for s in scheds:
                class_ids.add(s[0])
        class_ids = list(class_ids)
        
        annonces_list = Announcement.query.filter(
            (Announcement.class_id == None) | 
            (Announcement.class_id.in_(class_ids)) | 
            (Announcement.author_id == current_user.user_id)
        ).order_by(Announcement.created_at.desc()).all()
    else:
        annonces_list = Announcement.query.filter(
            (Announcement.class_id == None) | (Announcement.class_id == current_user.class_id)
        ).order_by(Announcement.created_at.desc()).all()
        
    classes = ClassGroup.query.all()
    nb_annonces = len(annonces_list)
    current_user.last_announcements_read_at = datetime.utcnow()
    db.session.commit()
    return render_template('annonces.html', active_page='annonces', annonces=annonces_list, classes=classes, nb_annonces=nb_annonces)

@main_bp.route('/chat')
@login_required
def chat():
    return render_template('chat.html', active_page='chat')

@main_bp.route('/api/chat/contacts', methods=['GET'])
@login_required
def get_contacts():
    users = User.query.filter(User.id != current_user.id).all()
    contacts = [{
        'user_id': u.user_id,
        'firstname': u.firstname,
        'lastname': u.lastname,
        'role': u.role,
        'profile_pic': u.profile_pic
    } for u in users]
    return jsonify(contacts)

@main_bp.route('/api/chat/messages/<contact_id>', methods=['GET'])
@login_required
def get_messages(contact_id):
    from sqlalchemy import or_, and_
    messages = ChatMessage.query.filter(
        or_(
            and_(ChatMessage.envoyeur == current_user.user_id, ChatMessage.destinataire == contact_id),
            and_(ChatMessage.envoyeur == contact_id, ChatMessage.destinataire == current_user.user_id)
        )
    ).order_by(ChatMessage.heure.asc()).all()
    
    return jsonify([{
        'id': m.id,
        'envoyeur': m.envoyeur,
        'destinataire': m.destinataire,
        'heure': m.heure.isoformat(),
        'message': m.message
    } for m in messages])

@main_bp.route('/api/chat/send', methods=['POST'])
@login_required
def send_message():
    data = request.get_json()
    if not data or 'destinataire' not in data or 'message' not in data:
        return jsonify({'error': 'Invalid request'}), 400
        
    msg = ChatMessage(
        envoyeur=current_user.user_id,
        destinataire=data['destinataire'],
        message=data['message']
    )
    db.session.add(msg)
    db.session.commit()
    
    return jsonify({
        'id': msg.id,
        'envoyeur': msg.envoyeur,
        'destinataire': msg.destinataire,
        'heure': msg.heure.isoformat(),
        'message': msg.message
    }), 201

@main_bp.route('/group-chats', methods=['GET'])
@login_required
def get_group_chats():
    # Only return groups the current user is a member of
    user_groups = GroupChatMember.query.filter_by(user_id=current_user.user_id).all()
    group_ids = [m.group_id for m in user_groups]
    groups = GroupChat.query.filter(GroupChat.id.in_(group_ids)).all()
    
    return jsonify([{
        'id': g.id,
        'name': g.name,
        'members_count': GroupChatMember.query.filter_by(group_id=g.id).count()
    } for g in groups])

@main_bp.route('/group-messages', methods=['GET'])
@login_required
def get_group_messages():
    group_chat_id = request.args.get('group_chat_id')
    if not group_chat_id:
        return jsonify({'error': 'group_chat_id required'}), 400
        
    # Check if user is in group
    member = GroupChatMember.query.filter_by(group_id=group_chat_id, user_id=current_user.user_id).first()
    if not member:
        return jsonify({'error': 'Not unauthorized'}), 403
        
    messages = GroupMessage.query.filter_by(group_id=group_chat_id).order_by(GroupMessage.created_at.asc()).all()
    
    return jsonify([{
        'sender_id': m.sender_id,
        'sender_name': m.sender.get_full_name() if m.sender else m.sender_id,
        'message': m.message,
        'created_at': m.created_at.strftime('%H:%M')
    } for m in messages])

@main_bp.route('/send-group-message', methods=['POST'])
@login_required
def send_group_message():
    data = request.get_json()
    if not data or 'group_chat_id' not in data or 'message' not in data:
        return jsonify({'error': 'Invalid request'}), 400
        
    msg = GroupMessage(
        group_id=data['group_chat_id'],
        sender_id=current_user.user_id,
        message=data['message']
    )
    db.session.add(msg)
    db.session.commit()
    
    return jsonify({'status': 'ok'}), 200

@main_bp.route('/create-group-chat', methods=['POST'])
@login_required
def create_group_chat():
    data = request.get_json()
    if not data or 'name' not in data:
        return jsonify({'error': 'Name is required'}), 400
        
    group = GroupChat(
        name=data['name'],
        description=data.get('description', '')
    )
    db.session.add(group)
    db.session.flush() # get group.id
    
    # Add creator
    db.session.add(GroupChatMember(group_id=group.id, user_id=current_user.user_id))
    
    if 'members' in data and isinstance(data['members'], list):
        for user_id in data['members']:
            # avoid adding twice if the creator is in the members list
            if user_id != current_user.user_id:
                db.session.add(GroupChatMember(group_id=group.id, user_id=user_id))
                
    db.session.commit()
    return jsonify({'status': 'ok', 'group_id': group.id}), 201

@main_bp.route('/prof')
@login_required
def teacher_panel():
    return redirect(url_for('main.dashboard'))

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
            
            if current_user.role == 'teacher':
                teacher_name = event.class_group.name if event.class_group else "Classe"
            else:
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

@main_bp.route('/admin/tickets')
@login_required
@admin_required
def admin_tickets():
    return render_template('admin_tickets.html', active_tab='tickets')

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
        msg = MailMessage(subject="Mise à jour de votre absence",
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

# ==========================================
# ROUTES TICKETS SUPPORT
# ==========================================
from app.models import SupportTicket, TicketMessage

@main_bp.route('/api/tickets', methods=['GET'])
@login_required
def get_tickets():
    if current_user.role == 'admin':
        tickets = SupportTicket.query.order_by(SupportTicket.created_at.desc()).all()
    else:
        tickets = SupportTicket.query.filter_by(user_id=current_user.user_id).order_by(SupportTicket.created_at.desc()).all()
    
    return jsonify([{
        'id': t.id,
        'title': t.title,
        'status': t.status,
        'user_name': t.user.firstname + ' ' + t.user.lastname,
        'created_at': t.created_at.strftime('%Y-%m-%d %H:%M')
    } for t in tickets])

@main_bp.route('/api/tickets', methods=['POST'])
@login_required
def create_ticket():
    data = request.json
    title = data.get('title')
    description = data.get('description')
    
    if not title or not description:
        return jsonify({'error': 'Le titre et la description sont requis.'}), 400
        
    ticket = SupportTicket(
        title=title,
        description=description,
        user_id=current_user.user_id
    )
    db.session.add(ticket)
    db.session.commit()
    
    # Optional: Admin notification or email could be triggered here
    
    return jsonify({
        'id': ticket.id,
        'title': ticket.title,
        'status': ticket.status,
        'message': 'Ticket créé avec succès.'
    }), 201

@main_bp.route('/api/tickets/<int:ticket_id>/messages', methods=['GET'])
@login_required
def get_ticket_messages(ticket_id):
    ticket = SupportTicket.query.get_or_404(ticket_id)
    
    if current_user.role != 'admin' and ticket.user_id != current_user.user_id:
        return jsonify({'error': 'Accès non autorisé.'}), 403
        
    messages = TicketMessage.query.filter_by(ticket_id=ticket.id).order_by(TicketMessage.created_at).all()
    
    res = []
    # Add initial description as the first message
    res.append({
        'id': 0,
        'sender_id': ticket.user_id,
        'sender_name': ticket.user.firstname + ' ' + ticket.user.lastname,
        'message': ticket.description,
        'created_at': ticket.created_at.strftime('%Y-%m-%d %H:%M')
    })
    
    for m in messages:
        res.append({
            'id': m.id,
            'sender_id': m.sender_id,
            'sender_name': m.sender.firstname + ' ' + m.sender.lastname if m.sender else 'Inconnu',
            'message': m.message,
            'created_at': m.created_at.strftime('%Y-%m-%d %H:%M')
        })
        
    return jsonify({'ticket': {'title': ticket.title, 'status': ticket.status, 'user_id': ticket.user_id}, 'messages': res})

@main_bp.route('/api/tickets/<int:ticket_id>/messages', methods=['POST'])
@login_required
def send_ticket_message(ticket_id):
    ticket = SupportTicket.query.get_or_404(ticket_id)
    
    if current_user.role != 'admin' and ticket.user_id != current_user.user_id:
        return jsonify({'error': 'Accès non autorisé.'}), 403
        
    if ticket.status == 'closed':
        return jsonify({'error': 'Ce ticket est fermé.'}), 400
        
    data = request.json
    message_text = data.get('message')
    
    if not message_text:
        return jsonify({'error': 'Le message est vide.'}), 400
        
    msg = TicketMessage(
        ticket_id=ticket.id,
        sender_id=current_user.user_id,
        message=message_text
    )
    
    db.session.add(msg)
    
    if current_user.role == 'admin' and data.get('close_ticket'):
        ticket.status = 'closed'
        
    db.session.commit()
    
    return jsonify({
        'id': msg.id,
        'sender_id': msg.sender_id,
        'message': msg.message,
        'created_at': msg.created_at.strftime('%Y-%m-%d %H:%M'),
        'ticket_status': ticket.status
    }), 201

@main_bp.route('/api/tickets/<int:ticket_id>/close', methods=['POST'])
@login_required
def close_ticket(ticket_id):
    ticket = SupportTicket.query.get_or_404(ticket_id)
    
    if current_user.role != 'admin' and ticket.user_id != current_user.user_id:
        return jsonify({'error': 'Accès non autorisé.'}), 403
        
    ticket.status = 'closed'
    db.session.commit()
    
    return jsonify({'status': 'closed', 'message': 'Ticket fermé avec succès.'})
@main_bp.route('/api/teacher/students/<int:class_id>', methods=['GET'])
@login_required
def api_teacher_students(class_id):
    if current_user.role != 'teacher':
        return jsonify({'error': 'Unauthorized'}), 403
    students = User.query.filter_by(class_id=class_id, role='student').all()
    return jsonify([{'id': s.id, 'user_id': s.user_id, 'firstname': s.firstname, 'lastname': s.lastname, 'profile_pic': s.profile_pic} for s in students])


@main_bp.route('/api/teacher/schedules_by_date', methods=['GET'])
@login_required
def api_teacher_schedules_by_date():
    if current_user.role != 'teacher':
        return jsonify({'error': 'Unauthorized'}), 403
        
    date_str = request.args.get('date')
    if not date_str:
        return jsonify([])
        
    try:
        from datetime import datetime
        query_date = datetime.strptime(date_str, '%Y-%m-%d').date()
    except Exception as e:
        return jsonify([])
        
    from app.models import Course, ScheduleEvent
    courses = Course.query.filter_by(prof_id=current_user.id).all()
    course_ids = [c.id for c in courses]
    
    if not course_ids:
        return jsonify([])
        
    from sqlalchemy import func
    schedules = ScheduleEvent.query.filter(
        ScheduleEvent.course_id.in_(course_ids),
        func.date(ScheduleEvent.start_time) == query_date
    ).order_by(ScheduleEvent.start_time).all()
    
    result = []
    for s in schedules:
        result.append({
            'schedule_id': s.id,
            'class_id': s.class_id,
            'class_name': s.class_group.name,
            'course_id': s.course_id,
            'course_name': s.course.name,
            'start_time': s.start_time.strftime('%H:%M'),
            'end_time': s.end_time.strftime('%H:%M')
        })
        
    return jsonify(result)

@main_bp.route('/api/teacher/absences', methods=['GET'])
@login_required
def api_get_absences():
    if current_user.role != 'teacher':
        return jsonify({'error': 'Unauthorized'}), 403
    class_id = request.args.get('class_id')
    course_id = request.args.get('course_id')
    date_str = request.args.get('date')
    if not (class_id and course_id and date_str):
        return jsonify({'error': 'Missing parameters'}), 400
    try:
        query_date = datetime.strptime(date_str, '%Y-%m-%d').date()
    except ValueError:
        return jsonify({'error': 'Invalid date format'}), 400
    absences = Absence.query.join(User).filter(
        User.class_id == class_id,
        Absence.course_id == course_id,
        db.func.date(Absence.date) == query_date
    ).all()
    return jsonify([{'student_id': a.student_id, 'is_justified': a.is_justified} for a in absences])

@main_bp.route('/api/teacher/absences/toggle', methods=['POST'])
@login_required
def api_toggle_absence():
    if current_user.role != 'teacher':
        return jsonify({'error': 'Unauthorized'}), 403
    data = request.get_json()
    student_id = data.get('student_id')
    course_id = data.get('course_id')
    date_str = data.get('date')
    try:
        query_date = datetime.strptime(date_str, '%Y-%m-%d').date()
    except ValueError:
        return jsonify({'error': 'Invalid date format'}), 400

    absence = Absence.query.filter(
        Absence.student_id == student_id,
        Absence.course_id == course_id,
        db.func.date(Absence.date) == query_date
    ).first()
    
    if absence:
        db.session.delete(absence)
        is_absent = False
    else:
        new_absence = Absence(student_id=student_id, course_id=course_id, date=query_date)
        db.session.add(new_absence)
        is_absent = True
    
    db.session.commit()
    return jsonify({'success': True, 'is_absent': is_absent})

@main_bp.route('/api/teacher/grades', methods=['GET'])
@login_required
def api_get_grades():
    if current_user.role != 'teacher':
        return jsonify({'error': 'Unauthorized'}), 403
    class_id = request.args.get('class_id')
    course_id = request.args.get('course_id')
    grades = Grade.query.join(User).filter(User.class_id == class_id, Grade.course_id == course_id).all()
    return jsonify([{'id': g.id, 'student_id': g.student_id, 'value': g.value, 'exam_name': g.exam_name, 'coefficient': g.coefficient} for g in grades])

@main_bp.route('/api/teacher/grades', methods=['POST'])
@login_required
def api_submit_grade():
    if current_user.role != 'teacher':
        return jsonify({'error': 'Unauthorized'}), 403
    data = request.get_json()
    student_id = data.get('student_id')
    course_id = data.get('course_id')
    value = data.get('value')
    exam_name = data.get('exam_name', 'Contrôle continu')
    coefficient = data.get('coefficient', 1.0)
    
    new_grade = Grade(student_id=student_id, course_id=course_id, value=float(value), coefficient=float(coefficient), exam_name=exam_name)
    db.session.add(new_grade)
    db.session.commit()
    return jsonify({'success': True})

@main_bp.route('/api/teacher/homeworks', methods=['GET'])
@login_required
def api_get_homeworks():
    if current_user.role != 'teacher':
        return jsonify({'error': 'Unauthorized'}), 403
    class_id = request.args.get('class_id')
    course_id = request.args.get('course_id')
    homeworks = Homework.query.filter_by(class_id=class_id, course_id=course_id).all()
    return jsonify([{'id': h.id, 'title': h.title, 'description': h.description, 'due_date': h.due_date.strftime('%Y-%m-%d %H:%M') if h.due_date else None} for h in homeworks])

@main_bp.route('/api/teacher/homeworks', methods=['POST'])
@login_required
def api_submit_homework():
    if current_user.role != 'teacher':
        return jsonify({'error': 'Unauthorized'}), 403
    data = request.get_json()
    class_id = data.get('class_id')
    course_id = data.get('course_id')
    title = data.get('title')
    description = data.get('description')
    due_date_str = data.get('due_date')
    
    try:
        due_date = datetime.strptime(due_date_str, '%Y-%m-%dT%H:%M') if due_date_str else None
    except ValueError:
        try:
            due_date = datetime.strptime(due_date_str, '%Y-%m-%d')
        except ValueError:
            due_date = datetime.utcnow()
            
    hw = Homework(course_id=course_id, class_id=class_id, title=title, description=description, due_date=due_date)
    db.session.add(hw)
    db.session.commit()
    return jsonify({'success': True})

@main_bp.route('/api/teacher/absences/batch', methods=['POST'])
@login_required
def api_batch_absences():
    if current_user.role != 'teacher':
        return jsonify({'error': 'Unauthorized'}), 403
    data = request.get_json()
    class_id = data.get('class_id')
    course_id = data.get('course_id')
    date_str = data.get('date')
    absent_ids = data.get('absent_ids', [])
    
    try:
        query_date = datetime.strptime(date_str, '%Y-%m-%d').date()
    except ValueError:
        return jsonify({'error': 'Invalid date format'}), 400

    students = User.query.filter_by(class_id=class_id, role='student').all()
    student_ids = [s.id for s in students]
    
    db.session.query(Absence).filter(
        Absence.student_id.in_(student_ids),
        Absence.course_id == course_id,
        db.func.date(Absence.date) == query_date
    ).delete(synchronize_session=False)
    
    schedule_id = data.get('schedule_id')
    for sid in absent_ids:
        if sid in student_ids:
            new_abs = Absence(student_id=sid, course_id=course_id, date=query_date, schedule_id=schedule_id)
            db.session.add(new_abs)
            
    db.session.commit()
    return jsonify({'success': True})

