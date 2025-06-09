from flask import Flask, render_template, request, redirect, url_for, flash, session, jsonify
import sqlite3
from datetime import datetime, date
import hashlib
import os

app = Flask(__name__)
app.secret_key = 'your-secret-key-here'  # Change this to a random secret key

# Database initialization
def init_db():
    conn = sqlite3.connect('student_sport_portfolio.db')
    cursor = conn.cursor()
    
    # Create Students table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS Students (
            StudentID INTEGER PRIMARY KEY AUTOINCREMENT,
            USN TEXT UNIQUE NOT NULL,
            FirstName TEXT NOT NULL,
            LastName TEXT NOT NULL,
            DateOfBirth DATE NOT NULL,
            Email TEXT NOT NULL,
            CollegeJoiningYear INTEGER,
            CollegeEndingYear INTEGER,
            Branch TEXT,
            Section TEXT,
            PhoneNumber TEXT,
            AgentName TEXT,
            AgentPhoneNumber TEXT,
            CreatedAt TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            UpdatedAt TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # Create Sports table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS Sports (
            SportID INTEGER PRIMARY KEY AUTOINCREMENT,
            SportName TEXT UNIQUE NOT NULL
        )
    ''')
    
    # Create Tournaments table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS Tournaments (
            TournamentID INTEGER PRIMARY KEY AUTOINCREMENT,
            StudentID INTEGER,
            SportID INTEGER,
            TournamentName TEXT NOT NULL,
            TournamentDate DATE NOT NULL,
            LeagueLevel TEXT NOT NULL,
            EventType TEXT NOT NULL,
            TeamName TEXT,
            TeamRole TEXT,
            Opponents TEXT NOT NULL,
            CoachName TEXT,
            StudentScore TEXT,
            OpponentScore TEXT,
            Outcome TEXT NOT NULL,
            AchievementsAwards TEXT,
            Notes TEXT,
            CreatedAt TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            UpdatedAt TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (StudentID) REFERENCES Students (StudentID),
            FOREIGN KEY (SportID) REFERENCES Sports (SportID)
        )
    ''')
    
    # Create Admin table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS Admin (
            AdminID INTEGER PRIMARY KEY AUTOINCREMENT,
            Username TEXT UNIQUE NOT NULL,
            PasswordHash TEXT NOT NULL,
            CreatedAt TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # Insert default sports
    sports = [
        'Cricket', 'Football', 'Weightlifting', 'Powerlifting', 'Tennis', 
        'Table Tennis', 'Basketball', 'Kho Kho', 'Kabaddi', 'Volleyball', 
        'Athletics', 'Badminton', 'Chess'
    ]
    
    for sport in sports:
        cursor.execute('INSERT OR IGNORE INTO Sports (SportName) VALUES (?)', (sport,))
    
    conn.commit()
    conn.close()

def get_db_connection():
    conn = sqlite3.connect('student_sport_portfolio.db')
    conn.row_factory = sqlite3.Row
    return conn

def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()

def row_to_dict(row):
    """Convert SQLite Row object to dictionary"""
    if row is None:
        return None
    return dict(row)

def rows_to_dict_list(rows):
    """Convert list of SQLite Row objects to list of dictionaries"""
    return [dict(row) for row in rows]

def calculate_student_stats(student_id):
    """Calculate statistics for a specific student"""
    conn = get_db_connection()
    
    # Get total tournaments
    total_tournaments = conn.execute(
        'SELECT COUNT(*) as count FROM Tournaments WHERE StudentID = ?',
        (student_id,)
    ).fetchone()['count']
    
    # Get wins
    total_wins = conn.execute(
        'SELECT COUNT(*) as count FROM Tournaments WHERE StudentID = ? AND Outcome = "Win"',
        (student_id,)
    ).fetchone()['count']
    
    # Get unique sports played
    sports_played = conn.execute(
        'SELECT COUNT(DISTINCT SportID) as count FROM Tournaments WHERE StudentID = ?',
        (student_id,)
    ).fetchone()['count']
    
    # Calculate win percentage
    win_percentage = round((total_wins / total_tournaments * 100) if total_tournaments > 0 else 0, 1)
    
    conn.close()
    
    return {
        'total_tournaments': total_tournaments,
        'total_wins': total_wins,
        'sports_played': sports_played,
        'win_percentage': win_percentage
    }

