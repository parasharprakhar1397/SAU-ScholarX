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
app.secret_key = os.environ.get('SECRET_KEY', 'sau-scholarx-secure-academic-secret-key-2026')
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024
ALLOWED = {'pdf','png','jpg','jpeg','doc','docx'}

EXCHANGE_RATE = 91  # Locked exchange rate: 1 USD = 91 INR for Academic Session 2026–27

def format_inr(val):
    if val is None:
        return "₹0"
    n = int(round(val))
    s = str(n)
    if len(s) <= 3:
        return f"₹{s}"
    last3 = s[-3:]
    rest = s[:-3]
    groups = []
    while len(rest) > 2:
        groups.insert(0, rest[-2:])
        rest = rest[:-2]
    if rest:
        groups.insert(0, rest)
    return f"₹{','.join(groups)},{last3}"

@app.template_filter('inr')
def inr_filter(usd):
    return format_inr((usd or 0) * EXCHANGE_RATE)

@app.template_filter('dual_curr')
def dual_curr_filter(usd):
    u = usd or 0
    return f"${u:,.2f} ({format_inr(u * EXCHANGE_RATE)})"

@app.template_filter('dual_heading')
def dual_heading_filter(usd):
    u = usd or 0
    return f"${u:,.0f} / {format_inr(u * EXCHANGE_RATE)}"

def student_avatar(val):
    if not val:
        return 'images/scholar-male.jpeg'
    s = str(val).lower()
    if 'pooja' in s or 'shrestha' in s or 'female' in s:
        return 'images/scholar-female.jpeg'
    elif 'aarav' in s or 'sharma' in s:
        return 'images/scholar-male.jpeg'
    elif 'tariqul' in s or 'islam' in s:
        return 'images/scholar-portrait.jpeg'
    elif 'maya' in s or 'raghavan' in s or 'admin' in s or 'reviewer' in s:
        return 'images/sau-logo.jpeg'
    return 'images/scholar-male.jpeg'

@app.template_filter('avatar')
def avatar_filter(val):
    return student_avatar(val)

def db():
    con = sqlite3.connect(DB)
    con.row_factory = sqlite3.Row
    con.execute('PRAGMA foreign_keys = ON')
    return con

