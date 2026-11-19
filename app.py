from flask import Flask, render_template, request, redirect, url_for, session, flash, send_from_directory
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
from functools import wraps
from pathlib import Path
import sqlite3, os

ROOT = Path(__file__).resolve().parent
DB = ROOT / 'scholarships.db'
UPLOADS = ROOT / 'uploads'
UPLOADS.mkdir(exist_ok=True)
app = Flask(__name__)
app.secret_key = os.environ.get('SECRET_KEY', 'change-this-development-secret')
app.config['MAX_CONTENT_LENGTH'] = 12 * 1024 * 1024
ALLOWED = {'pdf','png','jpg','jpeg','doc','docx'}

def db():
    con = sqlite3.connect(DB); con.row_factory = sqlite3.Row; con.execute('PRAGMA foreign_keys = ON'); return con

def init_db():
    with db() as c:
        c.executescript("""
        CREATE TABLE IF NOT EXISTS users(id INTEGER PRIMARY KEY, name TEXT NOT NULL, email TEXT UNIQUE NOT NULL, password TEXT NOT NULL, role TEXT NOT NULL CHECK(role IN ('student','reviewer','admin')), student_id TEXT, program TEXT, year TEXT, gpa REAL, created_at TEXT DEFAULT CURRENT_TIMESTAMP);
        CREATE TABLE IF NOT EXISTS scholarships(id INTEGER PRIMARY KEY, title TEXT NOT NULL, category TEXT NOT NULL, description TEXT NOT NULL, amount REAL NOT NULL, deadline TEXT NOT NULL, eligibility TEXT NOT NULL, requirements TEXT NOT NULL, status TEXT NOT NULL DEFAULT 'Open', created_at TEXT DEFAULT CURRENT_TIMESTAMP);
        CREATE TABLE IF NOT EXISTS applications(id INTEGER PRIMARY KEY, scholarship_id INTEGER NOT NULL REFERENCES scholarships(id), student_id INTEGER NOT NULL REFERENCES users(id), essay TEXT NOT NULL, requested_amount REAL, status TEXT NOT NULL DEFAULT 'Submitted', staff_notes TEXT DEFAULT '', submitted_at TEXT DEFAULT CURRENT_TIMESTAMP, UNIQUE(scholarship_id, student_id));
        CREATE TABLE IF NOT EXISTS documents(id INTEGER PRIMARY KEY, application_id INTEGER NOT NULL REFERENCES applications(id) ON DELETE CASCADE, filename TEXT NOT NULL, original_name TEXT NOT NULL, kind TEXT NOT NULL, uploaded_at TEXT DEFAULT CURRENT_TIMESTAMP);
        CREATE TABLE IF NOT EXISTS reviews(id INTEGER PRIMARY KEY, application_id INTEGER NOT NULL REFERENCES applications(id) ON DELETE CASCADE, reviewer_id INTEGER NOT NULL REFERENCES users(id), decision TEXT NOT NULL, notes TEXT DEFAULT '', created_at TEXT DEFAULT CURRENT_TIMESTAMP);
        """)
        if not c.execute('SELECT id FROM users LIMIT 1').fetchone():
            c.execute('INSERT INTO users(name,email,password,role,student_id,program,year,gpa) VALUES(?,?,?,?,?,?,?,?)', ('Aarav Student','student@university.edu',generate_password_hash('Student123!'),'student','U2024001','Computer Science','2nd Year',3.72))
            c.execute('INSERT INTO users(name,email,password,role) VALUES(?,?,?,?)', ('Maya Reviewer','reviewer@university.edu',generate_password_hash('Reviewer123!'),'reviewer'))
            c.execute('INSERT INTO users(name,email,password,role) VALUES(?,?,?,?)', ('System Admin','admin@university.edu',generate_password_hash('Admin123!'),'admin'))
        if not c.execute('SELECT id FROM scholarships LIMIT 1').fetchone():
            rows=[('Merit Excellence Award','Merit','Recognizing students who combine strong academic results with meaningful contributions to campus life.',2500,'2027-01-31','Minimum GPA 3.5; enrolled full time.','Transcript, personal statement'),('Future Leaders Grant','Leadership','Support for students who have demonstrated leadership and service in their community.',1800,'2027-02-15','Open to all undergraduate years.','Personal statement, one reference'),('STEM Opportunity Scholarship','STEM','Helping promising STEM students focus on research, learning, and innovation.',3000,'2027-03-01','Studying a STEM program; minimum GPA 3.0.','Transcript, project summary')]
            c.executemany('INSERT INTO scholarships(title,category,description,amount,deadline,eligibility,requirements) VALUES(?,?,?,?,?,?,?)',rows)