def check_admin_exists():
    """Check if admin credentials exist"""
    conn = get_db_connection()
    admin_count = conn.execute('SELECT COUNT(*) as count FROM Admin').fetchone()['count']
    conn.close()
    return admin_count > 0

@app.route('/')
def index():
    return redirect(url_for('login'))

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        usn = request.form['usn'].upper()
        dob = request.form['dob']
        
        conn = get_db_connection()
        student = conn.execute(
            'SELECT * FROM Students WHERE USN = ? AND DateOfBirth = ?',
            (usn, dob)
        ).fetchone()
        conn.close()
        
        if student:
            session['student_id'] = student['StudentID']
            session['student_name'] = f"{student['FirstName']} {student['LastName']}"
            flash('Login successful!', 'success')
            return redirect(url_for('dashboard'))
        else:
            flash('Invalid USN or Date of Birth. Please try again.', 'danger')
    
    return render_template('login.html')

@app.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == 'POST':
        try:
            # Get form data
            usn = request.form['usn'].upper()
            first_name = request.form['first_name']
            last_name = request.form['last_name']
            dob = request.form['dob']
            email = request.form['email']
            college_joining_year = int(request.form['college_joining_year'])
            college_ending_year = int(request.form['college_ending_year'])
            branch = request.form['branch']
            section = request.form['section']
            phone_number = request.form['phone_number']
            agent_name = request.form.get('agent_name', '')
            agent_phone_number = request.form.get('agent_phone_number', '')
            
            conn = get_db_connection()
            
            # Check if USN already exists
            existing_student = conn.execute(
                'SELECT USN FROM Students WHERE USN = ?', (usn,)
            ).fetchone()
            
            if existing_student:
                flash('A student with this USN already exists.', 'danger')
                conn.close()
                return render_template('signup.html', 
                                     form_data=request.form, 
                                     current_year=datetime.now().year)
            
            # Insert new student
            conn.execute('''
                INSERT INTO Students (
                    USN, FirstName, LastName, DateOfBirth, Email,
                    CollegeJoiningYear, CollegeEndingYear, Branch, Section,
                    PhoneNumber, AgentName, AgentPhoneNumber
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                usn, first_name, last_name, dob, email,
                college_joining_year, college_ending_year, branch, section,
                phone_number, agent_name, agent_phone_number
            ))
            
            conn.commit()
            conn.close()
            
            flash('Account created successfully! You can now log in.', 'success')
            return redirect(url_for('login'))
            
        except Exception as e:
            flash(f'Error creating account: {str(e)}', 'danger')
            return render_template('signup.html', 
                                 form_data=request.form, 
                                 current_year=datetime.now().year)
    
    return render_template('signup.html', current_year=datetime.now().year)

@app.route('/dashboard')
def dashboard():
    if 'student_id' not in session:
        flash('Please log in to access the dashboard.', 'warning')
        return redirect(url_for('login'))
    
    student_id = session['student_id']
    conn = get_db_connection()
    
    # Get student information
    student = conn.execute(
        'SELECT * FROM Students WHERE StudentID = ?',
        (student_id,)
    ).fetchone()
    
    # Get tournaments with sport names
    tournaments = conn.execute('''
        SELECT t.*, s.SportName 
        FROM Tournaments t
        JOIN Sports s ON t.SportID = s.SportID
        WHERE t.StudentID = ?
        ORDER BY t.TournamentDate DESC
    ''', (student_id,)).fetchall()
    
    conn.close()
    
    # Calculate student statistics
    stats = calculate_student_stats(student_id)
    
    # Format tournament dates for display
    formatted_tournaments = []
    for tournament in tournaments:
        tournament_dict = dict(tournament)
        # Convert date format from YYYY-MM-DD to DD/MM/YYYY for display
        if tournament_dict['TournamentDate']:
            date_obj = datetime.strptime(tournament_dict['TournamentDate'], '%Y-%m-%d')
            tournament_dict['TournamentDate'] = date_obj.strftime('%d/%m/%Y')
        formatted_tournaments.append(tournament_dict)
    
    return render_template('dashboard.html', 
                         student=student, 
                         tournaments=formatted_tournaments,
                         stats=stats)

@app.route('/add_tournament', methods=['GET', 'POST'])
def add_tournament():
    if 'student_id' not in session:
        flash('Please log in to access this page.', 'warning')
        return redirect(url_for('login'))
    
    if request.method == 'POST':
        try:
            student_id = session['student_id']
            sport_id = request.form['sport_id']
            tournament_name = request.form['tournament_name']
            tournament_date = request.form['tournament_date']
            league_level = request.form['league_level']
            event_type = request.form['event_type']
            team_name = request.form.get('team_name', '')
            team_role = request.form.get('team_role', '')
            opponents = request.form['opponents']
            coach_name = request.form.get('coach_name', '')
            student_score = request.form.get('student_score', '')
            opponent_score = request.form.get('opponent_score', '')
            outcome = request.form['outcome']
            achievements_awards = request.form.get('achievements_awards', '')
            notes = request.form.get('notes', '')
            
            conn = get_db_connection()
            conn.execute('''
                INSERT INTO Tournaments (
                    StudentID, SportID, TournamentName, TournamentDate, LeagueLevel,
                    EventType, TeamName, TeamRole, Opponents, CoachName,
                    StudentScore, OpponentScore, Outcome, AchievementsAwards, Notes
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                student_id, sport_id, tournament_name, tournament_date, league_level,
                event_type, team_name, team_role, opponents, coach_name,
                student_score, opponent_score, outcome, achievements_awards, notes
            ))
            conn.commit()
            conn.close()
            
            flash('Tournament entry added successfully!', 'success')
            return redirect(url_for('dashboard'))
            
        except Exception as e:
            flash(f'Error adding tournament: {str(e)}', 'danger')
    
    # Get sports for the form
    conn = get_db_connection()
    sports = conn.execute('SELECT * FROM Sports ORDER BY SportName').fetchall()
    conn.close()
    
    return render_template('add_edit_tournament.html', 
                         sports=sports, 
                         is_edit=False)