def init_db():
    with db() as c:
        c.executescript("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY,
            name TEXT NOT NULL,
            email TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL,
            role TEXT NOT NULL CHECK(role IN ('student','reviewer','admin')),
            student_id TEXT,
            program TEXT,
            faculty TEXT DEFAULT 'Faculty of Mathematics and Computer Science',
            country TEXT DEFAULT 'India',
            year TEXT,
            gpa REAL,
            hostel_resident TEXT DEFAULT 'Yes (Hostel Block A, Maidan Garhi Campus)',
            created_at TEXT DEFAULT CURRENT_TIMESTAMP
        );
        CREATE TABLE IF NOT EXISTS scholarships (
            id INTEGER PRIMARY KEY,
            title TEXT NOT NULL,
            category TEXT NOT NULL,
            description TEXT NOT NULL,
            amount REAL NOT NULL,
            deadline TEXT NOT NULL,
            eligibility TEXT NOT NULL,
            requirements TEXT NOT NULL,
            status TEXT NOT NULL DEFAULT 'Open',
            created_at TEXT DEFAULT CURRENT_TIMESTAMP
        );
        CREATE TABLE IF NOT EXISTS applications (
            id INTEGER PRIMARY KEY,
            application_no TEXT DEFAULT '',
            academic_year TEXT DEFAULT '2026-2027',
            scholarship_id INTEGER NOT NULL REFERENCES scholarships(id),
            student_id INTEGER NOT NULL REFERENCES users(id),
            essay TEXT NOT NULL,
            requested_amount REAL,
            status TEXT NOT NULL DEFAULT 'Submitted',
            staff_notes TEXT DEFAULT '',
            submitted_at TEXT DEFAULT CURRENT_TIMESTAMP,
            UNIQUE(scholarship_id, student_id)
        );
        CREATE TABLE IF NOT EXISTS documents (
            id INTEGER PRIMARY KEY,
            application_id INTEGER NOT NULL REFERENCES applications(id) ON DELETE CASCADE,
            filename TEXT NOT NULL,
            original_name TEXT NOT NULL,
            kind TEXT NOT NULL,
            uploaded_at TEXT DEFAULT CURRENT_TIMESTAMP
        );
        CREATE TABLE IF NOT EXISTS reviews (
            id INTEGER PRIMARY KEY,
            application_id INTEGER NOT NULL REFERENCES applications(id) ON DELETE CASCADE,
            reviewer_id INTEGER NOT NULL REFERENCES users(id),
            decision TEXT NOT NULL,
            notes TEXT DEFAULT '',
            created_at TEXT DEFAULT CURRENT_TIMESTAMP
        );
        """)
        # Ensure schema migrations if existing db lacks columns
        u_cols = [r[1] for r in c.execute('PRAGMA table_info(users)').fetchall()]
        if 'faculty' not in u_cols: c.execute("ALTER TABLE users ADD COLUMN faculty TEXT DEFAULT 'Faculty of Mathematics and Computer Science'")
        if 'country' not in u_cols: c.execute("ALTER TABLE users ADD COLUMN country TEXT DEFAULT 'India'")
        if 'hostel_resident' not in u_cols: c.execute("ALTER TABLE users ADD COLUMN hostel_resident TEXT DEFAULT 'Yes (Hostel Block A, Maidan Garhi Campus)'")

        a_cols = [r[1] for r in c.execute('PRAGMA table_info(applications)').fetchall()]
        if 'application_no' not in a_cols: c.execute("ALTER TABLE applications ADD COLUMN application_no TEXT DEFAULT ''")
        if 'academic_year' not in a_cols: c.execute("ALTER TABLE applications ADD COLUMN academic_year TEXT DEFAULT '2026-2027'")

        # Automatic initial seed if tables are newly created
        if c.execute("SELECT COUNT(*) FROM scholarships").fetchone()[0] == 0:
            c.executemany("""
                INSERT INTO scholarships (id, title, category, description, amount, deadline, eligibility, requirements, status)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, [
                (1, 'SAARC-India Silver Jubilee Scholarship (SJS)', 'Inter-Governmental', 'Prestigious inter-governmental fellowship instituted under the SAARC framework, providing full tuition waiver, monthly living allowance, and hostel accommodation.', 4200.0, '2027-03-31', 'Top 5% Entrance Rank & CGPA >= 8.75/10.00 across any postgraduate degree program.', 'Annexure-B Bonafide Certificate, Previous Degree Marksheets, SAARC Passport / Citizenship ID.', 'Open'),
                (2, "SAU President's Fellowship for Doctoral Scholars", 'Doctoral Fellowship', "Premier institutional fellowship granted by the President of SAU to exceptional research scholars admitted to Ph.D. programs across all faculties.", 4800.0, '2027-04-15', 'Full-time enrolled Ph.D. candidate with approved synopsis and CGPA >= 8.50/10.00 in coursework.', 'Annexure-C Research Synopsis Endorsement, Supervisor Recommendation, Coursework Marksheet.', 'Open'),
                (3, 'SAU Financial Support Scheme (FSS - Need-cum-Merit)', 'Financial Support', 'Direct fee concession and living subsidy for scholars from underprivileged socio-economic backgrounds across SAARC nations.', 2400.0, '2027-03-15', 'Annual household income below USD $4,000 / INR 3,64,000 and minimum CGPA of 6.50/10.00.', 'Annexure-A Income Certificate Affidavit, Revenue Authority Endorsement, Current Semester Marksheet.', 'Open'),
                (4, 'Faculty of Mathematics & Computer Science (FMCS) Technical Research Grant', 'Departmental Research', 'Specialized grant for postgraduate students and doctoral fellows conducting computational algorithms, artificial intelligence, and systems research.', 3500.0, '2027-04-30', 'Enrolled M.Tech/Ph.D. in FMCS with CGPA >= 8.00/10.00 and documented research project proposal.', 'Technical Synopsis, Departmental Bonafide, GitHub Repository / Publications portfolio.', 'Open'),
                (5, 'SAU Semester Merit Scholarship (Top 10% Decile)', 'Academic Merit', 'Merit concession awarded semester-wise to students ranking in the top 10 percentile of their respective academic departments.', 1800.0, '2027-02-28', 'SGPA >= 8.50/10.00 in the immediate previous semester with zero backlogs or disciplinary flags.', 'Previous Semester Grade Card, Dean recommendation.', 'Open'),
                (6, 'Special Regional Representation Quota Grant (Maldives, Bhutan, Afghanistan)', 'Regional Quota', 'Institutional grant ensuring balanced South Asian representation, assisting scholars from smaller SAARC member states with travel, living, and educational allowances.', 3000.0, '2027-05-15', 'Citizens of Afghanistan, Bhutan, or Maldives enrolled in any Master’s or Ph.D. program with CGPA >= 7.00/10.00.', 'Valid Passport of eligible nation, SAU Enrolment Letter, Proof of Residence.', 'Open'),
                (7, 'Faculty of Life Sciences & Biotechnology (FLSB) Research Fellowship', 'Life Sciences & Biotech', 'Research stipend supporting laboratory bench fees, molecular biology consumables, and international conference travel for biotechnology scholars.', 3200.0, '2027-05-01', 'M.Sc or Ph.D. students in FLSB with CGPA >= 8.25/10.00 and active laboratory experimental assignment.', 'Laboratory Synopsis, Departmental Attendance Record, Faculty Advisor Endorsement.', 'Open'),
                (8, 'Faculty of Legal Studies (FLS) International Law & Policy Fellowship', 'Legal Studies & Policy', 'Fellowship promoting comparative South Asian constitutional law, human rights, and public international policy research.', 2800.0, '2027-04-10', 'LL.M or Ph.D. Law scholars with CGPA >= 8.00/10.00 and active research docket.', 'Draft Research Paper, HoD Recommendation, Enrolment Verification.', 'Open')
            ])

        if c.execute("SELECT COUNT(*) FROM users").fetchone()[0] == 0:
            c.executemany("""
                INSERT INTO users (id, name, email, password, role, student_id, program, faculty, country, year, gpa, hostel_resident)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, [
                (1, 'Aarav Sharma', 'student@university.edu', generate_password_hash('Student123!'), 'student', 'SAU/2024/CSE/019', 'M.Tech Computer Science & Engineering', 'Faculty of Mathematics and Computer Science', 'India', '2nd Year', 9.12, 'Yes (Hostel Block A, Maidan Garhi Campus)'),
                (2, 'Prof. Maya Sen', 'reviewer@university.edu', generate_password_hash('Reviewer123!'), 'reviewer', 'FAC/FMCS/004', 'Faculty of Mathematics & Computer Science', 'Faculty of Mathematics and Computer Science', 'India', 'Faculty', None, 'Yes (Hostel Block A, Maidan Garhi Campus)'),
                (3, 'Dr. K. Raghavan', 'admin@university.edu', generate_password_hash('Admin123!'), 'admin', 'ADM/DIR/001', 'Directorate of Student Affairs & Financial Aid', 'Office of the Dean, Student Affairs', 'India', 'Dean', None, 'Yes (Hostel Block A, Maidan Garhi Campus)'),
                (4, 'Pooja Shrestha', 'pooja.shrestha@sau.ac.in', generate_password_hash('Student123!'), 'student', 'SAU/2024/LSB/007', 'M.Sc Biotechnology', 'Faculty of Life Sciences and Biotechnology', 'Nepal', '2nd Year', 8.85, 'Yes (Hostel Block B, Maidan Garhi Campus)'),
                (5, 'Tariqul Islam', 'tariqul.islam@sau.ac.in', generate_password_hash('Student123!'), 'student', 'SAU/2024/ECO/014', 'M.A. Economics', 'Faculty of Economics', 'Bangladesh', '1st Year', 8.45, 'Yes (Hostel Block A, Maidan Garhi Campus)')
            ])

        if c.execute("SELECT COUNT(*) FROM applications").fetchone()[0] == 0:
            c.executemany("""
                INSERT INTO applications (id, application_no, academic_year, scholarship_id, student_id, essay, requested_amount, status, staff_notes)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, [
                (1, 'SAU-SCH-2026-0019', '2026-2027', 1, 1, 'Applying for the SAARC-India Silver Jubilee Scholarship to support my M.Tech CSE research into high-performance distributed systems. Maintaining a 9.12/10.00 CGPA.', 4200.0, 'Approved', 'Verified by Faculty Committee. Sanction confirmed by SCSFA Central Board at locked rate ₹91/USD.'),
                (2, 'SAU-SCH-2026-0034', '2026-2027', 4, 1, 'Requesting departmental assistance for GPU computing cloud credits and IEEE conference registration.', 3500.0, 'Under Review', 'Departmental Scrutiny Committee currently evaluating synopsis.'),
                (3, 'SAU-SCH-2026-0007', '2026-2027', 2, 4, 'Applying for President’s Doctoral Fellowship for genomic data sequencing in the Faculty of Life Sciences & Biotechnology.', 4800.0, 'Submitted', 'Pending initial verification by Dean of Student Affairs.')
            ])

