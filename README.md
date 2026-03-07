# SmartPlan Task Management System
A simple Django-based task management application with core features for task tracking, sorting, and statistics.

## Quick Start (For Team Members)

### 1. Clone the Repository
```bash
git clone https://github.com/WangXinrui605/smartplan-task-management.git
cd smartplan-task-management
```

### 2. Set Up the Environment (Windows)
#### (1) Create and activate a virtual environment
```bash
python -m venv smartplan_env
smartplan_env\Scripts\activate
```

#### (2) Install dependencies
```bash
pip install -r requirements.txt
```

### 3. Initialize the Database and Test Data
```bash
# Run database migrations to create tables
python manage.py migrate

# Populate test data (creates test user, categories, and sample tasks)
python populate_smartplan.py
```

### 4. Run the Development Server
```bash
python manage.py runserver
```

### 5. Access the Application
- **Task Dashboard**: http://127.0.0.1:8000/
- **Admin Panel**: http://127.0.0.1:8000/admin/
  - Test username: `testuser`
  - Test password: `test123456`

## Core Features
1.  **Task Dashboard**: View, sort, edit, delete, and mark tasks as complete.
2.  **Statistics Page**: Track completion rates and task distribution by category/priority.
3.  **Task Management**: Create/edit tasks with validation for due dates and required fields.

---
