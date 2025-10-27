English Version
Overview

Shift is a lightweight and flexible scheduling management web application designed to help teams manage shifts, track workloads, and improve collaboration efficiency.
It’s built with Django on the backend, and currently deployed on both Render and AWS, serving as a full-stack project demonstration for portfolio and career development purposes.

Features

🗓 Create, edit, and delete shifts easily

👥 Manage team members and roles

🔔 View daily/weekly schedules

🌐 Django-based backend API

☁️ Deployed to both Render and AWS

Deployment

✅ Render: Fully deployed and functional

⚙️ AWS: Backend deployed successfully; frontend integration in progress

🎯 Goal: Connect both ends and achieve full-stack integration within this week

🔗 A live demo link will be added once the AWS frontend is fully connected.

Tech Stack
Category	Technology
Backend	Python (Django)
Database	SQLite (configurable to PostgreSQL / MySQL)
Frontend	HTML, CSS, Django Template (frontend framework in development)
Deployment	Render, AWS EC2 / S3 / Elastic Beanstalk

Testing
Currently, there are no automated tests implemented.
Future updates may include unit and integration tests using Django’s built-in framework.

Project Structure
shift/
 ├── shift/              # Django project core settings
 ├── shiftapp/           # Main app logic
 ├── db.sqlite3          # Default database
 ├── manage.py           # Django management entry point
 └── requirements.txt    # Dependencies

Purpose
I currently work at a pharmacy, where the manager still manually creates shift schedules using Excel.
I realized there should be a faster and more automated solution — so I built Shift to address that pain point.
Although there are already many existing scheduling apps available, I wanted to develop my own version to both solve a real problem and strengthen my skills by building a complete side project from scratch.