def login_required(fn):
    @wraps(fn)
    def wrapped(*a, **kw):
        if 'user_id' not in session:
            flash('Please sign in with your official university credentials.', 'info')
            return redirect(url_for('login'))
        return fn(*a, **kw)
    return wrapped

def staff_required(fn):
    @wraps(fn)
    @login_required
    def wrapped(*a, **kw):
        if session.get('role') not in ('reviewer','admin'):
            flash('Access Restricted: University Committee or Administrative credentials required.', 'error')
            return redirect(url_for('dashboard'))
        return fn(*a, **kw)
    return wrapped

@app.context_processor
def common():
    profile = None
    if 'user_id' in session:
        with db() as c:
            profile = c.execute('SELECT * FROM users WHERE id=?', (session['user_id'],)).fetchone()
    return {
        'current_user': session.get('name'),
        'role': session.get('role'),
        'user_profile': profile,
        'EXCHANGE_RATE': EXCHANGE_RATE,
        'EXCHANGE_NOTE': 'Official Locked Rate: 1 USD = ₹91.00 INR (Session 2026–27)',
        'UNIVERSITY_ADDRESS': 'South Asian University, Gaushala Road, Maidan Garhi, New Delhi – 110068, India',
        'UNIVERSITY_PHONE': '+91 (11) 3565 6600',
        'UNIVERSITY_PBX': '+91 (11) 3565 6500',
        'UNIVERSITY_PRESIDENT_PHONE': '+91 (11) 3565 6595',
        'UNIVERSITY_EMAIL': 'financial-aid@sau.int',
        'format_inr': format_inr,
        'student_avatar': student_avatar,
        'saarc_countries': [
            {'name': 'Afghanistan', 'flag': '🇦🇫', 'code': 'AF'},
            {'name': 'Bangladesh', 'flag': '🇧🇩', 'code': 'BD'},
            {'name': 'Bhutan', 'flag': '🇧🇹', 'code': 'BT'},
            {'name': 'India', 'flag': '🇮🇳', 'code': 'IN'},
            {'name': 'Maldives', 'flag': '🇲🇻', 'code': 'MV'},
            {'name': 'Nepal', 'flag': '🇳🇵', 'code': 'NP'},
            {'name': 'Pakistan', 'flag': '🇵🇰', 'code': 'PK'},
            {'name': 'Sri Lanka', 'flag': '🇱🇰', 'code': 'LK'}
        ],
        'sau_faculties': [
            'Faculty of Mathematics and Computer Science',
            'Faculty of Life Sciences and Biotechnology',
            'Faculty of Economics',
            'Faculty of Legal Studies',
            'Faculty of International Studies',
            'Faculty of Social Sciences',
            'Faculty of Physical & Chemical Sciences'
        ]
    }

