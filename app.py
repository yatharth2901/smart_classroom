from flask import Flask, render_template, request, redirect, url_for, flash, session
from werkzeug.utils import secure_filename
from modules import db, User, Announcement, Recording, Mentor
from functools import wraps
import os

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///C:/Users/rekha/Desktop/TB/smart classroom/instance/database.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.secret_key = 'cb61af8951a169099b6d69c20ac6a563fe8e23f23b3dbb77b7e01fc1a36d8f69'

# File Upload Configuration
UPLOAD_FOLDER = 'static/videos'
ALLOWED_EXTENSIONS = {'mp4', 'mov', 'avi', 'mkv'}
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

# Initialize the database
db.init_app(app)

# Ensure the upload folder exists
if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)

# Create tables if they don't exist
with app.app_context():
    db.create_all()

# Helper: Check allowed file extensions
def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

# Role-based access decorator
def role_required(required_role):
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if 'user_id' not in session or session.get('role') != required_role:
                flash('Access denied!', 'danger')
                return redirect(url_for('login'))
            return f(*args, **kwargs)
        return decorated_function
    return decorator

# ROUTES #################################

@app.route('/')
def index():
    return render_template('index.html')

# Signup route
@app.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        role = request.form.get('role')

        # Check if username already exists
        if User.query.filter_by(username=username).first():
            flash('Username already exists! Please choose a different one.', 'danger')
            return redirect(url_for('signup'))

        # Create a new user and store it in the database
        new_user = User(username=username, password=password, role=role)
        db.session.add(new_user)
        db.session.commit()

        flash('Signup successful! Please log in.', 'success')
        return redirect(url_for('login'))

    return render_template('signup.html')


# Login route
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')

        # Check user credentials
        user = User.query.filter_by(username=username, password=password).first()
        if user:
            # Store session information
            session['user_id'] = user.id
            session['username'] = user.username
            session['role'] = user.role

            flash('Login successful!', 'success')

            # Redirect based on role
            if user.role == 'student':
                return redirect(url_for('student_dashboard'))
            elif user.role == 'teacher':
                return redirect(url_for('teacher_dashboard'))

        flash('Invalid username or password!', 'danger')
        return redirect(url_for('login'))

    return render_template('login.html')


# Logout route
@app.route('/logout')
def logout():
    session.clear()
    flash('Logged out successfully.', 'info')
    return redirect(url_for('index'))

# Student Dashboard
@app.route('/student_dashboard')
def student_dashboard():
    if 'user_id' not in session or session.get('role') != 'student':
        flash('Access denied! Please log in as a student.', 'danger')
        return redirect(url_for('login'))
    return render_template('student_dashboard.html')

#techer dasboard
@app.route('/teacher_dashboard')
def teacher_dashboard():
    if 'user_id' not in session or session.get('role') != 'teacher':
        flash('Access denied! Please log in as a teacher.', 'danger')
        return redirect(url_for('login'))
    return render_template('teacher_dashboard.html')


# Admin Dashboard
@app.route('/admin-dashboard')
def admin_dashboard():
    if 'user_id' not in session or session.get('role') != 'admin':
        flash('Access denied! Please log in as an admin.', 'danger')
        return redirect(url_for('login'))
    return render_template('admin_dashboard.html')

# Announcements route
@app.route('/announcements', methods=['GET', 'POST'])
def announcements():
    if request.method == 'POST' and 'role' in session and session['role'] == 'teacher':
        title = request.form.get('title')
        content = request.form.get('content')

        if title and content:
            new_announcement = Announcement(title=title, content=content)
            db.session.add(new_announcement)
            db.session.commit()
            flash('Announcement added successfully!', 'success')

    announcements = Announcement.query.order_by(Announcement.date_posted.desc()).all()
    return render_template('announcements.html', announcements=announcements)

# Recordings route
@app.route('/recordings', methods=['GET', 'POST'])
def recordings():
    if request.method == 'POST' and 'role' in session and session['role'] == 'teacher':
        if 'video' not in request.files:
            flash('No file selected!', 'danger')
            return redirect(url_for('recordings'))

        video = request.files['video']
        if video and allowed_file(video.filename):
            filename = secure_filename(video.filename)
            filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            video.save(filepath)

            new_recording = Recording(title=request.form.get('title'), url=filename)
            db.session.add(new_recording)
            db.session.commit()
            flash('Recording uploaded successfully!', 'success')

    recordings = Recording.query.order_by(Recording.date_uploaded.desc()).all()
    return render_template('recordings.html', recordings=recordings)

# Mentors route
@app.route('/mentors', methods=['GET', 'POST'])
def mentors():
    if request.method == 'POST' and 'role' in session and session['role'] == 'student':
        name = request.form.get('name')
        specialization = request.form.get('specialization')
        email = request.form.get('email')

        new_mentor = Mentor(name=name, specialization=specialization, email=email)
        db.session.add(new_mentor)
        db.session.commit()
        flash('Mentor request added successfully!', 'success')

    mentors = Mentor.query.all()
    return render_template('mentors.html', mentors=mentors)

if __name__ == '__main__':
    app.run(debug=True)
