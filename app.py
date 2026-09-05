from flask import Flask, render_template, request, redirect, session, flash, abort
from werkzeug.security import generate_password_hash, check_password_hash
import sqlite3
import os

app = Flask(__name__)
app.secret_key = os.urandom(24)

# Defining the routes for the web app
@app.route('/')
def root():
    return render_template('index.html')

@app.route('/login')
def login_page():
    return render_template('login.html')

@app.route('/signup')
def signup_page():
    return render_template('signup.html')

@app.route('/signup', methods=["POST"])
def signup():
    # request.form gets the values from the signup form
    name = request.form['name']
    email = request.form['email']
    pwd = request.form['pwd2']
    # Hash the password before saving it so the database doesnt have them in plain text
    hashed_pwd = generate_password_hash(pwd)

    conn = sqlite3.connect('app.db')
    cursor = conn.cursor()

    # Insert the new user's name, email, and hashed password into the users table.
    cursor.execute(
        'INSERT INTO users (user_name, user_email, user_pwd) VALUES (?, ?, ?)',
        (name, email, hashed_pwd)
    )

    conn.commit()
    conn.close()

    flash('Account created', 'success')
    return redirect('/login')

@app.route('/logon', methods=["POST"])
def logon():
    # Get the email and password from the login form
    email = request.form['email']
    pwd = request.form['pwd']

    conn = sqlite3.connect('app.db')
    cursor = conn.cursor()

    # Find the password hash and user ID belonging to the submitted email address
    cursor.execute('SELECT user_pwd, user_id FROM users WHERE user_email = ?', (email,))
    result = cursor.fetchone()
    conn.close()

    # Check if the hashed password in the database is the same as the password that the user entered
    if result:
        stored_password, user_id = result[0], result[1]
        if check_password_hash(stored_password, pwd):
            session['user_id'] = user_id
            session['user_email'] = email
            flash('Logged in successfully', 'success')
            return redirect('/')
        
        else:
            error = "Incorrect Password!"

    else:
        error = 'User Does Not Exist!'

    return render_template('login.html', error=error)

@app.route('/logout')
def logout():
    session.clear()
    flash('Logged out', 'success')
    return redirect('/')

@app.route('/list-job')
def list_job():
    # Check the session before displaying the form for creating a new job listing.
    if 'user_email' not in session:
        return redirect('/login')

    return render_template('list-job.html')

@app.route('/jobs')
def jobs():
    conn = sqlite3.connect('app.db')
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    # Select active jobs and join each one to the user who created it
    query = '''
        SELECT jobs.*, users.user_name, users.user_email 
        FROM jobs 
        JOIN users ON jobs.user_id = users.user_id 
        WHERE jobs.completed = "no"
    '''

    # Join each job to its owner, then filter out jobs that have already been completed.
    jobs = cursor.execute(query).fetchall()
    

    conn.close()

    return render_template('jobs.html', jobs=jobs)

@app.route('/list', methods=['POST'])
def list():
    # Get the new jobs details from the job listing form
    title = request.form['job-title']
    desc = request.form['job-desc']
    location = request.form['job-location']
    pay = request.form['job-pay']
    # Save the submitted listing to the database with the status set to no
    completed = 'no'
    user_id = session['user_id']

    conn = sqlite3.connect('app.db')
    cursor = conn.cursor()

    cursor.execute(
        'INSERT INTO jobs (user_id, job_desc, job_title, job_location, pay, completed) VALUES (?, ?, ?, ?, ?, ?)',
        (user_id, desc, title, location, pay, completed)
    )

    conn.commit()
    conn.close()

    flash('Job has been listed', 'success')
    return redirect('/')

@app.route('/job/<int:job_id>')
def job_details(job_id):
    if 'user_email' not in session:
        return redirect('/login')

    conn = sqlite3.connect('app.db')
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    # Find the requested job by its ID so its details can be displayed.
    job = cursor.execute('SELECT * FROM jobs WHERE job_id = ?', (job_id,)).fetchone()
    conn.close()

    if job is None:
        abort(404)

    return render_template('job_details.html', job=job)


@app.route('/inquire', methods=["POST"])
def inquire():
    # Get the applicant's contact details and the IDs for the job
    phone = request.form['number']
    why = request.form['reason']
    time = request.form['date']
    lister_id = request.form['lister_id']
    job_id = request.form['job_id']
    user_id = session['user_id']
    # Save the applicant's contact details and reason
    status = 'pending'

    conn = sqlite3.connect('app.db')
    cursor = conn.cursor()

    # Insert the new inquiry and connect it to the applicant, job, and job owner
    cursor.execute(
        'INSERT INTO inquiries (status, lister_id, job_id, user_id, phone, why, time) VALUES (?, ?, ?, ?, ?, ?, ?)',
        (status, lister_id, job_id, user_id, phone, why, time)
    )

    conn.commit()
    conn.close()

    flash('Inquiry Sent', 'success')
    return redirect('/')

