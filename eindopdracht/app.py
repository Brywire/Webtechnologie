from flask import Flask, render_template, redirect, url_for, request, flash
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, logout_user, login_required, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import date, datetime

# ── App setup ──────────────────────────────────────────────────────────────
app = Flask(__name__)
app.config['SECRET_KEY'] = 'geheim-sleutel-verander-dit-later'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///studyflow.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)

login_manager = LoginManager(app)
login_manager.login_view = 'login'           # stuur niet-ingelogde users naar /login
login_manager.login_message = 'Log eerst in om je taken te bekijken.'
login_manager.login_message_category = 'error'


# ── Database modellen ──────────────────────────────────────────────────────

class User(UserMixin, db.Model):
    id       = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80),  unique=True, nullable=False)
    email    = db.Column(db.String(120), unique=True, nullable=False)
    password = db.Column(db.String(200), nullable=False)
    tasks    = db.relationship('Task', backref='owner', lazy=True)


class Task(db.Model):
    id          = db.Column(db.Integer, primary_key=True)
    title       = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text, default='')
    subject     = db.Column(db.String(100), default='')
    priority    = db.Column(db.String(20),  default='medium')   # low / medium / high
    deadline    = db.Column(db.Date, nullable=True)
    done        = db.Column(db.Boolean, default=False)
    created_at  = db.Column(db.DateTime, default=datetime.utcnow)
    user_id     = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)


@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))


# ── Routes ─────────────────────────────────────────────────────────────────

# -- Homepage / takenlijst --
@app.route('/')
@login_required
def index():
    filter_param = request.args.get('filter', 'all')
    today = date.today()

    # Haal alleen de taken op van de ingelogde gebruiker
    query = Task.query.filter_by(user_id=current_user.id)

    if filter_param == 'open':
        query = query.filter_by(done=False)
    elif filter_param == 'done':
        query = query.filter_by(done=True)
    elif filter_param == 'urgent':
        # Taken die niet af zijn én deadline binnen 3 dagen (of verlopen)
        query = query.filter(
            Task.done == False,
            Task.deadline != None,
            Task.deadline <= date.fromordinal(today.toordinal() + 3)
        )

    tasks = query.order_by(Task.deadline.asc().nullslast(), Task.created_at.desc()).all()

    all_tasks = Task.query.filter_by(user_id=current_user.id).all()
    stats = {
        'total': len(all_tasks),
        'done':  sum(1 for t in all_tasks if t.done),
        'open':  sum(1 for t in all_tasks if not t.done),
    }

    return render_template('index.html', tasks=tasks, today=today, filter=filter_param, stats=stats)


# -- Registreren --
@app.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('index'))

    if request.method == 'POST':
        username         = request.form.get('username', '').strip()
        email            = request.form.get('email', '').strip()
        password         = request.form.get('password', '')
        confirm_password = request.form.get('confirm_password', '')

        # Validatie
        if not username or not email or not password:
            flash('Vul alle verplichte velden in.', 'error')
            return redirect(url_for('register'))

        if password != confirm_password:
            flash('Wachtwoorden komen niet overeen.', 'error')
            return redirect(url_for('register'))

        if len(password) < 6:
            flash('Wachtwoord moet minimaal 6 tekens zijn.', 'error')
            return redirect(url_for('register'))

        if User.query.filter_by(username=username).first():
            flash('Deze gebruikersnaam is al in gebruik.', 'error')
            return redirect(url_for('register'))

        if User.query.filter_by(email=email).first():
            flash('Dit e-mailadres is al in gebruik.', 'error')
            return redirect(url_for('register'))

        # Gebruiker aanmaken
        hashed_pw = generate_password_hash(password)
        new_user  = User(username=username, email=email, password=hashed_pw)
        db.session.add(new_user)
        db.session.commit()

        flash('Account aangemaakt! Je kunt nu inloggen.', 'success')
        return redirect(url_for('login'))

    return render_template('register.html')


# -- Inloggen --
@app.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('index'))

    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        password = request.form.get('password', '')

        user = User.query.filter_by(username=username).first()

        if not user or not check_password_hash(user.password, password):
            flash('Gebruikersnaam of wachtwoord klopt niet.', 'error')
            return redirect(url_for('login'))

        login_user(user)
        flash(f'Welkom terug, {user.username}!', 'success')
        return redirect(url_for('index'))

    return render_template('login.html')


