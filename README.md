# South Asian University (SAU) — ScholarX Portal
### Directorate of Student Affairs & Standing Committee on Scholarships & Financial Aid (SCSFA)

An official institutional web portal for **South Asian University (SAU)**, New Delhi — an international university established by the eight member nations of the **South Asian Association for Regional Cooperation (SAARC)**: Afghanistan, Bangladesh, Bhutan, India, Maldives, Nepal, Pakistan, and Sri Lanka.

---

## 🏛️ System Overview

The **SAU ScholarX Portal** is designed to administer, verify, and adjudicate fellowships, merit awards, and need-based fee remissions under the mandate of Section 12 of the South Asian University Act and the Financial Aid Ordinances of the SAU Governing Board.

### Key Functional Capabilities

1. **Inter-Governmental Quota & Scheme Registry**:
   - Manages statutory scholarship ordinances including the **SAARC-India Silver Jubilee Scholarship (SJS)**, **President’s Doctoral Fellowship**, **Financial Support Scheme (FSS)**, and departmental technical research grants.
   - Distinct categorization for all eight SAU academic faculties.

2. **Official Student Academic Dossier**:
   - Complete tracking with institutional SAU roll numbers (`SAU/2024/CSE/019`), SAARC citizenship designation, academic faculties, and accommodation records.
   - Real-time procedural progress tracking: `Submitted` ➔ `Faculty Scrutiny` ➔ `SCSFA Central Review` ➔ `Sanction Approved`.

3. **Printable Official Verification Slip (`/applications/<id>/slip`)**:
   - Generates an official university docket with the SAU Crest, Sanskrit motto (*ज्ञानं सीमारहितम्*), candidate credentials, statutory attachment checklist, and formal signoff blocks for the Head of Department and Dean of Student Affairs.

4. **Standing Committee Adjudication Workspace**:
   - Faculty reviewers and administrative officers can filter applications by SAARC nationality, degree faculty, and decision status.
   - Record official determinations, award amounts, and committee minutes directly into the candidate's record.

5. **Statutory Regulations & Prescribed Annexures (`/guidelines`)**:
   - Complete legal guidelines, quota allocation rules across SAARC nations, and verbatim templates for **Annexure-A** (Income Affidavit), **Annexure-B** (Bonafide Attendance Certificate), and **Annexure-C** (Research Synopsis Endorsement).

---

## 🏛️ Official University Contact Directory

- **Permanent Campus Address:** South Asian University, Gaushala Road, Maidan Garhi, New Delhi – 110068, India
- **Telephone Lines:**
  - **Admissions / Financial Aid Directorate:** `+91 (11) 3565 6600`
  - **General Reception / EPABX:** `+91 (11) 3565 6500`
  - **Office of the President / Registrar:** `+91 (11) 3565 6595`
- **Official Emails:** `financial-aid@sau.int`, `scholarships@sau.int`, `admissions@sau.int`

---

## 💱 Institutional Currency & Grading Standards

1. **Locked Exchange Rate Policy:**
   - Pursuant to the SAU Finance Committee resolution for Session 2026–27, all financial awards, fee remissions, and maintenance stipends are pegged to USD and disbursed at the locked conversion rate of **₹91.00 INR per USD**.
   - Dual currency values are rendered automatically across all public catalogs, student dockets, and committee rosters (e.g. `$4,200 (₹3,82,200)`).

2. **Standard 10.00 CGPA Grading Scale:**
   - Academic standing and eligibility thresholds across all 7 faculties are evaluated on a **10.00 Cumulative Grade Point Average (CGPA)** grading scale (replacing 4.0 scales).

---

## 🔐 Demonstration Credentials

| Academic Role | Institutional Email | Password | Profile Particulars |
|---|---|---|---|
| **Enrolled Scholar (India)** | `student@university.edu` | `Student123!` | Aarav Sharma &bull; M.Tech CSE &bull; Roll: `SAU/2024/CSE/019` |
| **Enrolled Scholar (Nepal)** | `pooja.shrestha@sau.ac.in` | `Student123!` | Pooja Shrestha &bull; M.Sc Biotechnology &bull; Roll: `SAU/2024/LSB/007` |
| **Enrolled Scholar (Bangladesh)** | `tariqul.islam@sau.ac.in` | `Student123!` | Tariqul Islam &bull; M.A. Economics &bull; Roll: `SAU/2024/ECO/014` |
| **Faculty Reviewer (SCSFA)** | `reviewer@university.edu` | `Reviewer123!` | Prof. Maya Sen &bull; Member Secretary, Scrutiny Committee |
| **Administrative Dean** | `admin@university.edu` | `Admin123!` | Dr. K. Raghavan &bull; Dean, Directorate of Student Affairs |

*Quick 1-click credential auto-fill buttons are provided on the login page.*

---

## 📁 Repository Architecture

```
Project/
├── app.py                      # Flask application, routing, and SQLite schema
├── requirements.txt            # Python dependencies (Flask >= 3.0)
├── README.md                   # Institutional documentation
├── PROJECT_SPEC.md             # Functional and technical requirements
├── scholarships.db             # SQLite database with SAU data
├── uploads/                    # Secure repository for verified student attachments
├── static/
│   ├── style.css               # Official SAU design system (Oxford Navy & Crimson)
│   └── app.js                  # Client scripts, file feedback, and alert auto-dismissal
└── templates/
    ├── base.html               # Institutional layout, SAARC bar, and SAU seal
    ├── landing.html            # Public homepage with Dean's welcome and featured grants
    ├── guidelines.html         # Statutory regulations and Annexures A, B, C
    ├── login.html              # Central Authentication Service (SSO)
    ├── register.html           # Student registration with SAARC country and faculty picker
    ├── student_dashboard.html  # Student academic dossier and application tracker
    ├── staff_dashboard.html    # SCSFA Committee workspace with scrutiny filters
    ├── scholarships.html       # Searchable scholarship ordinances catalog
    ├── scholarship_detail.html # Grant specifics and application submission form
    ├── documents.html          # Verification attachments inspector
    └── application_slip.html   # Printable official verification docket
```

---

## 🚀 Execution Instructions

1. Ensure Python 3.10+ is installed.
2. In the project directory, run:
   ```powershell
   python app.py
   ```
3. Open your browser and navigate to:
   ```
   http://127.0.0.1:5000
   ```
