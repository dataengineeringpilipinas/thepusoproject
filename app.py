import sqlite3
from datetime import datetime
from flask import Flask, redirect, render_template, request, session, url_for, g, flash
from flask_bootstrap import Bootstrap
from werkzeug.security import generate_password_hash, check_password_hash
import matplotlib.pyplot as plt
import matplotlib
matplotlib.use('Agg')
import os
import re
from urllib.parse import urlparse
import logging
from logging.handlers import RotatingFileHandler
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

app = Flask(__name__)
# Use environment variable for secret key, generate secure random key as fallback
app.secret_key = os.environ.get('SECRET_KEY', os.urandom(24))

# Configure logging
if not app.debug:  # Only log to file in production
    if not os.path.exists('logs'):
        os.mkdir('logs')
    file_handler = RotatingFileHandler('logs/pusoproject.log', maxBytes=10240, backupCount=10)
    file_handler.setFormatter(logging.Formatter(
        '%(asctime)s %(levelname)s: %(message)s [in %(pathname)s:%(lineno)d]'
    ))
    file_handler.setLevel(logging.INFO)
    app.logger.addHandler(file_handler)
    app.logger.setLevel(logging.INFO)
    app.logger.info('Puso Project startup')

# Database configuration
DATABASE = os.environ.get('CITIZENDEVS_DB_PATH', './citizendevs.db')
DATAJOBS_DATABASE = os.environ.get('DATAJOBS_DB_PATH', './datajobs.db')
LESSONS_FILE = os.environ.get('LESSONS_FILE_PATH', './lessons.txt')

def get_db(db_name=None):
    """Open a new database connection if there is none yet for the current application context."""
    if db_name is None:
        db_name = DATABASE  # Default to the main database if no name is provided

    # Create a unique key for each database connection
    db_key = f'db_{db_name.replace("./", "").replace(".db", "")}'
    
    if not hasattr(g, db_key):
        # Remove check_same_thread=False - it's unsafe and not needed with proper connection management
        db = sqlite3.connect(db_name)
        db.row_factory = sqlite3.Row  # Allows access by column name
        # Enable foreign key constraints
        db.execute('PRAGMA foreign_keys = ON')
        setattr(g, db_key, db)
    
    return getattr(g, db_key)

@app.teardown_appcontext
def close_connection(exception):
    """Close all database connections at the end of the request."""
    # Close the main database connection
    if hasattr(g, 'db_citizendevs'):
        db = getattr(g, 'db_citizendevs')
        if db is not None:
            db.close()
            delattr(g, 'db_citizendevs')
    
    # Close the datajobs database connection
    if hasattr(g, 'db_datajobs'):
        db = getattr(g, 'db_datajobs')
        if db is not None:
            db.close()
            delattr(g, 'db_datajobs')

# Input validation functions
def validate_job_data(form_data):
    """
    Validate job posting form data.
    Returns a list of error messages if validation fails, empty list if valid.
    """
    errors = []
    
    # Validate required fields
    required_fields = ['datePosted', 'jobTitle', 'jobCategory', 'companyName', 'location']
    for field in required_fields:
        if not form_data.get(field, '').strip():
            errors.append(f"{field.replace('jobCategory', 'Job Category').replace('companyName', 'Company Name').replace('datePosted', 'Date Posted').replace('jobTitle', 'Job Title').title()} is required")
    
    # Validate date format
    if form_data.get('datePosted'):
        try:
            datetime.strptime(form_data['datePosted'], '%Y-%m-%d')
        except ValueError:
            errors.append("Date Posted must be in YYYY-MM-DD format")
    
    # Validate job title length
    if form_data.get('jobTitle') and len(form_data['jobTitle']) > 200:
        errors.append("Job Title must be less than 200 characters")
    
    # Validate URL format
    if form_data.get('jobPostLink'):
        try:
            result = urlparse(form_data['jobPostLink'])
            if not all([result.scheme, result.netloc]) or result.scheme not in ['http', 'https']:
                errors.append("Job Post Link must be a valid URL starting with http:// or https://")
        except Exception:
            errors.append("Job Post Link must be a valid URL")
    
    # Validate application deadline if provided
    if form_data.get('applicationDeadline'):
        try:
            deadline = datetime.strptime(form_data['applicationDeadline'], '%Y-%m-%d')
            posted_date = datetime.strptime(form_data.get('datePosted', ''), '%Y-%m-%d')
            if deadline < posted_date:
                errors.append("Application Deadline cannot be before Date Posted")
        except ValueError:
            errors.append("Application Deadline must be in YYYY-MM-DD format")
    
    return errors

