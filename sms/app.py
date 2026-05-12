from flask import Flask, render_template, request, redirect, session, send_file, jsonify
from database import (
    init_db, register_user, login_user, get_user, user_has_submission,
    get_user_submission, create_submission, update_submission, get_all_submissions,
    approve_submission, reject_submission, get_submission_stats, search_submissions,
    delete_submission, update_user_profile
)
from io import BytesIO
import csv
from datetime import datetime
from openpyxl import Workbook
import os
from dotenv import load_dotenv

load_dotenv()

# Indian States List
INDIAN_STATES = [
    'Andaman and Nicobar Islands', 'Andhra Pradesh', 'Arunachal Pradesh', 'Assam',
    'Bihar', 'Chandigarh', 'Chhattisgarh', 'Dadra and Nagar Haveli', 'Daman and Diu',
    'Delhi', 'Goa', 'Gujarat', 'Haryana', 'Himachal Pradesh', 'Jharkhand',
    'Karnataka', 'Kerala', 'Ladakh', 'Lakshadweep', 'Madhya Pradesh', 'Maharashtra',
    'Manipur', 'Meghalaya', 'Mizoram', 'Nagaland', 'Odisha', 'Puducherry', 'Punjab',
    'Rajasthan', 'Sikkim', 'Tamil Nadu', 'Telangana', 'Tripura', 'Uttar Pradesh',
    'Uttarakhand', 'West Bengal'
]

app = Flask(__name__)
app.secret_key = os.getenv('FLASK_SECRET_KEY', 'swaroop_agrochemical_secret_key_2024')

ADMIN_EMAIL = os.getenv('ADMIN_EMAIL')
ADMIN_PASSWORD = os.getenv('ADMIN_PASSWORD')

init_db()

@app.before_request
def load_logged_in_user():
    pass

@app.route('/')
def index():
    if 'user_id' in session:
        return redirect('/dashboard')
    if 'admin_id' in session:
        return redirect('/admin/dashboard')
    return redirect('/register')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        try:
            full_name = request.form.get('full_name', '').strip()
            email = request.form.get('email', '').strip()
            password = request.form.get('password', '')
            confirm_password = request.form.get('confirm_password', '')
            role = request.form.get('role', '')
            phone = request.form.get('phone', '').strip()
            location = request.form.get('location', '').strip()
            designation = request.form.get('designation', '').strip()
            
            if not all([full_name, email, password, role, phone, location, designation]):
                return render_template('register.html', error='All fields are required', states=INDIAN_STATES)
            
            if len(password) < 6:
                return render_template('register.html', error='Password must be at least 6 characters', states=INDIAN_STATES)
            
            if password != confirm_password:
                return render_template('register.html', error='Passwords do not match', states=INDIAN_STATES)
            
            if role not in ['employee', 'vendor']:
                return render_template('register.html', error='Invalid role selected', states=INDIAN_STATES)
            
            if len(phone) < 10:
                return render_template('register.html', error='Phone number must be at least 10 digits', states=INDIAN_STATES)
            
            if register_user(full_name, email, password, role, phone, location, designation):
                return redirect('/login?success=Registration successful')
            else:
                return render_template('register.html', error='Email already exists', states=INDIAN_STATES)
        except Exception as e:
            return render_template('register.html', error='An error occurred during registration. Please try again.', states=INDIAN_STATES)
    
    return render_template('register.html', states=INDIAN_STATES)

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        try:
            email = request.form.get('email', '').strip()
            password = request.form.get('password', '').strip()
            
            if not email or not password:
                return render_template('login.html', error='Email and password are required')
            
            user_id = login_user(email, password)
            if user_id:
                user = get_user(user_id)
                if user:
                    session['user_id'] = user_id
                    session['full_name'] = user[1]
                    session['email'] = user[2]
                    session['role'] = user[3]
                    return redirect('/dashboard')
                else:
                    return render_template('login.html', error='User data could not be loaded')
            else:
                return render_template('login.html', error='Invalid email or password')
        except Exception as e:
            return render_template('login.html', error='An error occurred during login. Please try again.')
    
    return render_template('login.html')