@app.route('/')
def index():
    if 'user_id' in session:
        return redirect(url_for('dashboard'))
    with db() as c:
        scholarships = c.execute("SELECT * FROM scholarships WHERE status='Open' ORDER BY deadline LIMIT 4").fetchall()
        total_schemes = c.execute("SELECT COUNT(*) FROM scholarships").fetchone()[0]
        total_students = c.execute("SELECT COUNT(*) FROM users WHERE role='student'").fetchone()[0]
    return render_template('landing.html', scholarships=scholarships, total_schemes=total_schemes, total_students=total_students)

@app.route('/guidelines')
def guidelines():
    return render_template('guidelines.html')

@app.route('/login', methods=['GET','POST'])
def login():
    if request.method == 'POST':
        email = request.form.get('email','').strip().lower()
        password = request.form.get('password','')
        with db() as c:
            user = c.execute('SELECT * FROM users WHERE email=?', (email,)).fetchone()
        if user and check_password_hash(user['password'], password):
            session.clear()
            session.update(user_id=user['id'], name=user['name'], role=user['role'])
            flash(f'Signed in successfully as {user["name"]} ({user["role"].upper()}).', 'success')
            return redirect(url_for('dashboard'))
        flash('Authentication failed: Invalid institutional email or password.', 'error')
    return render_template('login.html')

