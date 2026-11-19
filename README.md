# Northstar Scholarship Hub

A full-stack scholarship management system for a university software engineering project. It includes a student portal, staff review workspace, scholarship publishing, application tracking, and document uploads.

## Features

- Student registration, sign in, profile details, and role-based views
- Scholarship catalog with search and category filtering
- Scholarship detail pages with eligibility and document requirements
- Student applications with a personal statement and multiple supporting files
- Application statuses visible to students
- Staff dashboard with application review and decision notes
- Staff scholarship creation and open/closed status
- SQLite database initialized automatically with demonstration content
- Responsive desktop and mobile layout

## Technology

- Python 3 and Flask
- SQLite
- Jinja templates, HTML, CSS, and vanilla JavaScript

## Run locally

1. Install Python 3.10 or newer.
2. Open a terminal in this project folder.
3. Create and activate a virtual environment:

   Windows PowerShell:
   ```powershell
   py -m venv .venv
   .\.venv\Scripts\Activate.ps1
   ```

   macOS/Linux:
   ```bash
   python3 -m venv .venv
   source .venv/bin/activate
   ```

4. Install dependencies and start the server:

   ```bash
   pip install -r requirements.txt
   python app.py
   ```

5. Visit [http://127.0.0.1:5000](http://127.0.0.1:5000).

The database and upload directory are created automatically in the project folder. The seed accounts are created only when the users table is empty.

## Demo accounts

| Role | Email | Password |
|---|---|---|
| Student | student@university.edu | Student123! |
| Reviewer | reviewer@university.edu | Reviewer123! |
| Administrator | admin@university.edu | Admin123! |

Use a student account to submit an application. Sign into the reviewer or administrator account to publish scholarships and review student submissions.

## Project structure

```
scholarship-hub/
├── app.py
├── requirements.txt
├── README.md
├── templates/
│   ├── base.html
│   ├── landing.html
│   ├── login.html
│   ├── register.html
│   ├── student_dashboard.html
│   ├── staff_dashboard.html
│   ├── scholarships.html
│   ├── scholarship_detail.html
│   └── documents.html
├── static/
│   ├── app.js
│   └── style.css
└── uploads/
```

## Data model

- **User** has a student, reviewer, or administrator role. Student profile fields include campus ID, program, year, and GPA.
- **Scholarship** stores its description, award amount, deadline, eligibility, required documents, category, and status.
- **Application** links a student to a scholarship and stores the statement, requested amount, status, and staff notes. A student can submit only one application per scholarship.
- **Document** stores metadata and a generated filename for each uploaded file.
- **Review** records staff decisions and notes over time.

## Main routes

| Route | Purpose |
|---|---|
| `/` | Public landing page |
| `/register`, `/login`, `/logout` | Account access |
| `/dashboard` | Student or staff dashboard |
| `/scholarships` | Search and browse scholarships |
| `/scholarships/<id>` | Scholarship information and application form |
| `/scholarships/new` | Staff scholarship creation (POST) |
| `/applications/<id>/status` | Staff decision update (POST) |
| `/applications/<id>/documents` | Application document list |
| `/health` | Basic service health response |

## Configuration

- `SECRET_KEY`: set a long random value outside local development.
- `PORT`: server port (defaults to 5000).
- `FLASK_DEBUG=1`: enables Flask debug mode for local development only.

## Notes for project submission

This is a runnable academic project starter, not a production deployment. Before a real university rollout, connect institutional identity and student records, require CSRF protection, add password reset and email notification services, define retention and privacy policies, configure production hosting and backups, and validate eligibility rules with the university. The included demo credentials and development secret must be changed before deployment.

## Suggested demo walkthrough

1. Sign in as the student and explore the scholarship directory.
2. Open an award and submit an application with a statement and optional document.
3. Show the application in the student dashboard.
4. Sign out and sign in as reviewer.
5. Open the review action and record a decision with notes.
6. Sign back in as student to show the updated status.
7. Publish a new scholarship from the reviewer dashboard.