@app.route('/dashboard', methods=['GET', 'POST'])
def dashboard():
    if 'user_id' not in session:
        return redirect('/login')
    
    try:
        user_id = session['user_id']
        user = get_user(user_id)
        
        if not user:
            session.clear()
            return redirect('/login')
        
        has_submission = user_has_submission(user_id)
        submission = get_user_submission(user_id) if has_submission else None
        
        if request.method == 'POST':
            if 'submit_form' in request.form:
                try:
                    authorized_person = request.form.get('authorized_person', '').strip()
                    appointed_person = request.form.get('appointed_person', '').strip()
                    salary = request.form.get('salary', '0')
                    travel_allowance = request.form.get('travel_allowance', '0')
                    dearness_allowance = request.form.get('dearness_allowance', '0')
                    sales_target = request.form.get('sales_target', '0')
                    remarks = request.form.get('remarks', '').strip()
                    
                    if not authorized_person or not appointed_person:
                        return render_template('dashboard.html', user=user, has_submission=has_submission, 
                                             submission=submission, error='Authorized Person and Appointed Person are required')
                    
                    try:
                        salary = float(salary)
                        travel_allowance = float(travel_allowance)
                        dearness_allowance = float(dearness_allowance)
                        sales_target = float(sales_target)
                        
                        if salary < 0 or travel_allowance < 0 or dearness_allowance < 0 or sales_target < 0:
                            return render_template('dashboard.html', user=user, has_submission=has_submission, 
                                                 submission=submission, error='Numeric values cannot be negative')
                    except ValueError:
                        return render_template('dashboard.html', user=user, has_submission=has_submission, 
                                             submission=submission, error='Please enter valid numeric values for amounts')
                    
                    if has_submission and submission and submission[9] == 'rejected':
                        update_submission(submission[0], authorized_person, appointed_person, salary, 
                                        travel_allowance, dearness_allowance, sales_target, remarks)
                    elif not has_submission:
                        create_submission(user_id, authorized_person, appointed_person, salary, 
                                        travel_allowance, dearness_allowance, sales_target, remarks)
                    else:
                        return render_template('dashboard.html', user=user, has_submission=has_submission, 
                                             submission=submission, error='You can only resubmit if your previous submission was rejected')
                    
                    has_submission = user_has_submission(user_id)
                    submission = get_user_submission(user_id) if has_submission else None
                except Exception as e:
                    return render_template('dashboard.html', user=user, has_submission=has_submission, 
                                         submission=submission, error='An error occurred while saving your submission. Please try again.')
        
        return render_template('dashboard.html', user=user, has_submission=has_submission, submission=submission)
    
    except Exception as e:
        return render_template('error.html', error='An unexpected error occurred. Please try logging in again.'), 500

@app.route('/logout')
def logout():
    session.clear()
    return redirect('/login')

@app.route('/home')
def home():
    if 'user_id' not in session:
        return redirect('/login')
    
    try:
        user_id = session['user_id']
        user = get_user(user_id)
        if not user:
            session.clear()
            return redirect('/login')
        
        has_submission = user_has_submission(user_id)
        submission = get_user_submission(user_id) if has_submission else None
        
        return render_template('home.html', user=user, has_submission=has_submission, submission=submission)
    except Exception as e:
        return render_template('error.html', error='An error occurred. Please try again.'), 500

@app.route('/profile', methods=['GET', 'POST'])
def profile():
    if 'user_id' not in session:
        return redirect('/login')
    
    try:
        user_id = session['user_id']
        user = get_user(user_id)
        
        if not user:
            session.clear()
            return redirect('/login')
        
        if request.method == 'POST':
            try:
                full_name = request.form.get('full_name', '').strip()
                phone = request.form.get('phone', '').strip()
                location = request.form.get('location', '').strip()
                designation = request.form.get('designation', '').strip()
                
                if not all([full_name, phone, location, designation]):
                    return render_template('profile.html', user=user, error='All fields are required', states=INDIAN_STATES)
                
                if len(phone) < 10:
                    return render_template('profile.html', user=user, error='Phone number must be at least 10 digits', states=INDIAN_STATES)
                
                if update_user_profile(user_id, full_name, phone, location, designation):
                    session['full_name'] = full_name
                    user = get_user(user_id)
                    return render_template('profile.html', user=user, success='Profile updated successfully', states=INDIAN_STATES)
                else:
                    return render_template('profile.html', user=user, error='Failed to update profile', states=INDIAN_STATES)
            except Exception as e:
                return render_template('profile.html', user=user, error='An error occurred while updating profile', states=INDIAN_STATES)
        
        return render_template('profile.html', user=user, states=INDIAN_STATES)
    except Exception as e:
        return render_template('error.html', error='An error occurred. Please try again.'), 500

@app.route('/delete-submission/<int:submission_id>', methods=['POST'])
def delete_user_submission(submission_id):
    if 'user_id' not in session:
        return redirect('/login')
    
    try:
        submission = get_user_submission(session['user_id'])
        if submission and submission[0] == submission_id and submission[9] == 'rejected':
            delete_submission(submission_id)
            return redirect('/dashboard?success=Submission deleted successfully')
        else:
            return redirect('/dashboard?error=Can only delete rejected submissions')
    except Exception as e:
        return redirect('/dashboard?error=Failed to delete submission')