@app.route('/register', methods=['GET','POST'])
def register():
    if request.method == 'POST':
        name = request.form.get('name','').strip()
        email = request.form.get('email','').strip().lower()
        password = request.form.get('password','')
        student_id = request.form.get('student_id','').strip()
        program = request.form.get('program','').strip()
        faculty = request.form.get('faculty','Faculty of Mathematics and Computer Science')
        country = request.form.get('country','India')
        year = request.form.get('year','1st Year')
        hostel = request.form.get('hostel_resident','Yes (Hostel Block A, Maidan Garhi Campus)')
        try:
            gpa = float(request.form.get('gpa') or 0.0)
        except ValueError:
            gpa = 0.0

        if len(password) < 8:
            flash('Security Requirement: Password must contain at least 8 characters.', 'error')
        elif gpa < 0.0 or gpa > 10.0:
            flash('Grading Standard: Cumulative CGPA must be on a 10.00 scale (between 0.00 and 10.00).', 'error')
        else:
            try:
                with db() as c:
                    c.execute('''
                    INSERT INTO users (name, email, password, role, student_id, program, faculty, country, year, gpa, hostel_resident)
                    VALUES (?, ?, ?, 'student', ?, ?, ?, ?, ?, ?, ?)
                    ''', (name, email, generate_password_hash(password), student_id, program, faculty, country, year, gpa, hostel))
                flash('Student registration successful. Please sign in with your institutional credentials.', 'success')
                return redirect(url_for('login'))
            except sqlite3.IntegrityError:
                flash('An account with this institutional email address is already registered.', 'error')
    return render_template('register.html')

@app.route('/logout')
def logout():
    session.clear()
    flash('You have been securely signed out of the SAU portal.', 'info')
    return redirect(url_for('index'))

@app.route('/dashboard')
@login_required
def dashboard():
    with db() as c:
        if session['role'] == 'student':
            apps = c.execute('''
                SELECT a.*, s.title, s.category, s.amount, s.deadline 
                FROM applications a 
                JOIN scholarships s ON s.id = a.scholarship_id 
                WHERE a.student_id = ? 
                ORDER BY a.submitted_at DESC
            ''', (session['user_id'],)).fetchall()
            
            counts = c.execute('''
                SELECT 
                    COUNT(*) as total,
                    COALESCE(SUM(status='Approved'), 0) as approved,
                    COALESCE(SUM(status IN ('Submitted','Under Review','Needs Information')), 0) as active
                FROM applications 
                WHERE student_id = ?
            ''', (session['user_id'],)).fetchone()
            
            scholarships = c.execute("SELECT * FROM scholarships WHERE status='Open' ORDER BY deadline LIMIT 4").fetchall()
            return render_template('student_dashboard.html', apps=apps, counts=counts, scholarships=scholarships)

        # Reviewer and Administrator View
        status_filter = request.args.get('status', '').strip()
        faculty_filter = request.args.get('faculty', '').strip()
        country_filter = request.args.get('country', '').strip()

        stats = c.execute('''
            SELECT 
                COUNT(*) as total,
                COALESCE(SUM(status='Submitted'), 0) as submitted,
                COALESCE(SUM(status='Under Review'), 0) as reviewing,
                COALESCE(SUM(status='Approved'), 0) as approved
            FROM applications
        ''').fetchone()

        query = '''
            SELECT a.*, s.title, s.category, u.name as student_name, u.student_id as campus_id, 
                   u.program, u.faculty, u.country, u.gpa, u.hostel_resident
            FROM applications a 
            JOIN scholarships s ON s.id = a.scholarship_id 
            JOIN users u ON u.id = a.student_id 
            WHERE (? = '' OR a.status = ?)
              AND (? = '' OR u.faculty = ?)
              AND (? = '' OR u.country = ?)
            ORDER BY 
                CASE a.status 
                    WHEN 'Submitted' THEN 0 
                    WHEN 'Under Review' THEN 1 
                    WHEN 'Needs Information' THEN 2 
                    WHEN 'Approved' THEN 3 
                    ELSE 4 
                END,
                a.submitted_at DESC
        '''
        apps = c.execute(query, (status_filter, status_filter, faculty_filter, faculty_filter, country_filter, country_filter)).fetchall()
        scholarships = c.execute('SELECT * FROM scholarships ORDER BY created_at DESC').fetchall()
        
        return render_template('staff_dashboard.html', apps=apps, stats=stats, scholarships=scholarships,
                               status_filter=status_filter, faculty_filter=faculty_filter, country_filter=country_filter)

