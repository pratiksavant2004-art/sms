import sqlite3
import os
from datetime import datetime
from bcrypt import hashpw, gensalt, checkpw

DB_PATH = 'auth_system.db'

def init_db():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    cursor.execute('''CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        full_name TEXT NOT NULL,
        email TEXT UNIQUE NOT NULL,
        password_hash BLOB NOT NULL,
        role TEXT NOT NULL,
        phone TEXT NOT NULL,
        location TEXT,
        designation TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )''')
    
    # Add columns if they don't exist (for migration)
    try:
        cursor.execute('ALTER TABLE users ADD COLUMN location TEXT')
    except:
        pass
    try:
        cursor.execute('ALTER TABLE users ADD COLUMN designation TEXT')
    except:
        pass
    
    cursor.execute('''CREATE TABLE IF NOT EXISTS submissions (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER NOT NULL,
        authorized_person TEXT NOT NULL,
        appointed_person TEXT NOT NULL,
        salary REAL NOT NULL,
        travel_allowance REAL NOT NULL,
        dearness_allowance REAL NOT NULL,
        sales_target REAL NOT NULL,
        remarks TEXT,
        status TEXT DEFAULT 'pending',
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (user_id) REFERENCES users (id)
    )''')
    
    conn.commit()
    conn.close()

def register_user(full_name, email, password, role, phone, location=None, designation=None):
    try:
        if not all([full_name, email, password, role, phone]):
            return False
        
        password_hash = hashpw(password.encode('utf-8'), gensalt())
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute('''INSERT INTO users (full_name, email, password_hash, role, phone, location, designation)
                         VALUES (?, ?, ?, ?, ?, ?, ?)''',
                      (full_name, email, password_hash, role, phone, location, designation))
        conn.commit()
        conn.close()
        return True
    except sqlite3.IntegrityError:
        return False
    except Exception as e:
        return False

def login_user(email, password):
    try:
        if not email or not password:
            return None
        
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute('SELECT id, password_hash FROM users WHERE email = ?', (email,))
        user = cursor.fetchone()
        conn.close()
        
        if user and checkpw(password.encode('utf-8'), user[1]):
            return user[0]
        return None
    except Exception as e:
        return None

def get_user(user_id):
    try:
        if not user_id:
            return None
        
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute('SELECT id, full_name, email, role, phone, location, designation FROM users WHERE id = ?', (user_id,))
        user = cursor.fetchone()
        conn.close()
        return user
    except Exception as e:
        return None

def user_has_submission(user_id):
    try:
        if not user_id:
            return False
        
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute('SELECT id FROM submissions WHERE user_id = ?', (user_id,))
        submission = cursor.fetchone()
        conn.close()
        return submission is not None
    except Exception as e:
        return False

def get_user_submission(user_id):
    try:
        if not user_id:
            return None
        
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM submissions WHERE user_id = ? ORDER BY created_at DESC LIMIT 1', (user_id,))
        submission = cursor.fetchone()
        conn.close()
        if submission:
            submission = list(submission)
            submission[4] = float(submission[4]) if submission[4] else 0.0
            submission[5] = float(submission[5]) if submission[5] else 0.0
            submission[6] = float(submission[6]) if submission[6] else 0.0
            submission[7] = float(submission[7]) if submission[7] else 0.0
            submission = tuple(submission)
        return submission
    except Exception as e:
        return None

def create_submission(user_id, authorized_person, appointed_person, salary, travel_allowance, dearness_allowance, sales_target, remarks):
    try:
        if not all([user_id, authorized_person, appointed_person]):
            return False
        
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute('''INSERT INTO submissions 
                         (user_id, authorized_person, appointed_person, salary, travel_allowance, dearness_allowance, sales_target, remarks)
                         VALUES (?, ?, ?, ?, ?, ?, ?, ?)''',
                      (user_id, authorized_person, appointed_person, salary, travel_allowance, dearness_allowance, sales_target, remarks))
        conn.commit()
        conn.close()
        return True
    except Exception as e:
        return False

def update_submission(submission_id, authorized_person, appointed_person, salary, travel_allowance, dearness_allowance, sales_target, remarks):
    try:
        if not submission_id or not all([authorized_person, appointed_person]):
            return False
        
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute('''UPDATE submissions 
                         SET authorized_person = ?, appointed_person = ?, salary = ?, travel_allowance = ?, 
                             dearness_allowance = ?, sales_target = ?, remarks = ?, status = 'pending', updated_at = CURRENT_TIMESTAMP
                         WHERE id = ?''',
                      (authorized_person, appointed_person, salary, travel_allowance, dearness_allowance, sales_target, remarks, submission_id))
        conn.commit()
        conn.close()
        return True
    except Exception as e:
        return False