def validate_user_credentials(username, password):
    """
    Validate user registration credentials.
    Returns a list of error messages if validation fails, empty list if valid.
    """
    errors = []
    
    # Validate username
    if not username or not username.strip():
        errors.append("Username is required")
    elif len(username) < 3:
        errors.append("Username must be at least 3 characters long")
    elif len(username) > 50:
        errors.append("Username must be less than 50 characters")
    elif not re.match(r'^[a-zA-Z0-9_]+$', username):
        errors.append("Username can only contain letters, numbers, and underscores")
    
    # Validate password
    if not password or not password.strip():
        errors.append("Password is required")
    elif len(password) < 6:
        errors.append("Password must be at least 6 characters long")
    elif len(password) > 100:
        errors.append("Password must be less than 100 characters")
    
    return errors

# Utility functions for common operations
def ensure_user_table_exists():
    """Ensure the user table exists with proper schema."""
    db = get_db()
    cur = db.cursor()
    cur.execute('''
        CREATE TABLE IF NOT EXISTS user (
            username TEXT PRIMARY KEY,
            password TEXT NOT NULL,
            Nickname TEXT,
            PY4E1 TEXT DEFAULT 'To Do',
            PY4E2 TEXT DEFAULT 'To Do',
            PY4E3 TEXT DEFAULT 'To Do',
            PY4E4 TEXT DEFAULT 'To Do',
            PY4E5 TEXT DEFAULT 'To Do',
            PY4E6 TEXT DEFAULT 'To Do',
            PY4E7 TEXT DEFAULT 'To Do',
            PY4E8 TEXT DEFAULT 'To Do',
            PY4E9 TEXT DEFAULT 'To Do',
            PY4E10 TEXT DEFAULT 'To Do',
            PY4E11 TEXT DEFAULT 'To Do',
            PY4E12 TEXT DEFAULT 'To Do',
            PY4E13 TEXT DEFAULT 'To Do',
            PY4E14 TEXT DEFAULT 'To Do',
            PY4E15 TEXT DEFAULT 'To Do',
            PY4E16 TEXT DEFAULT 'To Do',
            PY4E17 TEXT DEFAULT 'To Do',
            PY4E18 TEXT DEFAULT 'To Do',
            last_update TIMESTAMP
        )
    ''')
    db.commit()
    cur.close()

def ensure_datajobs_table_exists(db):
    """Ensure the datajobs table exists with proper schema."""
    cur = db.cursor()
    cur.execute('''
        CREATE TABLE IF NOT EXISTS datajobs (
            id INTEGER PRIMARY KEY,
            datePosted TEXT,
            jobTitle TEXT,
            jobCategory TEXT,
            workSetup TEXT,
            companyName TEXT,
            location TEXT,
            salaryRange TEXT,
            jobPostLink TEXT,
            applicationDeadline TEXT
        )
    ''')
    db.commit()
    cur.close()

def get_py4e_completion_counts(db):
    """Get completion counts for all PY4E lessons."""
    cur = db.cursor()
    py4e_columns = [f'PY4E{i}' for i in range(1, 12)]
    # py4e_columns = [f'PY4E{i}' for i in range(1, 19)]
    allowed_columns = {f'PY4E{i}' for i in range(1, 12)}
    # allowed_columns = {f'PY4E{i}' for i in range(1, 19)}
    py4e_done_counts = {}
    
    for column in py4e_columns:
        if column in allowed_columns:
            cur.execute(f'SELECT COUNT(*) FROM user WHERE {column} = ?', ("Done",))
            py4e_done_counts[column] = cur.fetchone()[0]
    
    cur.close()
    return py4e_done_counts

