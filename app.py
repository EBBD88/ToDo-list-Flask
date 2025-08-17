from flask import Flask, g, render_template, request, jsonify, session, redirect, url_for
from datetime import datetime, timedelta
import sqlite3



app = Flask(__name__)
app.secret_key = 'super_secret_key'


DATABASE = 'todo_list.db'
user_id = 1  # This should be dynamically set based on the logged-in user

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
        user_local_date = user_time_corrected.date().isoformat()
        session['user_local_date'] = user_local_date
    except Exception as e:
        return jsonify({'error': 'Invalid date format sent from client.'}), 400
    return jsonify({'status': 'success'})


@app.route("/home")
def home():
    user_local_date = session.get('user_local_date')
    if not user_local_date:
        return redirect(url_for('runJS'))  # Ensure we have the local date
    
    today_tasks_sql = """ 
                          SELECT *
                          FROM Tasks
                          WHERE date(start_time) = ?
                          AND Tasks.user_id=?
                          ORDER by start_time ASC;
                      """
    today_tasks_results = query_db(today_tasks_sql, [user_local_date, user_id])
    
    # this sql needs user id and datetime and user id
        # replace '2024-02-04' with user DATETIME
    upcoming_tasks_sql = """
                            SELECT Tasks.*
                            FROM tasks
                            WHERE date(start_time) BETWEEN '2024-02-05' AND Date('2024-02-10')
                            AND Tasks.user_id=?
                            ORDER by start_time ASC;
                         """
    upcoming_tasks_results = query_db(upcoming_tasks_sql, [user_id])
    
    # this sql needs user DATETIME and user id
        # replace '2024-02-07 00:00:00' with user DATETIME
        # replace user_id=1 with user_id='user id' 
    ongoing_tasks_sql = """SELECT *
                           FROM tasks
                           WHERE (start_time < '2024-02-07 00:00:00'
                           AND (finish_time > '2024-02-07 00:00:00'
                           OR finish_time IS NULL))
                           AND completed = 0
                           AND user_id = ?
                           ORDER BY finish_time DESC;
                        """
    ongoing_tasks_results = query_db(ongoing_tasks_sql, [user_id])

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
    return render_template('home.html', results=results, user_local_date=user_local_date)







if __name__=="__main__":
    app.run(debug=True)