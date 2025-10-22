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
                          AND completed = 0
                          AND Tasks.user_id=?
                          ORDER by start_time ASC;
                      """
    today_tasks_results = query_db(today_tasks_sql, [user_local_date, user_id])

    upcoming_tasks_sql = """
                            SELECT *
                            FROM Tasks
                            WHERE date(start_time) BETWEEN Date(?, '+1 days') AND Date(?, '+7 days')
                            AND user_id=?
                            AND completed = 0
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
                          AND completed = 0
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
                            WHERE date(start_time) BETWEEN Date(?, '-7 days') AND Date(?, '+7 days')
                            AND user_id=?
                            AND completed = 0
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
            next_7_days.append((day.strftime('%b %d-') + 'Today', day.strftime('%Y-%m-%d')))
        elif day.date() == (user_date + timedelta(days=1)).date():
            next_7_days.append((day.strftime('%b %d-') + 'Tomorrow', day.strftime('%Y-%m-%d')))
        else:
            next_7_days.append((day.strftime('%b %d-%A'), day.strftime('%Y-%m-%d')))

    return render_template('upcoming.html', results=results, user_local_date=user_local_date, user_local_datetime=user_local_datetime, user_local_fancy=user_local_fancy, next_7_days=next_7_days)


@app.route("/ongoing")
def ongoing():
    user_local_date = session.get('user_local_date')
    user_local_datetime = session.get('user_local_datetime')
    if not user_local_date or not user_local_datetime:
        return redirect(url_for('runJS'))
    
    ongoing_tasks_sql = """
                            SELECT *
                            FROM tasks
                            WHERE start_time < ?
                            AND completed = 0
                            AND user_id = ?
                            ORDER BY finish_time DESC;
                        """
    ongoing_tasks_results = query_db(ongoing_tasks_sql, [user_local_datetime,user_id])
    results = {
        'Ongoing_tasks' : ongoing_tasks_results
    }

    user_date = datetime.strptime(user_local_date, '%Y-%m-%d')
    monday = user_date - timedelta(days=user_date.weekday())
    week_days = []
    for i in range(7):
        day = monday + timedelta(days=i)
        if day.date() == user_date.date():
            week_days.append((day.strftime('%b %d-') + 'Today', day.strftime('%Y-%m-%d')))
        elif day.date() == (user_date + timedelta(days=1)).date():
            week_days.append((day.strftime('%b %d-') + 'Tomorrow', day.strftime('%Y-%m-%d')))
        else:
            week_days.append((day.strftime('%b %d-%A'), day.strftime('%Y-%m-%d')))

    return render_template('ongoing.html', results=results, fake_date=fake_date, user_local_date=user_local_date, user_local_datetime=user_local_datetime, week_days=week_days)


@app.route("/goals")
def goals():
    user_local_date = session.get('user_local_date')
    user_local_datetime = session.get('user_local_datetime')
    if not user_local_date or not user_local_datetime:
        return redirect(url_for('runJS'))

    goals_sql = """
                    SELECT *
                    FROM Goals
                    WHERE completed = 0
                    AND user_id = ?
                    ORDER BY importance desc;
                """
    goal_results = query_db(goals_sql, [user_id])
    results = {
        'Goals' : goal_results
    }
    return render_template('goals.html', results=results, user_local_date=user_local_date, user_local_datetime=user_local_datetime)


@app.route("/completed_tasks")
def completed_tasks():
    user_local_date = session.get('user_local_date')
    user_local_datetime = session.get('user_local_datetime')
    if not user_local_date or not user_local_datetime:
        return redirect(url_for('runJS'))
    
    completed_tasks_sql = """
                            SELECT *
                            FROM Tasks
                            WHERE user_id = ?
                            AND completed = 1
                            ORDER BY finish_time DESC;
                          """
    compepted_tasks_results = query_db(completed_tasks_sql, [user_id])

    results = {
        'Completed_tasks' : compepted_tasks_results,
    }

    return render_template('completed_tasks.html', results=results, user_local_date=user_local_date, user_local_datetime=user_local_datetime)

