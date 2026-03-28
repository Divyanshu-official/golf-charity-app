from flask import Flask, render_template, request, redirect, url_for, session
from flask_sqlalchemy import SQLAlchemy
import random

app = Flask(__name__)

app.config['SECRET_KEY'] = 'secret123'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///database.db'

db = SQLAlchemy(app)

# ------------------ MODELS ------------------

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100))
    email = db.Column(db.String(100), unique=True)
    password = db.Column(db.String(100))
    subscription_status = db.Column(db.String(20), default="inactive")
    charity_id = db.Column(db.Integer)

class Score(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer)
    score = db.Column(db.Integer)
    date = db.Column(db.String(50))

class Charity(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100))

# ------------------ DATABASE INIT ------------------

with app.app_context():
    db.create_all()

    if Charity.query.count() == 0:
        db.session.add(Charity(name="Help Children"))
        db.session.add(Charity(name="Save Environment"))
        db.session.add(Charity(name="Education Fund"))
        db.session.commit()

# ------------------ ROUTES ------------------

@app.route('/')
def home():
    return redirect(url_for('login'))

# ------------------ SIGNUP ------------------

@app.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == 'POST':
        name = request.form['name']
        email = request.form['email']
        password = request.form['password']

        existing_user = User.query.filter_by(email=email).first()
        if existing_user:
            return "Email already exists"

        user = User(name=name, email=email, password=password)
        db.session.add(user)
        db.session.commit()

        return redirect(url_for('login'))

    return render_template('signup.html')

# ------------------ LOGIN ------------------

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']

        user = User.query.filter_by(email=email, password=password).first()

        if user:
            session['user_id'] = user.id
            return redirect(url_for('dashboard'))

        return "Invalid credentials"

    return render_template('login.html')

# ------------------ DASHBOARD ------------------

@app.route('/dashboard')
def dashboard():
    if 'user_id' not in session:
        return redirect(url_for('login'))

    user = User.query.get_or_404(session['user_id'])
    scores = Score.query.filter_by(user_id=user.id).order_by(Score.id.desc()).all()
    charities = Charity.query.all()

    return render_template('dashboard.html', user=user, scores=scores, charities=charities)

# ------------------ ADD SCORE ------------------

@app.route('/add_score', methods=['POST'])
def add_score():
    if 'user_id' not in session:
        return redirect(url_for('login'))

    user_id = session['user_id']
    score_value = int(request.form['score'])
    date = request.form['date']

    if score_value < 1 or score_value > 45:
        return "Score must be between 1 and 45"

    scores = Score.query.filter_by(user_id=user_id).order_by(Score.id).all()

    if len(scores) >= 5:
        db.session.delete(scores[0])

    new_score = Score(user_id=user_id, score=score_value, date=date)
    db.session.add(new_score)
    db.session.commit()

    return redirect(url_for('dashboard'))

# ------------------ SUBSCRIPTION ------------------

@app.route('/subscribe')
def subscribe():
    if 'user_id' not in session:
        return redirect(url_for('login'))

    user = User.query.get(session['user_id'])
    user.subscription_status = "active"

    db.session.commit()
    return redirect(url_for('dashboard'))

# ------------------ CHARITY ------------------

@app.route('/select_charity', methods=['POST'])
def select_charity():
    if 'user_id' not in session:
        return redirect(url_for('login'))

    user = User.query.get(session['user_id'])
    user.charity_id = int(request.form['charity_id'])

    db.session.commit()
    return redirect(url_for('dashboard'))

# ------------------ ADMIN (UPDATED ✅) ------------------

@app.route('/admin')
def admin():
    users = User.query.all()
    return render_template('admin.html', users=users)

# ------------------ DRAW SYSTEM ------------------

@app.route('/run_draw')
def run_draw():
    if 'user_id' not in session:
        return redirect(url_for('login'))

    user_id = session['user_id']

    scores = Score.query.filter_by(user_id=user_id).all()
    user_scores = [s.score for s in scores]

    draw_numbers = [random.randint(1, 45) for _ in range(5)]

    matches = list(set(user_scores) & set(draw_numbers))

    reward = ""
    if len(matches) >= 3:
        reward = "🎉 Congratulations! You win a reward!"
    else:
        reward = "😢 No reward this time. Try again!"

    return render_template(
        'draw.html',
        draw_numbers=draw_numbers,
        user_scores=user_scores,
        matches=matches,
        reward=reward
    )

# ------------------ LOGOUT ------------------

@app.route('/logout')
def logout():
    session.pop('user_id', None)
    return redirect(url_for('login'))