def login_required(fn):
    @wraps(fn)
    def wrapped(*a, **kw):
        if 'user_id' not in session: return redirect(url_for('login'))
        return fn(*a, **kw)
    return wrapped

def staff_required(fn):
    @wraps(fn)
    @login_required
    def wrapped(*a, **kw):
        if session.get('role') not in ('reviewer','admin'):
            flash('Staff access is required.', 'error'); return redirect(url_for('dashboard'))
        return fn(*a, **kw)
    return wrapped

@app.context_processor
def common(): return {'current_user': session.get('name'), 'role': session.get('role')}

@app.route('/')
def index():
    if 'user_id' in session: return redirect(url_for('dashboard'))
    with db() as c: scholarships=c.execute("SELECT * FROM scholarships WHERE status='Open' ORDER BY deadline LIMIT 3").fetchall()
    return render_template('landing.html', scholarships=scholarships)

@app.route('/login', methods=['GET','POST'])
def login():
    if request.method=='POST':
        email=request.form.get('email','').strip().lower(); password=request.form.get('password','')
        with db() as c: user=c.execute('SELECT * FROM users WHERE email=?',(email,)).fetchone()
        if user and check_password_hash(user['password'],password):
            session.clear(); session.update(user_id=user['id'],name=user['name'],role=user['role']); return redirect(url_for('dashboard'))
        flash('Email or password was not recognized.','error')
    return render_template('login.html')

@app.route('/register', methods=['GET','POST'])
def register():
    if request.method=='POST':
        name=request.form.get('name','').strip(); email=request.form.get('email','').strip().lower(); password=request.form.get('password',''); student_id=request.form.get('student_id','').strip()
        if len(password)<8: flash('Choose a password with at least 8 characters.','error')
        else:
            try:
                with db() as c: c.execute('INSERT INTO users(name,email,password,role,student_id,program,year,gpa) VALUES(?,?,?,?,?,?,?,?)',(name,email,generate_password_hash(password),'student',student_id,request.form.get('program',''),request.form.get('year',''),float(request.form.get('gpa') or 0)))
                flash('Account created. Sign in to continue.','success'); return redirect(url_for('login'))
            except sqlite3.IntegrityError: flash('An account with that email already exists.','error')
    return render_template('register.html')

@app.route('/logout')
def logout(): session.clear(); return redirect(url_for('index'))

@app.route('/dashboard')
@login_required
def dashboard():
    with db() as c:
        if session['role']=='student':
            apps=c.execute('SELECT a.*,s.title,s.amount,s.deadline FROM applications a JOIN scholarships s ON s.id=a.scholarship_id WHERE a.student_id=? ORDER BY a.submitted_at DESC',(session['user_id'],)).fetchall()
            counts=c.execute("SELECT COUNT(*) total, SUM(status='Approved') approved, SUM(status IN ('Submitted','Under Review','Needs Information')) active FROM applications WHERE student_id=?",(session['user_id'],)).fetchone()
            scholarships=c.execute("SELECT * FROM scholarships WHERE status='Open' ORDER BY deadline LIMIT 4").fetchall()
            return render_template('student_dashboard.html',apps=apps,counts=counts,scholarships=scholarships)
        stats=c.execute("SELECT COUNT(*) total, SUM(status='Submitted') submitted, SUM(status='Under Review') reviewing, SUM(status='Approved') approved FROM applications").fetchone()
        apps=c.execute("SELECT a.*,s.title,u.name student_name,u.student_id campus_id,u.program,u.gpa FROM applications a JOIN scholarships s ON s.id=a.scholarship_id JOIN users u ON u.id=a.student_id ORDER BY CASE a.status WHEN 'Submitted' THEN 0 WHEN 'Under Review' THEN 1 ELSE 2 END,a.submitted_at DESC LIMIT 12").fetchall()
        scholarships=c.execute('SELECT * FROM scholarships ORDER BY created_at DESC').fetchall()
        return render_template('staff_dashboard.html',apps=apps,stats=stats,scholarships=scholarships)

@app.route('/scholarships')
@login_required
def scholarships():
    q=request.args.get('q','').strip(); category=request.args.get('category','')
    with db() as c:
        rows=c.execute("SELECT s.*, (SELECT COUNT(*) FROM applications a WHERE a.scholarship_id=s.id AND a.student_id=?) applied FROM scholarships s WHERE (?='' OR s.title LIKE '%'||?||'%' OR s.description LIKE '%'||?||'%') AND (?='' OR s.category=?) ORDER BY CASE status WHEN 'Open' THEN 0 ELSE 1 END,deadline",(session['user_id'],q,q,q,category,category)).fetchall()
        cats=c.execute('SELECT DISTINCT category FROM scholarships ORDER BY category').fetchall()
    return render_template('scholarships.html',scholarships=rows,categories=cats,q=q,category=category)