def generate_py4e_chart(py4e_counts, total_enrollments, save_path=None):
    """Generate and save PY4E progress chart."""
    try:
        fig, ax = plt.subplots(figsize=(12, 6))
        
        # Add title with total enrollments
        ax.set_title(f"Total Enrollments: {total_enrollments:,}", fontsize=14, pad=20)
        
        # Create bar chart
        bars = ax.bar(py4e_counts.keys(), py4e_counts.values(), color='#B6D0E2')
        
        # Configure chart appearance
        ax.set_xlabel('PY4E Lessons', fontsize=12)
        ax.set_ylabel('Number of Completions', fontsize=12)
        ax.grid(True, alpha=0.3)
        
        # Set x-axis labels
        lesson_labels = [f'PY4E{i}' for i in range(1, 12)]
        # lesson_labels = [f'PY4E{i}' for i in range(1, 19)]
        ax.set_xticks(range(len(lesson_labels)))
        ax.set_xticklabels(lesson_labels, fontsize=10)
        
        # Add value labels on bars
        for i, bar in enumerate(bars):
            height = bar.get_height()
            x_position = bar.get_x() + bar.get_width() / 2
            ax.text(x_position, height + 0.1, str(int(height)), 
                   ha='center', va='bottom', fontsize=9)
        
        # Save chart with absolute path
        if save_path is None:
            save_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'static', 'py4e_progress.png')
        
        plt.tight_layout()
        plt.savefig(save_path, dpi=300, bbox_inches='tight')
        plt.close()
        
        app.logger.info(f"Generated chart with {len(lesson_labels)} lesson labels, saved to {save_path}")
        return save_path
        
    except Exception as e:
        app.logger.error(f"Error generating chart: {str(e)}")
        return None

# Error handlers
@app.errorhandler(404)
def not_found_error(error):
    app.logger.error(f'404 error: {request.url}')
    return render_template('404.html'), 404

@app.errorhandler(500)
def internal_error(error):
    app.logger.error(f'500 error: {error}')
    return render_template('500.html'), 500

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        password = request.form.get('password', '')
        
        # Validate user input
        validation_errors = validate_user_credentials(username, password)
        if validation_errors:
            for error in validation_errors:
                flash(error, 'error')
            return render_template('signup.html')
        
        # Hash the password before storing
        password_hash = generate_password_hash(password)
        
        db = get_db()
        try:
            db.execute('INSERT INTO user (username, password) VALUES (?, ?)', (username, password_hash))
            db.commit()
            flash('Registration successful! Please log in.', 'success')
            return redirect(url_for('startyourjourney'))
        except sqlite3.IntegrityError:
            flash('Username already taken. Please choose a different username.', 'error')
            return render_template('signup.html')
    
    return render_template('signup.html')
    
@app.route('/logout')
def logout():
    session.pop('user', None)
    return redirect(url_for('index'))

@app.route('/datajobs/', methods=['GET'])
def datajobs():
    db = get_db(DATAJOBS_DATABASE)  # Use datajobs.db
    cur = db.cursor()

    # Create the user table if it doesn't exist
    cur.execute(
        "CREATE TABLE IF NOT EXISTS user (user_id INTEGER PRIMARY KEY, username TEXT, password TEXT, first_name TEXT, last_name TEXT)"
    )

    # Create the datajobs table if it doesn't exist
    cur.execute(
        "CREATE TABLE IF NOT EXISTS datajobs (id INTEGER PRIMARY KEY, datePosted TEXT, jobTitle TEXT, jobCategory TEXT, workSetup TEXT, companyName TEXT, location TEXT, salaryRange TEXT, jobPostLink TEXT, applicationDeadline TEXT)",
    )

    cur.execute("SELECT * FROM datajobs")
    datajobs = cur.fetchall()
    cur.close()

    return render_template('datajobs.html', datajobs=datajobs)

