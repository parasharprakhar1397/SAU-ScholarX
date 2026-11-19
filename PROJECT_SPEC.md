# Project specification

## Problem statement

Scholarship opportunities, applications, documents, and decisions are often managed across disconnected forms and spreadsheets. Students need a single place to find opportunities and track progress, while university staff need a consistent workflow to collect and review submissions.

## Goals

1. Give students a searchable catalog of scholarship opportunities.
2. Collect student applications and supporting documents online.
3. Let authorized staff review submissions and record decisions.
4. Show application status to the student.
5. Maintain a structured data store for users, awards, submissions, documents, and reviews.

## Functional requirements

- Visitors can register a student account and sign in.
- A student can search/filter the scholarship directory, view eligibility and deadlines, and apply once per opportunity.
- An application contains a statement and may include supporting files.
- A student can see the status of each submitted application.
- A reviewer or administrator can publish a scholarship and set it open or closed.
- A reviewer or administrator can view the review queue, update application status, and add notes.
- The system records each review decision in the review history table.
- Only signed-in users can access application documents; students can only access documents for their own applications.
- Scholarship amounts, deadlines, and statuses are visible in the interface.

## Non-functional requirements

- Responsive layout for phone, tablet, and desktop.
- Passwords are stored as salted hashes.
- SQL values are passed as parameters.
- Upload size is limited to 12 MB per request and extensions are restricted to PDF, common images, and Word documents.
- Role checks protect staff actions.
- Application uniqueness is enforced by the database.
- The local app is easy to install and run using the included dependency file.

## Roles

| Role | Capabilities |
|---|---|
| Student | Browse awards, submit applications, view own status and documents |
| Reviewer | Publish awards, inspect submissions, update status and notes |
| Administrator | Same project-level access as reviewer; intended for broader system administration |

## Application lifecycle

`Submitted → Under Review → Needs Information / Approved / Rejected`

A reviewer may return an application to `Submitted` while correcting its workflow status. Review notes are retained with each decision.

## Core entities

`User 1—N Application N—1 Scholarship`; `Application 1—N Document`; `Application 1—N Review`; `User 1—N Review` (reviewer).

## Acceptance criteria

- A newly registered student can sign in and see the dashboard.
- The catalog displays seeded opportunities and filters by keyword/category.
- A student can submit a unique application and see it in the dashboard.
- The reviewer can see the submission, add a decision, and the student sees the new status.
- A reviewer can create a new scholarship and see it listed.
- An unauthorized visitor is redirected to sign in for protected screens.