@app.route('/scholarships/new',methods=['POST'])
@staff_required
def create_scholarship():
    try:
        with db() as c: c.execute('INSERT INTO scholarships(title,category,description,amount,deadline,eligibility,requirements,status) VALUES(?,?,?,?,?,?,?,?)',(request.form['title'],request.form['category'],request.form['description'],float(request.form['amount']),request.form['deadline'],request.form['eligibility'],request.form['requirements'],request.form.get('status','Open')))
        flash('Scholarship published.','success')
    except (ValueError,KeyError): flash('Please complete all scholarship fields.','error')
    return redirect(url_for('dashboard'))

@app.route('/scholarships/<int:sid>')
@login_required
def scholarship_detail(sid):
    with db() as c:
        s=c.execute('SELECT * FROM scholarships WHERE id=?',(sid,)).fetchone()
        if not s: return 'Scholarship not found',404
        applied=c.execute('SELECT id FROM applications WHERE scholarship_id=? AND student_id=?',(sid,session['user_id'])).fetchone() if session['role']=='student' else None
    return render_template('scholarship_detail.html',s=s,applied=applied)

@app.route('/scholarships/<int:sid>/apply',methods=['POST'])
@login_required
def apply(sid):
    if session['role']!='student': flash('Only students can apply.','error'); return redirect(url_for('scholarship_detail',sid=sid))
    with db() as c:
        s=c.execute("SELECT * FROM scholarships WHERE id=? AND status='Open'",(sid,)).fetchone()
        if not s: flash('This scholarship is closed.','error'); return redirect(url_for('scholarships'))
        try:
            cur=c.execute('INSERT INTO applications(scholarship_id,student_id,essay,requested_amount) VALUES(?,?,?,?)',(sid,session['user_id'],request.form.get('essay','').strip(),float(request.form.get('requested_amount') or s['amount'])))
            aid=cur.lastrowid
            for f in request.files.getlist('documents'):
                if f and f.filename and '.' in f.filename and f.filename.rsplit('.',1)[1].lower() in ALLOWED:
                    safe=secure_filename(f.filename); stored=f'{aid}_{os.urandom(5).hex()}_{safe}'; f.save(UPLOADS/stored)
                    c.execute('INSERT INTO documents(application_id,filename,original_name,kind) VALUES(?,?,?,?)',(aid,stored,f.filename,request.form.get('document_kind','Supporting document')))
            flash('Application submitted successfully.','success')
        except sqlite3.IntegrityError: flash('You have already applied for this scholarship.','error')
    return redirect(url_for('dashboard'))

@app.route('/applications/<int:aid>/status',methods=['POST'])
@staff_required
def update_application(aid):
    status=request.form.get('status'); allowed={'Under Review','Needs Information','Approved','Rejected','Submitted'}
    if status not in allowed: flash('Invalid status.','error'); return redirect(url_for('dashboard'))
    with db() as c:
        if not c.execute('SELECT id FROM applications WHERE id=?',(aid,)).fetchone(): return 'Application not found',404
        notes=request.form.get('staff_notes',''); c.execute('UPDATE applications SET status=?,staff_notes=? WHERE id=?',(status,notes,aid))
        c.execute('INSERT INTO reviews(application_id,reviewer_id,decision,notes) VALUES(?,?,?,?)',(aid,session['user_id'],status,notes))
    flash('Application review saved.','success'); return redirect(url_for('dashboard'))

@app.route('/applications/<int:aid>/documents')
@login_required
def documents(aid):
    with db() as c:
        approw=c.execute('SELECT * FROM applications WHERE id=?',(aid,)).fetchone()
        if not approw: return 'Application not found',404
        if session['role']=='student' and approw['student_id']!=session['user_id']: return 'Forbidden',403
        docs=c.execute('SELECT * FROM documents WHERE application_id=?',(aid,)).fetchall()
    return render_template('documents.html',docs=docs,aid=aid)

@app.route('/uploads/<path:filename>')
@login_required
def uploaded_file(filename): return send_from_directory(UPLOADS,filename,as_attachment=True)

@app.route('/health')
def health(): return {'status':'ok'}

init_db()
if __name__=='__main__': app.run(debug=os.environ.get('FLASK_DEBUG')=='1',port=int(os.environ.get('PORT',5000)))

