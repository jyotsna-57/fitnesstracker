from flask import Flask, render_template, request, redirect, url_for, session, jsonify, flash
import sqlite3
import datetime
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)
app.secret_key = 'your_secret_key_here'  # Change this in production

# Database initialization
def init_db():
    conn = sqlite3.connect('fitness.db')
    c = conn.cursor()
    
    # Users table
    c.execute('''CREATE TABLE IF NOT EXISTS users
                 (id INTEGER PRIMARY KEY AUTOINCREMENT,
                  username TEXT UNIQUE NOT NULL,
                  password TEXT NOT NULL,
                  name TEXT,
                  age INTEGER,
                  gender TEXT,
                  height REAL,
                  weight REAL,
                  goal_weight REAL,
                  daily_calorie_target INTEGER)''')
    
    # Workouts table
    c.execute('''CREATE TABLE IF NOT EXISTS workouts
                 (id INTEGER PRIMARY KEY AUTOINCREMENT,
                  user_id INTEGER,
                  date TEXT NOT NULL,
                  exercise_type TEXT NOT NULL,
                  duration INTEGER NOT NULL,
                  calories_burned INTEGER,
                  notes TEXT,
                  FOREIGN KEY (user_id) REFERENCES users (id))''')
    
    # Meals table
    c.execute('''CREATE TABLE IF NOT EXISTS meals
                 (id INTEGER PRIMARY KEY AUTOINCREMENT,
                  user_id INTEGER,
                  date TEXT NOT NULL,
                  meal_type TEXT NOT NULL,
                  food_item TEXT NOT NULL,
                  calories INTEGER NOT NULL,
                  FOREIGN KEY (user_id) REFERENCES users (id))''')
    
    # Goals table
    c.execute('''CREATE TABLE IF NOT EXISTS goals
                 (id INTEGER PRIMARY KEY AUTOINCREMENT,
                  user_id INTEGER,
                  goal_type TEXT NOT NULL,
                  target_value REAL NOT NULL,
                  target_date TEXT NOT NULL,
                  current_value REAL,
                  completed INTEGER DEFAULT 0,
                  FOREIGN KEY (user_id) REFERENCES users (id))''')
    
    # Habits table
    c.execute('''CREATE TABLE IF NOT EXISTS habits
                 (id INTEGER PRIMARY KEY AUTOINCREMENT,
                  user_id INTEGER,
                  habit_name TEXT NOT NULL,
                  frequency TEXT NOT NULL,
                  goal_description TEXT,
                  streak INTEGER DEFAULT 0,
                  last_completed TEXT,
                  FOREIGN KEY (user_id) REFERENCES users (id))''')
    
    conn.commit()
    conn.close()

init_db()

# Database helper functions
def get_db_connection():
    conn = sqlite3.connect('fitness.db')
    conn.row_factory = sqlite3.Row
    return conn

