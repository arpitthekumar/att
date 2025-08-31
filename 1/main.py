from database import init_db
from dashboard.auth import login
from dashboard.admin import admin_dashboard
from dashboard.teacher import teacher_dashboard
from dashboard.student import student_dashboard


def main():
    init_db()
    while True:
        user_id, role = None, None
        while not role:
            user_id, role = login()

        if role == "admin":
            admin_dashboard()
        elif role == "teacher":
            teacher_dashboard(user_id)
        elif role == "student":
            student_dashboard(user_id)


if __name__ == "__main__":
    main()