@app.route("/completed_goals")
def completed_goals():
    user_local_date = session.get('user_local_date')
    user_local_datetime = session.get('user_local_datetime')
    if not user_local_date or not user_local_datetime:
        return redirect(url_for('runJS'))
    
    completed_goals_sql = """
                            SELECT *
                            FROM Goals
                            WHERE user_id = ?
                            AND completed = 1
                            ORDER BY finish_time DESC;
                          """
    completed_goals_results = query_db(completed_goals_sql, [user_id])

    results = {
        'Completed_goals' : completed_goals_results,
    }

    return render_template('completed_goals.html', results=results, user_local_date=user_local_date, user_local_datetime=user_local_datetime)

# Route for testing dynamic tasks like the Tests example
@app.route('/test_tasks')
def test_tasks():
    db = get_db()
    tasks = query_db('SELECT * FROM Tasks WHERE user_id=? AND completed=0 ORDER BY task_id DESC', [user_id])
    return render_template('test_tasks.html', tasks=tasks)

@app.route('/test_add_task', methods=['POST'])
def test_add_task():
    data = request.get_json()
    title = data.get('title')
    description = data.get('description', '')
    start_time = data.get('start_time')
    all_day = int(data.get('all_day', 0))

    if not title: return jsonify({"error": "Title is required"}), 400
    if not start_time: return jsonify({"error": "Start time is required"}), 400

    try:
        if all_day:
            # Only date is allowed
            start_time_formatted = datetime.fromisoformat(start_time).strftime('%Y-%m-%d')
        else:
            # Full datetime
            start_time_formatted = datetime.fromisoformat(start_time).strftime('%Y-%m-%d %H:%M:%S')
    except Exception:
        return jsonify({"error": "Invalid start time format"}), 400

    db = get_db()
    cursor = db.execute(
        'INSERT INTO Tasks (user_id, title, description, start_time, all_day) VALUES (?, ?, ?, ?, ?)',
        (user_id, title, description, start_time_formatted, all_day)
    )
    db.commit()
    new_task_id = cursor.lastrowid

    return jsonify({
        "task_id": new_task_id,
        "title": title,
        "description": description,
        "start_time": start_time_formatted,
        "all_day": all_day
    }), 201


@app.route('/test_delete_task/<int:task_id>', methods=['POST'])
def test_delete_task(task_id):
    db = get_db()
    db.execute('DELETE FROM Tasks WHERE task_id = ? AND user_id = ?', (task_id, user_id))
    db.commit()
    return jsonify({"message": f"Task {task_id} deleted"}), 200


@app.route('/test_complete_task/<int:task_id>', methods=['POST'])
def test_complete_task(task_id):
    db = get_db()
    db.execute('UPDATE Tasks SET completed = 1 WHERE task_id = ?', (task_id,))
    db.commit()
    return jsonify({"message": f"Task {task_id} marked as completed"}), 200


@app.route('/test_update_task/<int:task_id>', methods=['POST'])
def test_update_task(task_id):
    data = request.get_json()
    title = data.get('title')
    description = data.get('description', '')
    start_time = data.get('start_time')
    all_day = data.get('all_day', 0)

    if not title or not start_time:
        return jsonify({"error": "Title and start_time required"}), 400

    db = get_db()
    db.execute("""
        UPDATE Tasks
        SET title = ?, description = ?, start_time = ?, all_day = ?
        WHERE task_id = ?
    """, (title, description, start_time, all_day, task_id))
    db.commit()

    return jsonify({
        "task_id": task_id,
        "title": title,
        "description": description,
        "start_time": start_time,
        "all_day": all_day
    }), 200



if __name__=="__main__":
    app.run(debug=True)