@app.route('/edit_tournament/<int:tournament_id>', methods=['GET', 'POST'])
def edit_tournament(tournament_id):
    if 'student_id' not in session:
        flash('Please log in to access this page.', 'warning')
        return redirect(url_for('login'))
    
    student_id = session['student_id']
    conn = get_db_connection()
    
    # Get tournament data
    tournament = conn.execute(
        'SELECT * FROM Tournaments WHERE TournamentID = ? AND StudentID = ?',
        (tournament_id, student_id)
    ).fetchone()
    
    if not tournament:
        flash('Tournament not found or access denied.', 'danger')
        conn.close()
        return redirect(url_for('dashboard'))
    
    if request.method == 'POST':
        try:
            sport_id = request.form['sport_id']
            tournament_name = request.form['tournament_name']
            tournament_date = request.form['tournament_date']
            league_level = request.form['league_level']
            event_type = request.form['event_type']
            team_name = request.form.get('team_name', '')
            team_role = request.form.get('team_role', '')
            opponents = request.form['opponents']
            coach_name = request.form.get('coach_name', '')
            student_score = request.form.get('student_score', '')
            opponent_score = request.form.get('opponent_score', '')
            outcome = request.form['outcome']
            achievements_awards = request.form.get('achievements_awards', '')
            notes = request.form.get('notes', '')
            
            conn.execute('''
                UPDATE Tournaments SET
                    SportID = ?, TournamentName = ?, TournamentDate = ?, LeagueLevel = ?,
                    EventType = ?, TeamName = ?, TeamRole = ?, Opponents = ?, CoachName = ?,
                    StudentScore = ?, OpponentScore = ?, Outcome = ?, AchievementsAwards = ?,
                    Notes = ?, UpdatedAt = CURRENT_TIMESTAMP
                WHERE TournamentID = ? AND StudentID = ?
            ''', (
                sport_id, tournament_name, tournament_date, league_level,
                event_type, team_name, team_role, opponents, coach_name,
                student_score, opponent_score, outcome, achievements_awards, notes,
                tournament_id, student_id
            ))
            conn.commit()
            conn.close()
            
            flash('Tournament entry updated successfully!', 'success')
            return redirect(url_for('dashboard'))
            
        except Exception as e:
            flash(f'Error updating tournament: {str(e)}', 'danger')
    
    # Get sports for the form
    sports = conn.execute('SELECT * FROM Sports ORDER BY SportName').fetchall()
    
    # Format date for form input (YYYY-MM-DD)
    display_tournament_date = tournament['TournamentDate']
    
    conn.close()
    
    return render_template('add_edit_tournament.html', 
                         sports=sports, 
                         tournament=tournament,
                         display_tournament_date=display_tournament_date,
                         is_edit=True)