@app.route('/post_job', methods=['POST'])
def post_job():
    # Extract and validate form data
    form_data = {
        'datePosted': request.form.get('datePosted', '').strip(),
        'jobTitle': request.form.get('jobTitle', '').strip(),
        'jobCategory': request.form.get('jobCategory', '').strip(),
        'workSetup': request.form.get('workSetup', '').strip(),
        'companyName': request.form.get('companyName', '').strip(),
        'location': request.form.get('location', '').strip(),
        'salaryRange': request.form.get('salaryRange', '').strip(),
        'jobPostLink': request.form.get('jobPostLink', '').strip(),
        'applicationDeadline': request.form.get('applicationDeadline', '').strip()
    }
    
    # Validate job data
    validation_errors = validate_job_data(form_data)
    if validation_errors:
        for error in validation_errors:
            flash(error, 'error')
        return redirect(url_for('datajobs'))
    
    # Insert job data into database
    try:
        db = get_db(DATAJOBS_DATABASE)
        cur = db.cursor()
        
        # Create table if it doesn't exist
        cur.execute(
            "CREATE TABLE IF NOT EXISTS datajobs (id INTEGER PRIMARY KEY, datePosted TEXT, jobTitle TEXT, jobCategory TEXT, workSetup TEXT, companyName TEXT, location TEXT, salaryRange TEXT, jobPostLink TEXT, applicationDeadline TEXT)"
        )
        
        # Insert job data
        cur.execute(
            "INSERT INTO datajobs (datePosted, jobTitle, jobCategory, workSetup, companyName, location, salaryRange, jobPostLink, applicationDeadline) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)",
            (form_data['datePosted'], form_data['jobTitle'], form_data['jobCategory'], 
             form_data['workSetup'], form_data['companyName'], form_data['location'], 
             form_data['salaryRange'], form_data['jobPostLink'], form_data['applicationDeadline'])
        )
        db.commit()
        cur.close()
        
        flash('Job posted successfully!', 'success')
        
    except sqlite3.Error as e:
        flash(f'Database error: {str(e)}', 'error')
    
    return redirect(url_for('datajobs'))

@app.route('/check_login/', methods=['GET'])
def check_login():
    """Check if the user is logged in and redirect accordingly."""
    if 'username' in session:
        app.logger.info(f'User {session["username"]} accessed check_login - redirecting to datajobs')
        return redirect(url_for('datajobs'))  # Redirect to Data Jobs page
    else:
        app.logger.info('Unauthenticated user accessed check_login - redirecting to index')
        return redirect(url_for('index'))  # Redirect to homepage or login page

@app.route('/startyourjourney', methods=['GET', 'POST'])
def startyourjourney():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        
        db = get_db()
        cur = db.cursor()

        # Check if the username exists in the database
        try:
            cur.execute('SELECT * FROM user WHERE username = ?', (username,))
            user = cur.fetchone()
            cur.close()

            # Verify the password (handle both plain text and hashed passwords)
            if user and (user['password'] == password or check_password_hash(user['password'], password)):
                session['username'] = username  # Store user in session
                app.logger.info(f'Successful login for user: {username}')
                return redirect(url_for('dashboard'))  # Redirect to the dashboard page
            else:
                app.logger.warning(f'Failed login attempt for username: {username}')
                flash('Invalid credentials. Please try again.', 'error')
                return render_template('startyourjourney.html')
        except sqlite3.Error as e:
            app.logger.error(f'Database error during login: {str(e)}')
            flash('Database error occurred. Please try again later.', 'error')
            return render_template('startyourjourney.html')

    db = get_db()
    cur = db.cursor()

    # Fetch completion counts for each PY4E lesson
    py4e_columns = [f'PY4E{i}' for i in range(1, 12)]
    # py4e_columns = [f'PY4E{i}' for i in range(1, 19)]
    py4e_done_counts = {}

    # Safe approach: use allowed column names to prevent SQL injection
    allowed_columns = {f'PY4E{i}' for i in range(1, 12)}
    # allowed_columns = {f'PY4E{i}' for i in range(1, 19)}
    
    for column in py4e_columns:
        # Validate column name against allowed list
        if column in allowed_columns:
            cur.execute(f'SELECT COUNT(*) FROM user WHERE {column} = ?', ("Done",))
            py4e_done_counts[column] = cur.fetchone()[0]

    # Query to get the total number of enrollments
    cur.execute("SELECT COUNT(*) FROM user")
    total_enrollments = cur.fetchone()[0]  # Total number of users

    cur.close()

    # Plot the graph
    fig, ax = plt.subplots(figsize=(12, 6))

    # Add a title to the graph with total enrollments
    ax.set_title(f"Total Enrollments: {total_enrollments:,}", fontsize=14, pad=20)

    bars = ax.bar(py4e_done_counts.keys(), py4e_done_counts.values(), color='#B6D0E2')

    # Additional formatting for the bar chart
    ax.set_xlabel('PY4E Lessons', fontsize=12)
    ax.set_ylabel('Number of Completions', fontsize=12)
    ax.tick_params(axis='x', rotation=45)

    # Add labels on top of bars
    for bar in bars:
        height = bar.get_height()
        if height > 0:
            ax.text(bar.get_x() + bar.get_width()/2, height, str(height), ha='center', va='bottom', fontsize=10, color='blue')

    plt.tight_layout()

    # Save the plot with absolute path and error handling
    try:
        img_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'static', 'py4e_progress.png')
        plt.savefig(img_path, dpi=300, bbox_inches='tight')
        plt.close()
        app.logger.info(f"Chart saved successfully to {img_path}")
    except Exception as e:
        app.logger.error(f"Error saving chart: {str(e)}")
        plt.close()
        # Fallback: try using the generate_py4e_chart function
        generate_py4e_chart(py4e_done_counts, total_enrollments)

    return render_template('startyourjourney.html', graph_url=url_for('static', filename='py4e_progress.png'), total_enrollments=total_enrollments)

