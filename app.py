from flask import Flask, g, render_template, request, jsonify, session, redirect, url_for
from datetime import datetime, timedelta
import sqlite3



app = Flask(__name__)
app.secret_key = 'super_secret_key'


DATABASE = 'todo_list.db'
user_id = 1  # This should be dynamically set based on the logged-in user
fake_date = "2025-08-20"

def get_db():
    db = getattr(g, '_database', None)
    if db is None:
        db = g._database = sqlite3.connect(DATABASE)
        db.row_factory = sqlite3.Row # This allows us to access columns by name
    return db

@app.teardown_appcontext
def close_connection(exception):
    db = getattr(g, '_database', None)
    if db is not None:
        db.close()

def query_db(query, args=(), one=False):
    cur = get_db().execute(query, args)
    rv = cur.fetchall()
    cur.close()
    return (rv[0] if rv else None) if one else rv


@app.route('/')          #later change to login page
def runJS():
    return render_template('run_JS.html')


@app.route('/receive_time', methods=['POST'])
def receive_time():
    data = request.get_json()
    local_time = data.get('local_time')
    timezone_offset = data.get('timezone_offset')
    try:
        user_time = datetime.fromisoformat(local_time.replace('Z', '+00:00'))
        user_time_corrected = user_time - timedelta(minutes=timezone_offset)
        # Format as 'YYYY-MM-DD'
        user_local_date = user_time_corrected.strftime('%Y-%m-%d')
        # Format as 'YYYY-MM-DD HH:MM:SS'
        user_local_datetime = user_time_corrected.strftime('%Y-%m-%d %H:%M:%S')
        # Format as 'Mon DD ‧ Day' for display
        user_local_fancy = user_time_corrected.strftime('%b %d-%A')
        # Save in session
        session['user_local_date'] = user_local_date
        session['user_local_datetime'] = user_local_datetime
        session['user_local_fancy'] = user_local_fancy
    except Exception as e:
        return jsonify({'error': 'Invalid date format sent from client.'}), 400
    return jsonify({'status': 'success'})


@app.route("/home")
def home():
    user_local_date = session.get('user_local_date')
    user_local_datetime = session.get('user_local_datetime')
    if not user_local_date or not user_local_datetime:
        return redirect(url_for('runJS'))  # Ensure we have the local date and datetime

    today_tasks_sql = """ 
                          SELECT *
                          FROM Tasks
                          WHERE date(start_time) = ?
                          AND Tasks.user_id=?
                          ORDER by start_time ASC;
                      """
    today_tasks_results = query_db(today_tasks_sql, [user_local_date, user_id])

    upcoming_tasks_sql = """
                            SELECT *
                            FROM Tasks
                            WHERE date(start_time) BETWEEN Date(?, '+1 days') AND Date(?, '+7 days')
                            AND user_id=?
                            ORDER by start_time ASC;
                         """
    upcoming_tasks_results = query_db(upcoming_tasks_sql, [user_local_date,user_local_date,user_id])
    
    # this sql needs user DATETIME and user id
        # replace '2024-02-07 00:00:00' with user DATETIME
        # replace user_id=1 with user_id='user id' 
    ongoing_tasks_sql = """SELECT *
                           FROM tasks
                           WHERE (start_time < ?
                           AND (finish_time > ?
                           OR finish_time IS NULL))
                           AND completed = 0
                           AND user_id = ?
                           ORDER BY finish_time DESC;
                        """
    ongoing_tasks_results = query_db(ongoing_tasks_sql, [user_local_datetime,user_local_datetime,user_id])

    goals_sql = """
                    SELECT *
                    FROM Goals
                    WHERE completed = 0
                    AND user_id = ?
                    ORDER BY importance desc;
                """
    goal_results = query_db(goals_sql, [user_id])

    results = {
        'Today_tasks' : today_tasks_results,
        'Upcoming_tasks' : upcoming_tasks_results,
        'Ongoing_tasks' : ongoing_tasks_results,
        'Goals' : goal_results
    }
    return render_template('home.html', results=results, user_local_date=user_local_date, user_local_datetime=user_local_datetime)


@app.route("/today")
def today():
    user_local_date = session.get('user_local_date')
    user_local_datetime = session.get('user_local_datetime')
    if not user_local_date or not user_local_datetime:
        return redirect(url_for('runJS'))

    today_tasks_sql = """ 
                          SELECT *
                          FROM Tasks
                          WHERE date(start_time) = ?
                          AND Tasks.user_id=?
                          ORDER by start_time ASC;
                      """
    today_tasks_results = query_db(today_tasks_sql, [user_local_date, user_id])

    results = {
        'Today_tasks' : today_tasks_results
    }

    return render_template('today.html', results=results, user_local_date=user_local_date, user_local_datetime=user_local_datetime)

@app.route("/upcoming")
def upcoming():
    user_local_fancy = session.get('user_local_fancy')
    user_local_date = session.get('user_local_date')
    user_local_datetime = session.get('user_local_datetime')
    if not user_local_date or not user_local_datetime or not user_local_fancy:
        return redirect(url_for('runJS'))  # Ensure we have the local date and datetime

    upcoming_tasks_sql = """
                            SELECT *
                            FROM Tasks
                            WHERE date(start_time) BETWEEN Date(?, '+1 days') AND Date(?, '+7 days')
                            AND user_id=?
                            ORDER by start_time ASC;
                         """
    upcoming_tasks_results = query_db(upcoming_tasks_sql, [user_local_date,user_local_date,user_id])
    results = {
        'Upcoming_tasks' : upcoming_tasks_results
    }

    # Use user_local_date (with year) for correct week calculation
    user_date = datetime.strptime(user_local_date, '%Y-%m-%d')
    monday = user_date - timedelta(days=user_date.weekday())
    next_7_days = []
    for i in range(7):
        day = monday + timedelta(days=i)
        if day.date() == user_date.date():
            next_7_days.append(day.strftime('%b %d-') + 'Today')
        elif day.date() == (user_date + timedelta(days=1)).date():
            next_7_days.append(day.strftime('%b %d-') + 'Tomorrow')
        else:
            next_7_days.append(day.strftime('%b %d-%A'))

    return render_template('upcoming.html', results=results, user_local_date=user_local_date, user_local_datetime=user_local_datetime, user_local_fancy=user_local_fancy, next_7_days=next_7_days)




if __name__=="__main__":
    app.run(debug=True)