@app.route('/delete_tournament/<int:tournament_id>', methods=['POST'])
def delete_tournament(tournament_id):
    if 'student_id' not in session:
        return jsonify({'success': False, 'message': 'Not logged in'}), 401
    
    student_id = session['student_id']
    
    try:
        conn = get_db_connection()
        
        # Check if tournament belongs to the logged-in student
        tournament = conn.execute(
            'SELECT TournamentID FROM Tournaments WHERE TournamentID = ? AND StudentID = ?',
            (tournament_id, student_id)
        ).fetchone()
        
        if not tournament:
            conn.close()
            return jsonify({'success': False, 'message': 'Tournament not found or access denied'}), 404
        
        # Delete the tournament
        conn.execute(
            'DELETE FROM Tournaments WHERE TournamentID = ? AND StudentID = ?',
            (tournament_id, student_id)
        )
        conn.commit()
        conn.close()
        
        return jsonify({'success': True, 'message': 'Tournament deleted successfully'})
        
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500

@app.route('/logout')
def logout():
    session.clear()
    flash('You have been logged out successfully.', 'info')
    return redirect(url_for('login'))

# Admin routes
@app.route('/admin')
def admin():
    """Redirect to admin login or setup based on whether admin exists"""
    if check_admin_exists():
        return redirect(url_for('admin_login'))
    else:
        return redirect(url_for('set_admin_credentials'))

@app.route('/admin_login', methods=['GET', 'POST'])
def admin_login():
    # Check if admin credentials exist, if not redirect to setup
    if not check_admin_exists():
        flash('No admin credentials found. Please set up admin credentials first.', 'warning')
        return redirect(url_for('set_admin_credentials'))
    
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        password_hash = hash_password(password)
        
        conn = get_db_connection()
        admin = conn.execute(
            'SELECT * FROM Admin WHERE Username = ? AND PasswordHash = ?',
            (username, password_hash)
        ).fetchone()
        conn.close()
        
        if admin:
            session['admin_id'] = admin['AdminID']
            session['admin_username'] = admin['Username']
            flash('Admin login successful!', 'success')
            return redirect(url_for('admin_dashboard'))
        else:
            flash('Invalid username or password.', 'danger')
    
    return render_template('admin_login.html')

