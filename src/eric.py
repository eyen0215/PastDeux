from flask import Flask, render_template, request, redirect, url_for, jsonify, session
from datetime import datetime
import calendar
from henry import Database

app = Flask(__name__)

# Temporary storage until Firebase integration
tasks = []
database = Database()

# Define pastel colors for each category
default_categories = {
    'homework': '#FFB3B3',  # Pastel red
    'event': '#B3E0FF',     # Pastel blue
    'exam': '#B3FFB3',      # Pastel green
    'chore': '#E0B3FF',     # Pastel purple
    'custom': '#808080'     # Default gray for custom tasks
}

def get_month_calendar(year, month):
    cal = calendar.monthcalendar(year, month)
    month_name = calendar.month_name[month]
    return cal, month_name

def get_tasks_for_date(date_str):
    return [task for task in tasks if task['due_date'].split('T')[0] == date_str]

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
            
        # Here you would typically store the user credentials
        print(f"New signup - Email: {email}, Password: {password}")
        
        # For now, just log them in like the login route
        session['logged_in'] = True
        return redirect(url_for('calendar_view'))
        
    return render_template('signup.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    error = None

    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')

        # Here, you would normally validate the email and password
        # For now, let's just print them to the console
        print(f"Email: {email}, Password: {password}")

        if database.authenticate_user(email, password): 
            # Set session variable to indicate the user is logged in
            session['logged_in'] = True
            return redirect(url_for('calendar_view'))
        else:
            error = "Invalid Login Credentials"
    
    
    return render_template('login.html', error=error)

@app.route('/logout')
def logout():
    # Clear the session to log out the user
    session.pop('logged_in', None)
    return redirect(url_for('home'))  # Redirect to home after logout

@app.route('/')
def home():
    return render_template('home.html', logged_in=session.get('logged_in', False))

@app.route('/calendar')
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
                           logged_in=session.get('logged_in', False))  # Pass login status to the template

@app.route('/day/<date>')
def day_view(date):
    day_tasks = get_tasks_for_date(date)
    return render_template('day.html',
                           date=date,
                           tasks=day_tasks,
                           categories=default_categories)

@app.route('/add_task', methods=['POST'])
def add_task():
    if request.method == 'POST':
        task_type = request.form.get('task_type')
        description = request.form.get('description')
        due_date = request.form.get('due_date')

        # Use the default color for the task type, or the custom color if provided
        color = (request.form.get('color')
                 if task_type == 'custom'
                 else default_categories.get(task_type))

        new_task = {
            'id': len(tasks) + 1,
            'type': task_type,
            'description': description,
            'due_date': due_date,
            'color': color,
            'completed': False
        }
        tasks.append(new_task)
        date = due_date.split('T')[0]
        return redirect(url_for('day_view', date=date))

@app.route('/toggle_task/<int:task_id>', methods=['POST'])
def toggle_task(task_id):
    task = next((task for task in tasks if task['id'] == task_id), None)
    if task:
        task['completed'] = not task['completed']
    return jsonify({'success': True})

if __name__ == '__main__':
    app.run(debug=True)