@app.route('/inquiries')
def inquiries():
    if 'user_email' not in session:
        return redirect('/login')

    # session stores the ID of the currently signed-in user
    user_id = session['user_id']

    conn = sqlite3.connect('app.db')
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    # Get the signed-in user's inquiries, including the job and job-owner details.
    my_inquiries = cursor.execute('''
            SELECT 
                inquiries.*, 
                jobs.job_title, 
                jobs.job_desc,
                jobs.pay, 
                jobs.job_location,
                users.user_name AS lister_name,
                users.user_email AS lister_email
            FROM inquiries
            JOIN jobs ON inquiries.job_id = jobs.job_id
            JOIN users ON inquiries.lister_id = users.user_id
            WHERE inquiries.user_id = ? AND inquiries.dismissed = 'no'
        ''', (user_id,)).fetchall()

    # Get pending inquiries for the user's jobs, including each applicant's details.
    pending_inquiries = cursor.execute('''
        SELECT 
            inquiries.*, 
            jobs.job_title, 
            jobs.job_desc,
            jobs.pay, 
            jobs.job_location,
            applicant.user_name AS applicant_name,
            applicant.user_email AS applicant_email,
            lister.user_name AS lister_name,
            lister.user_email AS lister_email
        FROM inquiries
        JOIN jobs ON inquiries.job_id = jobs.job_id
        JOIN users AS applicant ON inquiries.user_id = applicant.user_id
        JOIN users AS lister ON inquiries.lister_id = lister.user_id
        WHERE inquiries.lister_id = ? AND inquiries.status = 'pending'
    ''', (user_id,)).fetchall()

    conn.close()

    return render_template('inquiries.html', my_inquiries=my_inquiries, pending_inquiries=pending_inquiries)

@app.route('/accept-inquiry/<int:inquiry_id>')
def accept(inquiry_id):
    inquiry_status = 'accepted'

    conn = sqlite3.connect('app.db')
    cursor = conn.cursor()

    # Find the job connected to the inquiry before changing any statuses
    cursor.execute('SELECT job_id FROM inquiries WHERE inquiry_id = ?', (inquiry_id,))
    result = cursor.fetchone()

    if result is None:
        conn.close()
        abort(404)

    job_id = result[0]

    # Mark the selected inquiry accepted, close its job, and decline other applicants
    cursor.execute('UPDATE inquiries SET status = ? WHERE inquiry_id = ?', (inquiry_status, inquiry_id,))
    # Mark the related job as completed so it no longer appears as available
    cursor.execute('UPDATE jobs SET completed = ? WHERE job_id = ?', ('yes', job_id,))
    # Decline all other pending inquiries for the same job
    cursor.execute("UPDATE inquiries SET status = 'declined' WHERE job_id = ? AND inquiry_id != ? AND status = 'pending'", (job_id, inquiry_id,))

    conn.commit()
    conn.close()

    flash('Inquiry accepted, contact the applicant via their phone number or email which is on the inquiry, which can be found on the past jobs page.', 'success')
    return redirect('/past-jobs')


@app.route('/decline-inquiry/<int:inquiry_id>')
def decline(inquiry_id):
    inquiry_status = 'declined'

    conn = sqlite3.connect('app.db')
    cursor = conn.cursor()

    # Change the selected inquiry from pending to declined
    cursor.execute('UPDATE inquiries SET status = ? WHERE inquiry_id = ?', (inquiry_status, inquiry_id,))

    conn.commit()
    conn.close()

    flash('Inquiry declined', 'success')
    return redirect('/inquiries')


@app.route('/past-jobs')
def past_jobs():
    if 'user_email' not in session:
        return redirect('/login')

    # Use the signed-in user's ID to find their applications and completed listings
    user_id = session['user_id']

    conn = sqlite3.connect('app.db')
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    # List applications made by the user that were accepted or declined
    my_completed_jobs = cursor.execute('''
    SELECT
        inquiries.inquiry_id,
        inquiries.status,
        inquiries.phone,
        inquiries.why,
        inquiries.time,

        jobs.job_id,
        jobs.job_title,
        jobs.job_desc,
        jobs.job_location,
        jobs.pay,

        lister.user_id AS lister_id,
        lister.user_name AS lister_name,
        lister.user_email AS lister_email

    FROM inquiries

    JOIN jobs
        ON inquiries.job_id = jobs.job_id

    JOIN users AS lister
        ON jobs.user_id = lister.user_id

    WHERE inquiries.user_id = ?
    AND inquiries.status IN ('accepted', 'declined')

    ''', (user_id,)).fetchall()

    # List the user's completed jobs and include the applicant from the accepted inquiry
    my_listed_jobs = cursor.execute('''
        SELECT
            jobs.job_id,
            jobs.job_title,
            jobs.job_desc,
            jobs.job_location,
            jobs.pay,
            jobs.completed,

            inquiries.inquiry_id,
            inquiries.status,
            inquiries.phone,
            inquiries.why,
            inquiries.time,

            applicant.user_id AS applicant_id,
            applicant.user_name AS applicant_name,
            applicant.user_email AS applicant_email,

            lister.user_name AS lister_name,
            lister.user_email AS lister_email

        FROM jobs

        LEFT JOIN inquiries
            ON jobs.job_id = inquiries.job_id
            AND inquiries.status = 'accepted'

        LEFT JOIN users AS applicant
            ON inquiries.user_id = applicant.user_id

        JOIN users AS lister
            ON jobs.user_id = lister.user_id

        WHERE jobs.user_id = ?
        AND jobs.completed = 'yes'

        ''', (user_id,)).fetchall()

    return render_template('past-jobs.html', my_jobs=my_completed_jobs, my_listed=my_listed_jobs)


@app.route('/ok-pressed/<int:inquiry_id>')
def ok(inquiry_id):
    if 'user_email' not in session:
        return redirect('/login')

    user_id = session['user_id']

    conn = sqlite3.connect('app.db')
    cursor = conn.cursor()

    # Hide this finished inquiry from the applicant's list without deleting its record
    cursor.execute("UPDATE inquiries SET dismissed = 'yes' WHERE inquiry_id = ? AND user_id = ? AND status IN ('accepted', 'declined')", (inquiry_id, user_id,))

    conn.commit()
    conn.close()

    return redirect('/past-jobs')


if __name__ == '__main__':
    app.run(debug=True, host='127.0.0.1', port=5000)