# User authentication
@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        password = generate_password_hash(request.form['password'])
        name = request.form['name']
        
        conn = get_db_connection()
        try:
            conn.execute('INSERT INTO users (username, password, name) VALUES (?, ?, ?)',
                         (username, password, name))
            conn.commit()
            conn.close()
            return redirect(url_for('login'))
        except sqlite3.IntegrityError:
            conn.close()
            return "Username already exists. Please choose a different one."
    
    return render_template('register.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        
        conn = get_db_connection()
        user = conn.execute('SELECT * FROM users WHERE username = ?', (username,)).fetchone()
        conn.close()
        
        if user and check_password_hash(user['password'], password):
            session['user_id'] = user['id']
            session['username'] = user['username']
            return redirect(url_for('index'))
        else:
            flash('Invalid username or password')
            return redirect(url_for('login'))
    
    return render_template('login.html')

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login'))

# Main application routes
@app.route('/')
def index():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    user_id = session['user_id']
    conn = get_db_connection()
    
    # Get user info
    user = conn.execute('SELECT * FROM users WHERE id = ?', (user_id,)).fetchone()
    
    # Get today's workouts
    today = datetime.date.today().isoformat()
    workouts = conn.execute('SELECT * FROM workouts WHERE user_id = ? AND date = ?', 
                           (user_id, today)).fetchall()
    
    # Get today's meals
    meals = conn.execute('SELECT * FROM meals WHERE user_id = ? AND date = ?', 
                        (user_id, today)).fetchall()
    
    # Get goals
    goals = conn.execute('SELECT * FROM goals WHERE user_id = ?', (user_id,)).fetchall()
    
    # Get habits
    habits = conn.execute('SELECT * FROM habits WHERE user_id = ?', (user_id,)).fetchall()
    
    # Calculate total calories for today
    total_calories_burned = sum(workout['calories_burned'] for workout in workouts)
    total_calories_consumed = sum(meal['calories'] for meal in meals)
    
    conn.close()
    
    return render_template('index.html', 
                          user=user, 
                          workouts=workouts, 
                          meals=meals, 
                          goals=goals,
                          habits=habits,
                          total_calories_burned=total_calories_burned,
                          total_calories_consumed=total_calories_consumed,
                          today=today)

# Workout routes
@app.route('/add_workout', methods=['POST'])
def add_workout():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    user_id = session['user_id']
    date = request.form['date']
    exercise_type = request.form['exercise_type']
    duration = int(request.form['duration'])
    notes = request.form.get('notes', '')
    
    # Simple calorie calculation (can be improved)
    calories_burned = duration * 7  # Approximate calories burned per minute
    
    conn = get_db_connection()
    conn.execute('INSERT INTO workouts (user_id, date, exercise_type, duration, calories_burned, notes) VALUES (?, ?, ?, ?, ?, ?)',
                 (user_id, date, exercise_type, duration, calories_burned, notes))
    conn.commit()
    conn.close()
    
    return redirect(url_for('index'))

@app.route('/delete_workout/<int:workout_id>')
def delete_workout(workout_id):
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    conn = get_db_connection()
    conn.execute('DELETE FROM workouts WHERE id = ?', (workout_id,))
    conn.commit()
    conn.close()
    
    return redirect(url_for('index'))

# Meal routes
@app.route('/add_meal', methods=['POST'])
def add_meal():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    user_id = session['user_id']
    date = request.form['date']
    meal_type = request.form['meal_type']
    food_item = request.form['food_item']
    calories = int(request.form['calories'])
    
    conn = get_db_connection()
    conn.execute('INSERT INTO meals (user_id, date, meal_type, food_item, calories) VALUES (?, ?, ?, ?, ?)',
                 (user_id, date, meal_type, food_item, calories))
    conn.commit()
    conn.close()
    
    return redirect(url_for('index'))

@app.route('/delete_meal/<int:meal_id>')
def delete_meal(meal_id):
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    conn = get_db_connection()
    conn.execute('DELETE FROM meals WHERE id = ?', (meal_id,))
    conn.commit()
    conn.close()
    
    return redirect(url_for('index'))

# Goal routes
@app.route('/add_goal', methods=['POST'])
def add_goal():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    user_id = session['user_id']
    goal_type = request.form['goal_type']
    target_value = float(request.form['target_value'])
    target_date = request.form['target_date']
    current_value = float(request.form.get('current_value', 0))
    
    conn = get_db_connection()
    conn.execute('INSERT INTO goals (user_id, goal_type, target_value, target_date, current_value) VALUES (?, ?, ?, ?, ?)',
                 (user_id, goal_type, target_value, target_date, current_value))
    conn.commit()
    conn.close()
    
    return redirect(url_for('index'))

@app.route('/update_goal/<int:goal_id>', methods=['POST'])
def update_goal(goal_id):
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    current_value = float(request.form['current_value'])
    completed = 1 if 'completed' in request.form else 0
    
    conn = get_db_connection()
    conn.execute('UPDATE goals SET current_value = ?, completed = ? WHERE id = ?',
                 (current_value, completed, goal_id))
    conn.commit()
    conn.close()
    
    return redirect(url_for('index'))

@app.route('/delete_goal/<int:goal_id>')
def delete_goal(goal_id):
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    conn = get_db_connection()
    conn.execute('DELETE FROM goals WHERE id = ?', (goal_id,))
    conn.commit()
    conn.close()
    
    return redirect(url_for('index'))

# Habit routes
@app.route('/add_habit', methods=['POST'])
def add_habit():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    user_id = session['user_id']
    habit_name = request.form['habit_name']
    frequency = request.form['frequency']
    goal_description = request.form.get('goal_description', '')
    
    conn = get_db_connection()
    conn.execute('INSERT INTO habits (user_id, habit_name, frequency, goal_description) VALUES (?, ?, ?, ?)',
                 (user_id, habit_name, frequency, goal_description))
    conn.commit()
    conn.close()
    
    return redirect(url_for('index'))

@app.route('/complete_habit/<int:habit_id>')
def complete_habit(habit_id):
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    today = datetime.date.today().isoformat()
    
    conn = get_db_connection()
    habit = conn.execute('SELECT * FROM habits WHERE id = ?', (habit_id,)).fetchone()
    
    # Check if habit was already completed today
    if habit['last_completed'] != today:
        new_streak = habit['streak'] + 1
        conn.execute('UPDATE habits SET streak = ?, last_completed = ? WHERE id = ?',
                     (new_streak, today, habit_id))
        conn.commit()
    
    conn.close()
    
    return redirect(url_for('index'))

@app.route('/delete_habit/<int:habit_id>')
def delete_habit(habit_id):
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    conn = get_db_connection()
    conn.execute('DELETE FROM habits WHERE id = ?', (habit_id,))
    conn.commit()
    conn.close()
    
    return redirect(url_for('index'))

# Profile routes
@app.route('/profile')
def profile():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    user_id = session['user_id']
    conn = get_db_connection()
    user = conn.execute('SELECT * FROM users WHERE id = ?', (user_id,)).fetchone()
    conn.close()
    
    return render_template('profile.html', user=user)

@app.route('/update_profile', methods=['POST'])
def update_profile():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    user_id = session['user_id']
    name = request.form['name']
    age = int(request.form['age'])
    gender = request.form['gender']
    height = float(request.form['height'])
    weight = float(request.form['weight'])
    goal_weight = float(request.form['goal_weight'])
    daily_calorie_target = int(request.form['daily_calorie_target'])
    
    conn = get_db_connection()
    conn.execute('''UPDATE users SET name = ?, age = ?, gender = ?, height = ?, 
                    weight = ?, goal_weight = ?, daily_calorie_target = ? WHERE id = ?''',
                 (name, age, gender, height, weight, goal_weight, daily_calorie_target, user_id))
    conn.commit()
    conn.close()
    
    return redirect(url_for('profile'))

# Progress reports
@app.route('/reports')
def reports():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    user_id = session['user_id']
    conn = get_db_connection()
    
    # Get workout data for the last 7 days
    seven_days_ago = (datetime.date.today() - datetime.timedelta(days=7)).isoformat()
    workouts = conn.execute('''SELECT date, SUM(duration) as total_duration, 
                              SUM(calories_burned) as total_calories 
                              FROM workouts 
                              WHERE user_id = ? AND date >= ? 
                              GROUP BY date''', 
                           (user_id, seven_days_ago)).fetchall()
    
    # Get meal data for the last 7 days
    meals = conn.execute('''SELECT date, SUM(calories) as total_calories 
                           FROM meals 
                           WHERE user_id = ? AND date >= ? 
                           GROUP BY date''', 
                        (user_id, seven_days_ago)).fetchall()
    
    # Get weight progress if available
    weight_goals = conn.execute('''SELECT target_date, target_value, current_value 
                                  FROM goals 
                                  WHERE user_id = ? AND goal_type = "weight" 
                                  ORDER BY target_date''', 
                               (user_id,)).fetchall()
    
    conn.close()
    
    return render_template('reports.html', 
                          workouts=workouts, 
                          meals=meals, 
                          weight_goals=weight_goals)

# API endpoints for charts
@app.route('/api/workout_data')
def workout_data():
    if 'user_id' not in session:
        return jsonify({})
    
    user_id = session['user_id']
    conn = get_db_connection()
    
    # Get workout data for the last 7 days
    seven_days_ago = (datetime.date.today() - datetime.timedelta(days=7)).isoformat()
    workouts = conn.execute('''SELECT date, SUM(duration) as total_duration 
                              FROM workouts 
                              WHERE user_id = ? AND date >= ? 
                              GROUP BY date''', 
                           (user_id, seven_days_ago)).fetchall()
    
    conn.close()
    
    # Format data for chart
    dates = []
    durations = []
    for workout in workouts:
        dates.append(workout['date'])
        durations.append(workout['total_duration'])
    
    return jsonify({'dates': dates, 'durations': durations})

@app.route('/api/calorie_data')
def calorie_data():
    if 'user_id' not in session:
        return jsonify({})
    
    user_id = session['user_id']
    conn = get_db_connection()
    
    # Get calorie data for the last 7 days
    seven_days_ago = (datetime.date.today() - datetime.timedelta(days=7)).isoformat()
    burned = conn.execute('''SELECT date, SUM(calories_burned) as total_calories 
                            FROM workouts 
                            WHERE user_id = ? AND date >= ? 
                            GROUP BY date''', 
                         (user_id, seven_days_ago)).fetchall()
    
    consumed = conn.execute('''SELECT date, SUM(calories) as total_calories 
                              FROM meals 
                              WHERE user_id = ? AND date >= ? 
                              GROUP BY date''', 
                           (user_id, seven_days_ago)).fetchall()
    
    conn.close()
    
    # Format data for chart
    dates = []
    burned_data = []
    consumed_data = []
    
    # Create a dictionary for easy lookup
    burned_dict = {item['date']: item['total_calories'] for item in burned}
    consumed_dict = {item['date']: item['total_calories'] for item in consumed}
    
    # Generate dates for the last 7 days
    for i in range(7):
        date = (datetime.date.today() - datetime.timedelta(days=i)).isoformat()
        dates.insert(0, date)
        burned_data.insert(0, burned_dict.get(date, 0))
        consumed_data.insert(0, consumed_dict.get(date, 0))
    
    return jsonify({
        'dates': dates,
        'burned': burned_data,
        'consumed': consumed_data
    })

if __name__ == '__main__':
    app.run(debug=True)