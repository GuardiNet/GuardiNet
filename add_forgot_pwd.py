import os
import re

main_path = 'app/routes/main.py'
with open(main_path, 'r', encoding='utf-8') as f:
    content = f.read()

if 'PasswordReset' not in content:
    content = content.replace('from app.models import db, User,', 'from app.models import db, User, PasswordReset,')

new_routes = """
import secrets

@main_bp.route('/forgot-password', methods=['GET', 'POST'])
def forgot_password():
    if current_user.is_authenticated:
        return redirect(url_for('main.dashboard'))
        
    if request.method == 'POST':
        email = request.form.get('email')
        user = User.query.filter_by(email=email).first()
        
        if user:
            token = secrets.token_urlsafe(32)
            reset = PasswordReset(
                user_id=user.id,
                email=user.email,
                token=token,
                expires_at=datetime.utcnow() + timedelta(hours=1)
            )
            db.session.add(reset)
            db.session.commit()
            
            reset_url = url_for('main.reset_password', token=token, _external=True)
            
            try:
                from flask_mail import Message as MailMessage
                from app import mail
                
                msg = MailMessage('Réinitialisation de votre mot de passe',
                              sender=current_app.config.get('MAIL_DEFAULT_SENDER', 'noreply@guardinet.fr'),
                              recipients=[user.email])
                msg.body = f'''Bonjour {user.firstname},
                
Une demande de réinitialisation de mot de passe a été effectuée pour votre compte GuardiNet.
Pour réinitialiser votre mot de passe, visitez le lien suivant :
{reset_url}

Si vous n'avez pas demandé cette réinitialisation, veuillez ignorer cet e-mail.

Cordialement,
L'équipe GuardiNet'''
                mail.send(msg)
            except Exception as e:
                print(f"Erreur envoi email: {e}")
                
        flash('Si un compte existe avec cette adresse email, un lien de réinitialisation vous a été envoyé.', 'success')
        return redirect(url_for('main.login'))
        
    return render_template('forgot_password.html')

@main_bp.route('/reset-password/<token>', methods=['GET', 'POST'])
def reset_password(token):
    if current_user.is_authenticated:
        return redirect(url_for('main.dashboard'))
        
    reset = PasswordReset.query.filter_by(token=token, used=False).first()
    
    if not reset or not reset.is_valid():
        flash('Le lien de réinitialisation est invalide ou a expiré.', 'error')
        return redirect(url_for('main.login'))
        
    if request.method == 'POST':
        password = request.form.get('password')
        confirm_password = request.form.get('confirm_password')
        
        if password != confirm_password:
            flash('Les mots de passe ne correspondent pas.', 'error')
            return render_template('reset_password.html', token=token)
            
        user = User.query.get(reset.user_id)
        user.set_password(password)
        reset.used = True
        
        db.session.commit()
        
        flash('Votre mot de passe a été mis à jour avec succès.', 'success')
        return redirect(url_for('main.login'))
        
    return render_template('reset_password.html', token=token)

@main_bp.route('/admin/users/<int:user_id>/force-reset-password', methods=['POST'])
@login_required
@admin_required
def admin_force_reset_password(user_id):
    user = User.query.get_or_404(user_id)
    new_password = secrets.token_urlsafe(8)
    user.set_password(new_password)
    user.is_password_temporary = True
    db.session.commit()
    
    try:
        from flask_mail import Message as MailMessage
        from app import mail
        
        msg = MailMessage('Nouveau mot de passe',
                      sender=current_app.config.get('MAIL_DEFAULT_SENDER', 'noreply@guardinet.fr'),
                      recipients=[user.email])
        msg.body = f'''Bonjour {user.firstname},
        
Votre mot de passe GuardiNet a été réinitialisé par un administrateur.
Voici votre mot de passe temporaire : {new_password}

Connectez-vous avec ce mot de passe.

Cordialement,
L'équipe GuardiNet'''
        mail.send(msg)
        flash(f'Mot de passe réinitialisé pour {user.firstname} {user.lastname}. Un email lui a été envoyé.', 'success')
    except Exception as e:
        print(f"Erreur envoi email: {e}")
        flash(f'Le mot de passe a été réinitialisé à : {new_password}, mais l\\'email n\\'a pu être envoyé.', 'error')
        
    return redirect(url_for('main.admin_users'))
"""

if 'def forgot_password' not in content:
    content += '\n' + new_routes

with open(main_path, 'w', encoding='utf-8') as f:
    f.write(content)

print('Routes added!')