def get_all_submissions():
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute('''SELECT s.id, s.user_id, u.full_name, u.email, u.role, u.location, u.designation, s.authorized_person, s.appointed_person, 
                               s.salary, s.travel_allowance, s.dearness_allowance, s.sales_target, s.remarks, s.status, s.created_at
                         FROM submissions s
                         JOIN users u ON s.user_id = u.id
                         ORDER BY s.created_at DESC''')
        submissions = cursor.fetchall()
        conn.close()
        result = []
        for sub in submissions:
            sub = list(sub)
            sub[9] = float(sub[9]) if sub[9] else 0.0
            sub[10] = float(sub[10]) if sub[10] else 0.0
            sub[11] = float(sub[11]) if sub[11] else 0.0
            sub[12] = float(sub[12]) if sub[12] else 0.0
            result.append(tuple(sub))
        return result
    except Exception as e:
        return []

def approve_submission(submission_id):
    try:
        if not submission_id:
            return False
        
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute('UPDATE submissions SET status = ?, updated_at = CURRENT_TIMESTAMP WHERE id = ?', ('approved', submission_id))
        conn.commit()
        conn.close()
        return True
    except Exception as e:
        return False

def reject_submission(submission_id):
    try:
        if not submission_id:
            return False
        
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute('UPDATE submissions SET status = ?, updated_at = CURRENT_TIMESTAMP WHERE id = ?', ('rejected', submission_id))
        conn.commit()
        conn.close()
        return True
    except Exception as e:
        return False

def get_submission_by_id(submission_id):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM submissions WHERE id = ?', (submission_id,))
    submission = cursor.fetchone()
    conn.close()
    if submission:
        submission = list(submission)
        submission[4] = float(submission[4]) if submission[4] else 0.0
        submission[5] = float(submission[5]) if submission[5] else 0.0
        submission[6] = float(submission[6]) if submission[6] else 0.0
        submission[7] = float(submission[7]) if submission[7] else 0.0
        submission = tuple(submission)
    return submission

def get_submission_stats():
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        cursor.execute('SELECT COUNT(*) FROM submissions WHERE status = ?', ('pending',))
        pending = cursor.fetchone()[0]
        
        cursor.execute('SELECT COUNT(*) FROM submissions WHERE status = ?', ('approved',))
        approved = cursor.fetchone()[0]
        
        cursor.execute('SELECT COUNT(*) FROM submissions WHERE status = ?', ('rejected',))
        rejected = cursor.fetchone()[0]
        
        cursor.execute('SELECT COUNT(*) FROM submissions')
        total = cursor.fetchone()[0]
        
        conn.close()
        return {'pending': pending, 'approved': approved, 'rejected': rejected, 'total': total}
    except Exception as e:
        return {'pending': 0, 'approved': 0, 'rejected': 0, 'total': 0}

def search_submissions(search_query):
    try:
        if not search_query:
            return get_all_submissions()
        
        search_term = f'%{search_query}%'
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute('''SELECT s.id, s.user_id, u.full_name, u.email, u.role, u.location, u.designation, s.authorized_person, s.appointed_person, 
                               s.salary, s.travel_allowance, s.dearness_allowance, s.sales_target, s.remarks, s.status, s.created_at
                         FROM submissions s
                         JOIN users u ON s.user_id = u.id
                         WHERE u.full_name LIKE ? OR u.email LIKE ? OR s.authorized_person LIKE ? OR s.status LIKE ?
                         ORDER BY s.created_at DESC''',
                      (search_term, search_term, search_term, search_term))
        submissions = cursor.fetchall()
        conn.close()
        result = []
        for sub in submissions:
            sub = list(sub)
            sub[9] = float(sub[9]) if sub[9] else 0.0
            sub[10] = float(sub[10]) if sub[10] else 0.0
            sub[11] = float(sub[11]) if sub[11] else 0.0
            sub[12] = float(sub[12]) if sub[12] else 0.0
            result.append(tuple(sub))
        return result
    except Exception as e:
        return []

def delete_submission(submission_id):
    try:
        if not submission_id:
            return False
        
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute('DELETE FROM submissions WHERE id = ?', (submission_id,))
        conn.commit()
        conn.close()
        return True
    except Exception as e:
        return False

def update_user_profile(user_id, full_name, phone, location=None, designation=None):
    try:
        if not all([user_id, full_name, phone]):
            return False
        
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute('UPDATE users SET full_name = ?, phone = ?, location = ?, designation = ? WHERE id = ?', 
                      (full_name, phone, location, designation, user_id))
        conn.commit()
        conn.close()
        return True
    except Exception as e:
        return False