@app.route('/admin_dashboard')
def admin_dashboard():
    if 'admin_id' not in session:
        flash('Please log in as admin to access this page.', 'warning')
        return redirect(url_for('admin_login'))
    
    conn = get_db_connection()
    
    # Get total students
    total_students = conn.execute('SELECT COUNT(*) as count FROM Students').fetchone()['count']
    
    # Get students per sport - convert to dict list
    students_per_sport_rows = conn.execute('''
        SELECT s.SportName, COUNT(DISTINCT t.StudentID) as student_count
        FROM Sports s
        LEFT JOIN Tournaments t ON s.SportID = t.SportID
        GROUP BY s.SportID, s.SportName
        ORDER BY student_count DESC
    ''').fetchall()
    students_per_sport = rows_to_dict_list(students_per_sport_rows)
    
    # Get tournaments per sport - convert to dict list
    tournaments_per_sport_rows = conn.execute('''
        SELECT s.SportName, COUNT(t.TournamentID) as tournament_count
        FROM Sports s
        LEFT JOIN Tournaments t ON s.SportID = t.SportID
        GROUP BY s.SportID, s.SportName
        ORDER BY tournament_count DESC
    ''').fetchall()
    tournaments_per_sport = rows_to_dict_list(tournaments_per_sport_rows)
    
    # Get all students with their statistics - convert to dict list
    students_rows = conn.execute('''
        SELECT 
            s.*,
            COUNT(t.TournamentID) as total_matches_played,
            SUM(CASE WHEN t.Outcome = 'Win' THEN 1 ELSE 0 END) as total_wins,
            SUM(CASE WHEN t.Outcome = 'Loss' THEN 1 ELSE 0 END) as total_losses,
            GROUP_CONCAT(DISTINCT sp.SportName) as sports_played_list,
            MAX(t.UpdatedAt) as last_updated_at_raw
        FROM Students s
        LEFT JOIN Tournaments t ON s.StudentID = t.StudentID
        LEFT JOIN Sports sp ON t.SportID = sp.SportID
        GROUP BY s.StudentID
        ORDER BY s.USN
    ''').fetchall()
    
    conn.close()
    
    # Format students data for JavaScript
    students_list = []
    for student_row in students_rows:
        student_dict = dict(student_row)
        
        # Format last updated date
        if student_dict['last_updated_at_raw']:
            try:
                date_obj = datetime.strptime(student_dict['last_updated_at_raw'], '%Y-%m-%d %H:%M:%S')
                student_dict['last_updated_at_display'] = date_obj.strftime('%d/%m/%Y')
                student_dict['last_updated_at_raw'] = date_obj.strftime('%d%m%Y')
            except:
                student_dict['last_updated_at_display'] = 'N/A'
                student_dict['last_updated_at_raw'] = '01011900'
        else:
            student_dict['last_updated_at_display'] = 'N/A'
            student_dict['last_updated_at_raw'] = '01011900'
        
        # Handle None values
        for key in ['total_matches_played', 'total_wins', 'total_losses']:
            if student_dict[key] is None:
                student_dict[key] = 0
        
        students_list.append(student_dict)
    
    return render_template('admin_dashboard.html',
                         total_students=total_students,
                         students_per_sport=students_per_sport,
                         tournaments_per_sport=tournaments_per_sport,
                         students=students_list)

@app.route('/set_admin_credentials', methods=['GET', 'POST'])
def set_admin_credentials():
    # Check if admin already exists
    if check_admin_exists():
        flash('Admin credentials already set. Please use the login page.', 'info')
        return redirect(url_for('admin_login'))
    
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        confirm_password = request.form['confirm_password']
        
        if password != confirm_password:
            flash('Passwords do not match.', 'danger')
            return render_template('set_admin_credentials.html')
        
        if len(password) < 6:
            flash('Password must be at least 6 characters long.', 'danger')
            return render_template('set_admin_credentials.html')
        
        password_hash = hash_password(password)
        
        try:
            conn = get_db_connection()
            conn.execute(
                'INSERT INTO Admin (Username, PasswordHash) VALUES (?, ?)',
                (username, password_hash)
            )
            conn.commit()
            conn.close()
            
            flash('Admin credentials set successfully! You can now log in.', 'success')
            return redirect(url_for('admin_login'))
            
        except Exception as e:
            flash(f'Error setting admin credentials: {str(e)}', 'danger')
    
    return render_template('set_admin_credentials.html')

@app.route('/admin_logout')
def admin_logout():
    session.pop('admin_id', None)
    session.pop('admin_username', None)
    flash('Admin logged out successfully.', 'info')
    return redirect(url_for('admin_login'))

if __name__ == '__main__':
    init_db()
    app.run(debug=True)