# -- Uitloggen --
@app.route('/logout')
@login_required
def logout():
    logout_user()
    flash('Je bent uitgelogd.', 'success')
    return redirect(url_for('login'))


# -- Profielpagina --
@app.route('/profile')
@login_required
def profile():
    total = len(current_user.tasks)
    done  = sum(1 for t in current_user.tasks if t.done)
    open_ = total - done
    return render_template('profile.html', total=total, done=done, open_=open_)


# -- Taak toevoegen --
@app.route('/add', methods=['GET', 'POST'])
@login_required
def add_task():
    today = date.today()

    if request.method == 'POST':
        title       = request.form.get('title', '').strip()
        description = request.form.get('description', '').strip()
        subject     = request.form.get('subject', '').strip()
        priority    = request.form.get('priority', 'medium')
        deadline_str = request.form.get('deadline', '')

        if not title:
            flash('Een taaknaam is verplicht.', 'error')
            return redirect(url_for('add_task'))

        # Deadline omzetten naar een date-object (of None als leeg)
        deadline = None
        if deadline_str:
            try:
                deadline = datetime.strptime(deadline_str, '%Y-%m-%d').date()
            except ValueError:
                flash('Ongeldige deadline datum.', 'error')
                return redirect(url_for('add_task'))

        new_task = Task(
            title       = title,
            description = description,
            subject     = subject,
            priority    = priority,
            deadline    = deadline,
            user_id     = current_user.id
        )
        db.session.add(new_task)
        db.session.commit()

        flash(f'Taak "{title}" toegevoegd!', 'success')
        return redirect(url_for('index'))

    return render_template('add_task.html', today=today)


# -- Taak bewerken --
@app.route('/task/<int:task_id>/edit', methods=['GET', 'POST'])
@login_required
def edit_task(task_id):
    task = Task.query.get_or_404(task_id)

    if task.user_id != current_user.id:
        flash('Je hebt geen toegang tot deze taak.', 'error')
        return redirect(url_for('index'))

    if request.method == 'POST':
        title        = request.form.get('title', '').strip()
        description  = request.form.get('description', '').strip()
        subject      = request.form.get('subject', '').strip()
        priority     = request.form.get('priority', 'medium')
        deadline_str = request.form.get('deadline', '')

        if not title:
            flash('Een taaknaam is verplicht.', 'error')
            return redirect(url_for('edit_task', task_id=task_id))

        deadline = None
        if deadline_str:
            try:
                deadline = datetime.strptime(deadline_str, '%Y-%m-%d').date()
            except ValueError:
                flash('Ongeldige deadline datum.', 'error')
                return redirect(url_for('edit_task', task_id=task_id))

        task.title       = title
        task.description = description
        task.subject     = subject
        task.priority    = priority
        task.deadline    = deadline
        db.session.commit()

        flash(f'Taak "{title}" bijgewerkt!', 'success')
        return redirect(url_for('index'))

    return render_template('edit_task.html', task=task)


# -- Taak afvinken / terugzetten --
@app.route('/task/<int:task_id>/toggle', methods=['POST'])
@login_required
def toggle_task(task_id):
    task = Task.query.get_or_404(task_id)

    # Controleer of de taak van de ingelogde gebruiker is
    if task.user_id != current_user.id:
        flash('Je hebt geen toegang tot deze taak.', 'error')
        return redirect(url_for('index'))

    task.done = not task.done
    db.session.commit()
    return redirect(url_for('index'))


# -- Taak verwijderen --
@app.route('/task/<int:task_id>/delete', methods=['POST'])
@login_required
def delete_task(task_id):
    task = Task.query.get_or_404(task_id)

    if task.user_id != current_user.id:
        flash('Je hebt geen toegang tot deze taak.', 'error')
        return redirect(url_for('index'))

    db.session.delete(task)
    db.session.commit()
    flash('Taak verwijderd.', 'success')
    return redirect(url_for('index'))


# ── Start ──────────────────────────────────────────────────────────────────

if __name__ == '__main__':
    with app.app_context():
        db.create_all()   # maakt de database + tabellen aan als ze nog niet bestaan
    app.run(debug=True)