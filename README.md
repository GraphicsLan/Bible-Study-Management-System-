# Bible Study Management System

A web-based platform for managing small group Bible studies, member registration, group assignments, and community engagement for EUNCCU.

## Features
- Member registration and authentication
- Personalized member profiles
- Automatic and manual Bible study group assignment
- Group leader management
- Attendance/session tracking
- Dashboard for members and admins
- Admin actions log and export
- Responsive design for mobile and desktop

## Technology Stack
- Python 3.x
- Django 5.x
- Mysql 
- SQLite (default, can be swapped for MySQL)
- HTML5, CSS3 (with custom and dashboard styles)
- JavaScript (for interactivity)

## Project Structure
- `registration/` – Handles user registration, login, dashboard, and Bible study sessions
- `bs_grouping/` – Manages group creation, member assignment, leader management, and admin actions
- `members_profile/` – Member profile view and edit functionality
- `bs_system/` – Project settings, URLs, and templates

## Setup Instructions

### 1. Clone the Repository
```bash
# Clone the project
$ git clone <repo-url>
$ cd django_bs
```

### 2. Create and Activate a Virtual Environment
```bash
# Windows
$ python -m venv env
$ env\Scripts\activate

# Linux/Mac
$ python3 -m venv env
$ source env/bin/activate
```

### 3. Install Dependencies
```bash
$ pip install -r requirements.txt
```

### 4. Apply Migrations
```bash
$ python manage.py migrate
```

### 5. Create a Superuser (Admin)
```bash
$ python manage.py createsuperuser
```

### 6. Run the Development Server
```bash
$ python manage.py runserver
```

Visit [http://127.0.0.1:8000/](http://127.0.0.1:8000/) in your browser.

## Usage
- Register as a new member or log in as an admin.
- Members can view and edit their profiles, see group assignments, and track Bible study sessions.
- Admins can manage groups, assign leaders, rebalance groups, and export data.

## Customization
- To use MySQL or another database, update `DATABASES` in `bs_system/settings.py`.
- Email settings can be configured for production in `settings.py`.

## Contributing
Pull requests are welcome! For major changes, please open an issue first to discuss what you would like to change.

## License
This project is for educational and ministry use. 
contact me for any use and authorization
---
For questions or support, contact .
Phone +254 725023365
Email hian14550@gmail.com 