@app.route('/scholarships')
@login_required
def scholarships():
    q = request.args.get('q','').strip()
    category = request.args.get('category','')
    with db() as c:
        rows = c.execute('''
            SELECT s.*, 
                   (SELECT COUNT(*) FROM applications a WHERE a.scholarship_id=s.id AND a.student_id=?) as applied 
            FROM scholarships s 
            WHERE (?='' OR s.title LIKE '%'||?||'%' OR s.description LIKE '%'||?||'%' OR s.eligibility LIKE '%'||?||'%') 
              AND (?='' OR s.category=?) 
            ORDER BY CASE status WHEN 'Open' THEN 0 ELSE 1 END, deadline
        ''', (session['user_id'], q, q, q, q, category, category)).fetchall()
        cats = c.execute('SELECT DISTINCT category FROM scholarships ORDER BY category').fetchall()
    return render_template('scholarships.html', scholarships=rows, categories=cats, q=q, category=category)

@app.route('/scholarships/new', methods=['POST'])
@staff_required
def create_scholarship():
    try:
        title = request.form['title'].strip()
        category = request.form['category'].strip()
        description = request.form['description'].strip()
        amount = float(request.form['amount'])
        deadline = request.form['deadline'].strip()
        eligibility = request.form['eligibility'].strip()
        requirements = request.form['requirements'].strip()
        status = request.form.get('status', 'Open')

        with db() as c:
            c.execute('''
            INSERT INTO scholarships (title, category, description, amount, deadline, eligibility, requirements, status)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            ''', (title, category, description, amount, deadline, eligibility, requirements, status))
        inr_val = format_inr(amount * EXCHANGE_RATE)
        flash(f'Scholarship scheme "{title}" published with value ${amount:,.2f} ({inr_val}).', 'success')
    except (ValueError, KeyError):
        flash('Unable to publish: Please verify all mandatory scholarship fields.', 'error')
    return redirect(url_for('dashboard'))

@app.route('/scholarships/<int:sid>')
@login_required
def scholarship_detail(sid):
    with db() as c:
        s = c.execute('SELECT * FROM scholarships WHERE id=?', (sid,)).fetchone()
        if not s:
            flash('Requested scholarship ordinance not found.', 'error')
            return redirect(url_for('scholarships'))
        applied = None
        if session['role'] == 'student':
            applied = c.execute('SELECT * FROM applications WHERE scholarship_id=? AND student_id=?', (sid, session['user_id'])).fetchone()
    return render_template('scholarship_detail.html', s=s, applied=applied)

@app.route('/scholarships/<int:sid>/apply', methods=['POST'])
@login_required
def apply(sid):
    if session['role'] != 'student':
        flash('Unauthorized: Applications can only be lodged by enrolled university students.', 'error')
        return redirect(url_for('scholarship_detail', sid=sid))

    with db() as c:
        s = c.execute("SELECT * FROM scholarships WHERE id=? AND status='Open'", (sid,)).fetchone()
        if not s:
            flash('This scholarship ordinance is currently closed to new submissions.', 'error')
            return redirect(url_for('scholarships'))

        try:
            essay = request.form.get('essay','').strip()
            requested_amount = float(request.form.get('requested_amount') or s['amount'])
            
            cur = c.execute('''
            INSERT INTO applications (scholarship_id, student_id, essay, requested_amount, status)
            VALUES (?, ?, ?, ?, 'Submitted')
            ''', (sid, session['user_id'], essay, requested_amount))
            aid = cur.lastrowid
            
            # Generate official SAU application reference number
            app_no = f"SAU-SCH-2026-{aid:04d}"
            c.execute("UPDATE applications SET application_no=? WHERE id=?", (app_no, aid))

            # Handle file attachments
            for f in request.files.getlist('documents'):
                if f and f.filename and '.' in f.filename and f.filename.rsplit('.',1)[1].lower() in ALLOWED:
                    safe = secure_filename(f.filename) or 'supporting_doc.pdf'
                    stored = f'{aid}_{os.urandom(5).hex()}_{safe}'
                    f.save(UPLOADS / stored)
                    kind = request.form.get('document_kind', 'Supporting Document')
                    c.execute('INSERT INTO documents (application_id, filename, original_name, kind) VALUES (?, ?, ?, ?)',
                              (aid, stored, f.filename, kind))

            inr_val = format_inr(requested_amount * EXCHANGE_RATE)
            flash(f'Application successfully lodged ({app_no}) for ${requested_amount:,.2f} ({inr_val} at locked rate ₹91/USD).', 'success')
        except sqlite3.IntegrityError:
            flash('Duplicate Submission Notice: You have already filed an application for this scholarship scheme.', 'error')
    return redirect(url_for('dashboard'))