@app.route('/admin/login', methods=['GET', 'POST'])
def admin_login():
    if request.method == 'POST':
        try:
            username = request.form.get('username', '').strip()
            password = request.form.get('password', '').strip()
            
            if not username or not password:
                return render_template('admin_login.html', error='Username and password are required')
            
            if username == ADMIN_EMAIL and password == ADMIN_PASSWORD:
                session['admin_id'] = 'admin'
                session['admin_email'] = username
                return redirect('/admin/dashboard')
            else:
                return render_template('admin_login.html', error='Invalid credentials')
        except Exception as e:
            return render_template('admin_login.html', error='An error occurred during login. Please try again.')
    
    return render_template('admin_login.html')

@app.route('/admin/dashboard')
def admin_dashboard():
    if 'admin_id' not in session:
        return redirect('/admin/login')
    
    try:
        search_query = request.args.get('search', '').strip()
        if search_query:
            submissions = search_submissions(search_query)
        else:
            submissions = get_all_submissions()
        
        stats = get_submission_stats()
        return render_template('admin_dashboard.html', submissions=submissions, stats=stats, search_query=search_query)
    except Exception as e:
        return render_template('admin_dashboard.html', submissions=[], stats={'pending': 0, 'approved': 0, 'rejected': 0, 'total': 0}, error='An error occurred while loading submissions')

@app.route('/admin/approve/<int:submission_id>', methods=['POST'])
def admin_approve(submission_id):
    if 'admin_id' not in session:
        return redirect('/admin/login')
    
    try:
        approve_submission(submission_id)
        return redirect('/admin/dashboard')
    except Exception as e:
        return redirect('/admin/dashboard?error=Failed to approve submission')

@app.route('/admin/reject/<int:submission_id>', methods=['POST'])
def admin_reject(submission_id):
    if 'admin_id' not in session:
        return redirect('/admin/login')
    
    try:
        reject_submission(submission_id)
        return redirect('/admin/dashboard')
    except Exception as e:
        return redirect('/admin/dashboard?error=Failed to reject submission')

@app.route('/admin/download/csv')
def download_csv():
    if 'admin_id' not in session:
        return redirect('/admin/login')
    
    try:
        submissions = get_all_submissions()
        
        output = BytesIO()
        writer = csv.writer(output)
        
        writer.writerow(['ID', 'User Name', 'Email', 'Role', 'Authorized Person', 'Appointed Person', 
                         'Salary', 'Travel Allowance', 'Dearness Allowance', 'Sales Target', 'Remarks', 'Status', 'Submitted At'])
        
        for sub in submissions:
            writer.writerow([
                sub[0],
                sub[2],
                sub[3],
                sub[4],
                sub[5],
                sub[6],
                sub[7],
                sub[8],
                sub[9],
                sub[10],
                sub[11] or '',
                sub[12],
                sub[13]
            ])
        
        output.seek(0)
        return send_file(
            output,
            mimetype='text/csv',
            as_attachment=True,
            download_name=f'submissions_{datetime.now().strftime("%Y%m%d_%H%M%S")}.csv'
        )
    except Exception as e:
        return redirect('/admin/dashboard?error=Failed to download CSV')

@app.route('/admin/download/excel')
def download_excel():
    if 'admin_id' not in session:
        return redirect('/admin/login')
    
    try:
        submissions = get_all_submissions()
        
        wb = Workbook()
        ws = wb.active
        ws.title = "Submissions"
        
        headers = ['ID', 'User Name', 'Email', 'Role', 'Authorized Person', 'Appointed Person', 
                   'Salary', 'Travel Allowance', 'Dearness Allowance', 'Sales Target', 'Remarks', 'Status', 'Submitted At']
        ws.append(headers)
        
        for sub in submissions:
            ws.append([
                sub[0],
                sub[2],
                sub[3],
                sub[4],
                sub[5],
                sub[6],
                sub[7],
                sub[8],
                sub[9],
                sub[10],
                sub[11] or '',
                sub[12],
                sub[13]
            ])
        
        output = BytesIO()
        wb.save(output)
        output.seek(0)
        
        return send_file(
            output,
            mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
            as_attachment=True,
            download_name=f'submissions_{datetime.now().strftime("%Y%m%d_%H%M%S")}.xlsx'
        )
    except Exception as e:
        return redirect('/admin/dashboard?error=Failed to download Excel')

@app.route('/admin/logout')
def admin_logout():
    session.clear()
    return redirect('/admin/login')

@app.errorhandler(404)
def page_not_found(e):
    return render_template('error.html', error='Page not found'), 404

@app.errorhandler(500)
def internal_error(e):
    return render_template('error.html', error='An internal server error occurred. Please try again later.'), 500

if __name__ == '__main__':
    app.run(debug=False)
