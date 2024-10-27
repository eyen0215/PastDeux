from flask import Flask, render_template, request, redirect, url_for, jsonify, session
from datetime import datetime
import calendar
from functools import wraps
import re
from dotenv import load_dotenv
import os
from henry import Database
load_dotenv()

app = Flask(__name__)
app.secret_key = os.environ.get('FLASK_SECRET_KEY')
database = Database()

# Define pastel colors for each category
default_categories = {
    'homework': '#FFB3B3',  # Pastel red
    'event': '#B3E0FF',     # Pastel blue
    'exam': '#B3FFB3',      # Pastel green
    'chore': '#E0B3FF',     # Pastel purple
    'custom': '#808080'     # Default gray for custom tasks
}

def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not session.get('user_id'):
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function

def get_month_calendar(year, month):
    cal = calendar.monthcalendar(year, month)
    month_name = calendar.month_name[month]
    return cal, month_name

def get_tasks_for_date(date_str):
    user_id = session.get('user_id')
    if not user_id:
        return []
    
    all_tasks = database.get_user_tasks(user_id)
    return [task for task in all_tasks if task['due_date'].split('T')[0] == date_str]

@app.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
        
        # Basic server-side validation
        if len(password) < 6:
            return jsonify({'error': 'Password must be at least 6 characters long'}), 400
            
        email_regex = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        if not re.match(email_regex, email):
            return jsonify({'error': 'Invalid email format'}), 400
            
        # Register user with additional data
        additional_data = {
            'created_at': datetime.now().isoformat(),
            'last_login': datetime.now().isoformat()
        }
        
        user = database.register_user(email, password, additional_data)
        if user:
            session['user_id'] = user['localId']
            return redirect(url_for('calendar_view'))
        else:
            return render_template('signup.html', error="Registration failed. Please try again.")
            
    return render_template('signup.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')

        user = database.authenticate_user(email, password)
        if user:
            session['user_id'] = user['localId']
            # Update last login time in Firestore
            # database.update_user(user['localId'], {'last_login': datetime.now().isoformat()})
            return redirect(url_for('calendar_view'))
        else:
            return render_template('login.html', error="Invalid login credentials")
    
    return render_template('login.html')

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('home'))

@app.route('/')
def home():
    if session.get('user_id'):
        return redirect(url_for('calendar_view'))
    return render_template('home.html', logged_in=session.get('user_id') is not None)

@app.route('/calendar')
@login_required
def calendar_view():
    today = datetime.now()
    year = int(request.args.get('year', today.year))
    month = int(request.args.get('month', today.month))

    cal, month_name = get_month_calendar(year, month)

    prev_month = month - 1
    prev_year = year
    if prev_month < 1:
        prev_month = 12
        prev_year -= 1

    next_month = month + 1
    next_year = year
    if next_month > 12:
        next_month = 1
        next_year += 1

    # Get tasks from Firebase
    user_id = session.get('user_id')
    tasks = database.get_user_tasks(user_id)

    return render_template('calendar.html',
                         calendar=cal,
                         month_name=month_name,
                         year=year,
                         month=month,
                         prev_month=prev_month,
                         prev_year=prev_year,
                         next_month=next_month,
                         next_year=next_year,
                         tasks=tasks,
                         get_tasks_for_date=get_tasks_for_date,
                         logged_in=True)

@app.route('/day/<date>')
@login_required
def day_view(date):
    day_tasks = get_tasks_for_date(date)
    return render_template('day.html',
                         date=date,
                         tasks=day_tasks,
                         categories=default_categories, logged_in=session.get('user_id') is not None)

@app.route('/add_task', methods=['POST'])
@login_required
def add_task():
    if request.method == 'POST':
        user_id = session.get('user_id')
        task_type = request.form.get('task_type')
        description = request.form.get('description')
        due_date = request.form.get('due_date')

        # Use the default color for the task type, or the custom color if provided
        color = (request.form.get('color')
                if task_type == 'custom'
                else default_categories.get(task_type))

        task_data = {
            'type': task_type,
            'description': description,
            'due_date': due_date,
            'color': color,
            'completed': False,
            'overdue': False
        }

        new_task = database.add_task(user_id, task_data)
        if new_task:
            date = due_date.split('T')[0]
            return redirect(url_for('day_view', date=date))
        else:
            return jsonify({'error': 'Failed to add task'}), 500

@app.route('/toggle_task/<task_id>', methods=['POST'])
@login_required
def toggle_task(task_id):
    user_id = session.get('user_id')
    tasks = database.get_user_tasks(user_id)
    task = next((t for t in tasks if t['id'] == task_id), None)
    
    if task:
        success = database.update_task(user_id, task_id, {
            'completed': not task['completed']
        })
        return jsonify({'success': success})
    return jsonify({'error': 'Task not found'}), 404

@app.route('/delete_task/<task_id>', methods=['POST'])
@login_required
def delete_task(task_id):
    user_id = session.get('user_id')
    success = database.delete_task(user_id, task_id)
    return jsonify({'success': success})

if __name__ == '__main__':
    app.run(debug=True)