@app.route("/dashboard")
def dashboard():
    if "username" in session:
        username = session["username"]
        db = get_db()
        cur = db.cursor()
        
        # Query to get all user data
        cur.execute("SELECT * FROM user ORDER BY last_update DESC")
        users = cur.fetchall()

        # Initialize counts
        py4e_columns = [f'PY4E{i}' for i in range(1, 12)]
        # py4e_columns = [f'PY4E{i}' for i in range(1, 19)]
        py4e_done_counts = {}
        py4e_nickname_counts = {}

        total_done_count = 0  # Total number of 'Done' values
        google_form_count = 0  # Variable for Google Form count

        # Safe approach: use allowed column names to prevent SQL injection
        allowed_columns = {f'PY4E{i}' for i in range(1, 12)}
        # allowed_columns = {f'PY4E{i}' for i in range(1, 19)}
        
        # Query counts
        for column in py4e_columns:
            # Validate column name against allowed list
            if column in allowed_columns:
                cur.execute(f'SELECT COUNT(*) FROM user WHERE {column} = ?', ("Done",))
                done_count = cur.fetchone()[0]
                py4e_done_counts[column] = done_count
                total_done_count += done_count  # Total 'Done' count

                cur.execute(f'''
                    SELECT COUNT(*) FROM user
                    WHERE {column} = ? AND Nickname IS NOT NULL
                ''', ("Done",))
                nickname_count = cur.fetchone()[0]
                py4e_nickname_counts[column] = nickname_count

        # Count for Google Form registrations
        cur.execute('SELECT COUNT(*) FROM user WHERE Nickname IS NOT NULL')
        google_form_count = cur.fetchone()[0]

        # Query to get the status of the logged-in user
        cur.execute("SELECT PY4E1, PY4E2, PY4E3, PY4E4, PY4E5, PY4E6, PY4E7, PY4E8, PY4E9, PY4E10, PY4E11 FROM user WHERE username=?", (username,))
        # cur.execute("SELECT PY4E1, PY4E2, PY4E3, PY4E4, PY4E5, PY4E6, PY4E7, PY4E8, PY4E9, PY4E10, PY4E11, PY4E12, PY4E13, PY4E14, PY4E15, PY4E16, PY4E17, PY4E18 FROM user WHERE username=?", (username,))
        user_status = cur.fetchone()  # Fetch the status row for the logged-in user

        # Close the database connection
        cur.close()

        # Plot the graph
        fig, ax = plt.subplots(figsize=(12, 6))
        bars = ax.bar(py4e_done_counts.keys(), py4e_done_counts.values(), color='#B6D0E2')

        # Additional formatting for the bar chart
        ax.set_xlabel('PY4E Lessons', fontsize=12)
        ax.set_ylabel('Number of Completions', fontsize=12)
        ax.tick_params(axis='x', rotation=45)

        # Set x-axis labels directly to the lesson identifiers
        lesson_labels = [f'PY4E{i}' for i in range(1, 12)]
        # lesson_labels = [f'PY4E{i}' for i in range(1, 19)]
        ax.set_xticks(range(len(lesson_labels)))  # Set the x-ticks to the range of labels
        ax.set_xticklabels(lesson_labels, fontsize=10)  # Set explicit labels without counts

        # Log chart generation for debugging if needed
        app.logger.debug("Generated chart with %d lesson labels", len(lesson_labels))

        # Add labels on top of the bars without changing x-axis labels
        for i, bar in enumerate(bars):
            height = bar.get_height()
            x_position = bar.get_x() + bar.get_width() / 2

            # Add the "Done" count label in blue directly above each bar
            if height > 0:
                ax.text(x_position, height * 1.02, str(height), ha='center', va='bottom', fontsize=10, color='#2c63ab')

                # Add the nickname count indicator in purple just below the bar label
                nickname_count = py4e_nickname_counts.get(py4e_columns[i], 0)  # Use .get to avoid KeyErrors
                ax.text(x_position, height * 0.95, f'G: {nickname_count}', ha='center', va='top', fontsize=9, color='purple')
        
        # Set y-axis limits to ensure labels are visible
        ax.set_ylim(0, max(py4e_done_counts.values()) * 1.2)

        # Adjust layout to make space for the headers and avoid truncation
        plt.subplots_adjust(left=0.1, right=0.95, top=0.85, bottom=0.25)

        # Save the plot as an image with absolute path and error handling
        try:
            img_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'static', 'py4e_progress.png')
            plt.savefig(img_path, dpi=300, bbox_inches='tight')
            plt.close()
            app.logger.info(f"Dashboard chart saved successfully to {img_path}")
        except Exception as e:
            app.logger.error(f"Error saving dashboard chart: {str(e)}")
            plt.close()
            # Fallback: try using the generate_py4e_chart function  
            generate_py4e_chart(py4e_done_counts, total_enrollments)

        # Render the dashboard with the plot
        return render_template("dashboard.html", username=username, users=users, user_status=user_status, graph_url=url_for('static', filename='py4e_progress.png'))

    return redirect(url_for("startyourjourney")) 