@app.route('/applications/<int:aid>/status', methods=['POST'])
@staff_required
def update_application(aid):
    status = request.form.get('status')
    allowed = {'Under Review', 'Needs Information', 'Approved', 'Rejected', 'Submitted'}
    if status not in allowed:
        flash('Invalid Committee Decision Parameter.', 'error')
        return redirect(url_for('dashboard'))

    with db() as c:
        app_row = c.execute('SELECT * FROM applications WHERE id=?', (aid,)).fetchone()
        if not app_row:
            flash('Application dossier not found.', 'error')
            return redirect(url_for('dashboard'))

        notes = request.form.get('staff_notes', '').strip()
        c.execute('UPDATE applications SET status=?, staff_notes=? WHERE id=?', (status, notes, aid))
        c.execute('INSERT INTO reviews (application_id, reviewer_id, decision, notes) VALUES (?, ?, ?, ?)',
                  (aid, session['user_id'], status, notes))

    flash(f'Committee decision for application #{aid} successfully committed.', 'success')
    return redirect(url_for('dashboard'))

@app.route('/applications/<int:aid>/slip')
@login_required
def application_slip(aid):
    with db() as c:
        app_row = c.execute('''
            SELECT a.*, s.title as scholarship_title, s.category, s.amount as max_amount, s.deadline,
                   u.name as student_name, u.email as student_email, u.student_id as campus_id,
                   u.program, u.faculty, u.country, u.year, u.gpa, u.hostel_resident
            FROM applications a
            JOIN scholarships s ON s.id = a.scholarship_id
            JOIN users u ON u.id = a.student_id
            WHERE a.id = ?
        ''', (aid,)).fetchone()
        
        if not app_row:
            flash('Application docket not found.', 'error')
            return redirect(url_for('dashboard'))
            
        if session['role'] == 'student' and app_row['student_id'] != session['user_id']:
            flash('Access Restricted.', 'error')
            return redirect(url_for('dashboard'))

        docs = c.execute('SELECT * FROM documents WHERE application_id=?', (aid,)).fetchall()
        reviews = c.execute('''
            SELECT r.*, u.name as reviewer_name 
            FROM reviews r 
            JOIN users u ON u.id = r.reviewer_id 
            WHERE r.application_id = ? 
            ORDER BY r.created_at DESC
        ''', (aid,)).fetchall()

    return render_template('application_slip.html', app=app_row, docs=docs, reviews=reviews)

@app.route('/applications/<int:aid>/documents')
@login_required
def documents(aid):
    with db() as c:
        approw = c.execute('SELECT * FROM applications WHERE id=?', (aid,)).fetchone()
        if not approw:
            flash('Application dossier not found.', 'error')
            return redirect(url_for('dashboard'))
        if session['role'] == 'student' and approw['student_id'] != session['user_id']:
            flash('Security Access Denied.', 'error')
            return redirect(url_for('dashboard'))
        docs = c.execute('SELECT * FROM documents WHERE application_id=?', (aid,)).fetchall()
    return render_template('documents.html', docs=docs, aid=aid, app=approw)

@app.route('/uploads/<path:filename>')
@login_required
def uploaded_file(filename):
    return send_from_directory(UPLOADS, filename, as_attachment=True)

@app.route('/health')
def health():
    return {'status': 'healthy', 'institution': 'South Asian University', 'service': 'SAU ScholarX', 'exchange_rate_inr': EXCHANGE_RATE}

init_db()

if __name__ == '__main__':
    debug_mode = os.environ.get('FLASK_DEBUG', '1') == '1'
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=debug_mode)
