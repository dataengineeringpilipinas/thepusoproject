import sqlite3
from datetime import datetime
from flask import Flask, redirect, render_template, request, session, url_for, g
from flask_bootstrap import Bootstrap
import matplotlib.pyplot as plt
import matplotlib
matplotlib.use('Agg')
import os

app = Flask(__name__)
app.secret_key = 'your_secret_key'

# Database configuration
#DATABASE = '/home/engramar/thepusoproject/citizendevs.db'
DATABASE = './citizendevs.db'

def get_db():
    """Open a new database connection if there is none yet for the current application context."""
    if 'db' not in g:
        g.db = sqlite3.connect(DATABASE, check_same_thread=False)
        g.db.row_factory = sqlite3.Row  # Allows access by column name
    return g.db

@app.teardown_appcontext
def close_connection(exception):
    """Close the database connection at the end of the request."""
    db = g.pop('db', None)
    if db is not None:
        db.close()

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
            db.execute('INSERT INTO user (username, password) VALUES (?, ?)', (username, password))
            db.commit()
            return redirect(url_for('startyourjourney'))
        except sqlite3.IntegrityError:
            return 'Username already taken. <a href="/signup">Try again</a>'
    
    return render_template('signup.html')
    
@app.route('/logout')
def logout():
    session.pop('user', None)
    return redirect(url_for('index'))

# New Routes for Menu Pages
@app.route('/datajobs')
def datajobs():
    return render_template('datajobs.html')

@app.route('/startyourjourney', methods=['GET', 'POST'])
def startyourjourney():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        
        db = get_db()
        cur = db.cursor()

        # Check if the username and password match in the database
        cur.execute('SELECT * FROM user WHERE username = ? AND password = ?', (username, password))
        user = cur.fetchone()
        cur.close()

        if user:
            session['username'] = username  # Store user in session
            return redirect(url_for('dashboard'))  # Redirect to the dashboard page
        else:
            return 'Invalid credentials. <a href="/startyourjourney">Try again</a>'

    db = get_db()
    cur = db.cursor()

    # Fetch completion counts for each PY4E lesson
    py4e_columns = [f'PY4E{i}' for i in range(1, 18)]
    py4e_done_counts = {}

    for column in py4e_columns:
        cur.execute(f'SELECT COUNT(*) FROM user WHERE {column} = "Done"')
        py4e_done_counts[column] = cur.fetchone()[0]

    # Query to get the total number of enrollments
    cur.execute("SELECT COUNT(*) FROM user")
    total_enrollments = cur.fetchone()[0]  # Total number of users

    cur.close()

    # Plot the graph
    fig, ax = plt.subplots(figsize=(12, 6))

    # Add a title to the graph with total enrollments
    ax.set_title(f"Total Enrollments: {total_enrollments}", fontsize=14, pad=20)

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

    # Save the plot
    img_path = os.path.join('static', 'py4e_progress.png')
    plt.savefig(img_path)
    plt.close()

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
        py4e_columns = [f'PY4E{i}' for i in range(1, 18)]
        py4e_done_counts = {}
        py4e_nickname_counts = {}

        total_done_count = 0  # Total number of 'Done' values
        google_form_count = 0  # Variable for Google Form count

        # Query counts
        for column in py4e_columns:
            cur.execute(f'SELECT COUNT(*) FROM user WHERE {column} = "Done"')
            done_count = cur.fetchone()[0]
            py4e_done_counts[column] = done_count
            total_done_count += done_count  # Total 'Done' count

            cur.execute(f'''
                SELECT COUNT(*) FROM user
                WHERE {column} = "Done" AND Nickname IS NOT NULL
            ''')
            nickname_count = cur.fetchone()[0]
            py4e_nickname_counts[column] = nickname_count

        # Count for Google Form registrations
        cur.execute('SELECT COUNT(*) FROM user WHERE Nickname IS NOT NULL')
        google_form_count = cur.fetchone()[0]

        # Query to get the status of the logged-in user
        cur.execute("SELECT PY4E1, PY4E2, PY4E3, PY4E4, PY4E5, PY4E6, PY4E7, PY4E8, PY4E9, PY4E10, PY4E11, PY4E12, PY4E13, PY4E14, PY4E15, PY4E16, PY4E17 FROM user WHERE username=?", (username,))
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
        lesson_labels = [f'PY4E{i}' for i in range(1, 18)]
        ax.set_xticks(range(len(lesson_labels)))  # Set the x-ticks to the range of labels
        ax.set_xticklabels(lesson_labels, fontsize=10)  # Set explicit labels without counts

        # Debugging prints to check x-tick labels
        print("X-axis labels:", lesson_labels)

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

        # Save the plot as an image        
        #img_path = os.path.join('/home/engramar/thepusoproject/static', 'py4e_progress.png')        
        img_path = os.path.join('static', 'py4e_progress.png')
        plt.savefig(img_path)
        plt.close()

        # Render the dashboard with the plot
        return render_template("dashboard.html", username=username, users=users, user_status=user_status, graph_url=url_for('static', filename='py4e_progress.png'))

    return redirect(url_for("startyourjourney")) 

@app.route("/update/<username>", methods=["GET", "POST"])
def update(username):
    if request.method == "POST":
        status_values = [
            request.form[f"status{i}"] for i in range(1, 18)
        ]  # Status values for PY4E1 to PY4E17

        query = "UPDATE user SET "
        query += ", ".join([f"PY4E{i} = ?" for i in range(1, 18)])
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
        #fn = "/home/engramar/thepusoproject/lessons.txt"
        fn = "./lessons.txt"
        with open(fn) as fh:
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

@app.route('/sandbox')
def sandbox():
    return render_template('sandbox.html')

@app.route('/aboutdep')
def aboutdep():
    return render_template('aboutdep.html')

@app.route('/contact')
def contact():
    return render_template('contact.html')

if __name__ == '__main__':
    #init_db()
    app.run(debug=True)