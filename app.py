from flask import Flask, render_template, request, redirect, url_for, session,flash
import pyodbc

app = Flask(__name__)
app.secret_key = 'your_secret_key'

# Connect to SQL Server database
server = 'SHAFAFTVEDC-SRV'
database = 'refah'
username = 'pyrefah'
password = 'Aa@1234'
driver = '{ODBC Driver 17 for SQL Server}'  # Adjust the driver name if needed

conn = pyodbc.connect('DRIVER=' + driver + ';SERVER=' + server +';PORT=1433;DATABASE=' + database +';UID=' + username + ';PWD=' + password)
cursor = conn.cursor()

@app.route('/')
def index():
    if 'username' in session:
        username = session['username']
        cursor.execute("SELECT role FROM users WHERE username=?", (username,))
        user = cursor.fetchone()
        if user:
            role = user[0]
            if role == 'admin':
                return redirect(url_for('admin'))
            elif role == 'user':
                return redirect(url_for('qpage'))
    return render_template('login.html')

@app.route('/login', methods=['POST'])
def login():
    username = request.form['username']
    password = request.form['password']
    cursor.execute("SELECT role FROM users WHERE username=? AND password=?", (username, password))
    user = cursor.fetchone()
    if user:
        session['username'] = username
        role = user[0]
        if role == 'admin':
            return redirect(url_for('admin'))
        elif role == 'user':
            return redirect(url_for('qpage'))
    return 'Invalid username or password'

@app.route('/admin')
def admin():
    if 'username' in session:
        # Fetch subjects and questions from the database
        cursor.execute("SELECT * FROM subjects")
        subjects = cursor.fetchall()
        cursor.execute("SELECT * FROM questions")
        questions = cursor.fetchall()
        return render_template('admin.html', subjects=subjects, questions=questions)
    else:
        return redirect(url_for('index'))


@app.route('/qpage')
def qpage():
    if 'username' in session:
        return render_template('qpage.html')
    else:
        return redirect(url_for('index'))

@app.route('/logout', methods=['GET'])
def logout():
    session.pop('username', None)
    return redirect(url_for('index'))



@app.route('/admin/subjects/add', methods=['POST'])
def add_subject():
    if request.method == 'POST':
        # Retrieve subject name from the form
        subject_name = request.form.get('subject_name')

        # Check if the subject name is not empty
        if subject_name:
            try:
                # Insert the new subject into the database
                cursor.execute("INSERT INTO subjects (name, status) VALUES (?, ?)", (subject_name, 1))
                conn.commit()
                flash('Subject added successfully!', 'success')
            except pyodbc.Error as e:
                conn.rollback()
                flash(f'Failed to add subject: {str(e)}', 'danger')
        else:
            flash('Subject name cannot be empty!', 'danger')

        # Redirect back to the admin panel
        return redirect(url_for('admin'))
    else:
        # If the request method is not POST, redirect to the admin panel
        return redirect(url_for('admin'))



@app.route('/remove_subject/<int:subject_id>', methods=['POST'])
def remove_subject(subject_id):
    if 'username' in session:
        # Check if the user is an admin (optional)
        cursor.execute("SELECT role FROM users WHERE username=?", (session['username'],))
        user = cursor.fetchone()
        if user and user[0] == 'admin':
            # Perform the removal of the subject
            cursor.execute("DELETE FROM subjects WHERE id=?", (subject_id,))
            conn.commit()
            # Redirect back to the admin page
            return redirect(url_for('admin'))
    # Redirect to the login page if not logged in or not an admin
    return redirect(url_for('index'))

@app.route('/admin/subjects/update_status', methods=['POST'])
def update_subject_status():
    # Retrieve form data
    subject_id = request.form.get('subject_id')
    new_status = request.form.get('new_status')

    # Update the status of the subject in the database
    cursor.execute("UPDATE subjects SET status = ? WHERE id = ?", (new_status, subject_id))
    conn.commit()

    # Redirect back to the admin page
    return redirect(url_for('admin'))


@app.route('/admin/subjects/update_name', methods=['POST'])
def update_subject_name():
    # Retrieve form data
    subject_id = request.form.get('subject_id')  # Fix the typo here
    new_name = request.form.get('new_name')

    # Update the name of the subject in the database
    cursor.execute("UPDATE subjects SET name = ? WHERE id = ?", (new_name, subject_id))
    conn.commit()

    # Redirect back to the admin page
    return redirect(url_for('admin'))



@app.route('/admin/subjects/add_question', methods=['POST'])
def add_question():
    # Retrieve form data
    subject_id = request.form.get('subject_id')
    question_text = request.form.get('question')
    answer_type = request.form.get('answer_type')
    options = request.form.getlist('select_options[]')  # Retrieve the array of options

    try:
        # Insert the question into the database
        cursor.execute("INSERT INTO questions (subject_id, text, answer_type) OUTPUT INSERTED.id VALUES (?, ?, ?)",
                       (subject_id, question_text, answer_type))
        question_id = cursor.fetchone()[0]  # Fetch the last inserted question ID
        conn.commit()

        # Insert each option into the question_options table
        for option in options:
            cursor.execute("INSERT INTO question_options (question_id, option_text) VALUES (?, ?)",
                           (question_id, option))
        conn.commit()

        flash('Question added successfully!', 'success')
    except Exception as e:
        conn.rollback()
        flash('Failed to add question. Please try again.', 'error')
        print(e)  # Print the error for debugging

    # Redirect back to the admin page
    return redirect(url_for('admin'))





if __name__ == '__main__':
    app.run(debug=True)
