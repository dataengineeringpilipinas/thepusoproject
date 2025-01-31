from flask import Flask, render_template, request, redirect, url_for, session, g
import sqlite3

app = Flask(__name__)
app.secret_key = 'your_secret_key'
DATABASE = 'users.db'

def get_db():
    db = getattr(g, '_database', None)
    if db is None:
        db = g._database = sqlite3.connect(DATABASE)
        db.row_factory = sqlite3.Row
    return db

def init_db():
    with app.app_context():
        db = get_db()
        cursor = db.cursor()
        cursor.execute('''CREATE TABLE IF NOT EXISTS users (
                            id INTEGER PRIMARY KEY AUTOINCREMENT,
                            username TEXT UNIQUE NOT NULL,
                            password TEXT NOT NULL)''')
        db.commit()

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        
        db = get_db()
        try:
            db.execute('INSERT INTO users (username, password) VALUES (?, ?)', (username, password))
            db.commit()
            return redirect(url_for('login'))
        except sqlite3.IntegrityError:
            return 'Username already taken. <a href="/signup">Try again</a>'
    
    return render_template('signup.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        
        db = get_db()
        user = db.execute('SELECT * FROM users WHERE username = ? AND password = ?', (username, password)).fetchone()
        
        if user:
            session['user'] = username
            return redirect(url_for('index'))
        else:
            return 'Invalid credentials. <a href="/login">Try again</a>'
    
    return render_template('login.html')

@app.route('/logout')
def logout():
    session.pop('user', None)
    return redirect(url_for('index'))

# New Routes for Menu Pages
@app.route('/startyourjourney')
def startyourjourney():
    return render_template('startyourjourney.html')

@app.route('/projectideas')
def projectideas():
    return render_template('projectideas.html')

@app.route('/pusoprojects')
def pusoprojects():
    return render_template('pusoprojects.html')

@app.route('/datamasters')
def datamasters():
    return render_template('datamasters.html')

@app.route('/mentors')
def mentors():
    return render_template('mentors.html')

@app.route('/blogs')
def blogs():
    return render_template('blogs.html')

@app.route('/aboutdep')
def aboutdep():
    return render_template('aboutdep.html')

@app.route('/contact')
def contact():
    return render_template('contact.html')

@app.teardown_appcontext
def close_connection(exception):
    db = getattr(g, '_database', None)
    if db is not None:
        db.close()

if __name__ == '__main__':
    init_db()
    app.run(debug=True)