@app.route("/update/<username>", methods=["GET", "POST"])
def update(username):
    if request.method == "POST":
        status_values = [
            request.form[f"status{i}"] for i in range(1, 12)
        ]  # Status values for PY4E1 to PY4E11
        # status_values = [
        #     request.form[f"status{i}"] for i in range(1, 19)
        # ]  # Status values for PY4E1 to PY4E18

        query = "UPDATE user SET "
        query += ", ".join([f"PY4E{i} = ?" for i in range(1, 12)])
        # query += ", ".join([f"PY4E{i} = ?" for i in range(1, 19)])
        query += ", last_update = ?"  # Add last_update column
        query += " WHERE username = ?"

        # Append current timestamp and username to status_values
        status_values.append(datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
        status_values.append(username)

        db = get_db()
        cur = db.cursor()
        cur.execute(query, status_values)
        db.commit()

        return redirect(url_for("dashboard"))
    else:
        with open(LESSONS_FILE) as fh:
            lessons = [line.rstrip() for line in fh.readlines()]

        db = get_db()
        cur = db.cursor()
        cur.execute("SELECT * FROM user WHERE username=?", (username,))
        user = cur.fetchone()
        return render_template(
            "update.html", username=username, user=user, lessons=lessons
        )

@app.route('/deptalents')
def deptalents():
    return render_template('deptalents.html')

@app.route('/datadeepdive')
def datadeepdive():
    # Fetch data from datajobs database
    db = get_db(DATAJOBS_DATABASE)
    cur = db.cursor()
    
    # Create the datajobs table if it doesn't exist
    cur.execute(
        "CREATE TABLE IF NOT EXISTS datajobs (id INTEGER PRIMARY KEY, datePosted TEXT, jobTitle TEXT, jobCategory TEXT, workSetup TEXT, companyName TEXT, location TEXT, salaryRange TEXT, jobPostLink TEXT, applicationDeadline TEXT)",
    )
    
    cur.execute("SELECT * FROM datajobs")
    datajobs = cur.fetchall()
    cur.close()
    
    return render_template('datadeepdive.html', datajobs=datajobs)


@app.route('/datamasters')
def datamasters():
    return render_template('datamasters.html')

@app.route('/mentors')
def mentors():
    return render_template('mentors.html')

@app.route('/blogs')
def blogs():
    return render_template('blogs.html')

@app.route('/sandbox')
def sandbox():
    return render_template('sandbox.html')

@app.route('/aboutdep')
def aboutdep():
    return render_template('aboutdep.html')

@app.route('/contact')
def contact():
    return render_template('contact.html')

@app.route('/barangaydep')
def barangaydep():
    return render_template('barangaydep.html')

@app.route('/developers')
def developers():
    return render_template('developers.html')

if __name__ == '__main__':
    #init_db()
    app.run(debug=True, port=5002)