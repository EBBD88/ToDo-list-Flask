from flask import Flask, g
import sqlite3


DATABASE = 'todo_list.db'



app = Flask(__name__)


def get_db():
    db = getattr(g, '_database', None)
    if db is None:
        db = g._database = sqlite3.connect(DATABASE)
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



@app.route("/home")
def home():

    # this sql needs user id and date
        # replace '2024-02-05' by user date
        # replace Tasks.user_id=1 by Tasks.user_id='user id'
    today_tasks_sql = """ 
                          SELECT *
                          FROM Tasks
                          WHERE date(start_time) = '2024-02-05'
                          AND Tasks.user_id=1
                          ORDER by start_time ASC;
                      """
    today_tasks_results = query_db(today_tasks_sql)
    
    # this sql needs user id and datetime and user id
        # replace Tasks.user_id=1 by Tasks.user_id='user id'
        # replace '2024-02-04' with user DATETIME
    upcoming_tasks_sql = """
                            SELECT Tasks.*
                            FROM tasks
                            WHERE date(start_time) BETWEEN '2024-02-05' AND Date('2024-02-10')
                            AND Tasks.user_id=1
                            ORDER by start_time ASC;
                         """
    upcoming_tasks_results = query_db(upcoming_tasks_sql)
    
    # this sql needs user DATETIME and user id
        # replace '2024-02-07 00:00:00' with user DATETIME
        # replace user_id=1 with user_id='user id' 
    ongoing_tasks_sql = """SELECT *
                           FROM tasks
                           WHERE (start_time < '2024-02-07 00:00:00'
                           AND (finish_time > '2024-02-07 00:00:00'
                           OR finish_time IS NULL))
                           AND completed = 0
                           AND user_id = 1
                           ORDER BY finish_time DESC;
                        """
    ongoing_tasks_results = query_db(ongoing_tasks_sql)

    goals_sql = """
                    SELECT *
                    FROM Goals
                    WHERE completed = 0
                    AND user_id = 1
                    ORDER BY importance desc;
                """
    goal_results = query_db(goals_sql)

    results = {
        'Today_tasks' : today_tasks_results,
        'Upcoming_tasks' : upcoming_tasks_results,
        'Ongoing_tasks' : ongoing_tasks_results,
        'Goals' : goal_results
    }
    return results







if __name__=="__main__":
    app.run(debug=True)