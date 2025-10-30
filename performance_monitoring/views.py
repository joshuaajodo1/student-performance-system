# performance_monitoring/views.py
from django.shortcuts import get_object_or_404, render, redirect
from django.contrib.auth import authenticate, login as auth_login, logout as auth_logout
from django.contrib.auth.forms import AuthenticationForm
from .models import Student, Enrollment, DepartmentPassword, Department, Semester, Course
from django.urls import reverse
from django.contrib import messages
import json
from django.db.models import Avg, Sum, F

# --- Utility Functions ---
def get_grade_point(total_score):
    if total_score is None:
        return 0
    if 70 <= total_score <= 100:
        return 5
    elif 60 <= total_score <= 69:
        return 4
    elif 50 <= total_score <= 59:
        return 3
    elif 45 <= total_score <= 49:
        return 2
    elif 40 <= total_score <= 44:
        return 1
    else:
        return 0

# --- Core Views ---
def home(request):
    return render(request, 'performance_monitoring/homepage.html')

def custom_logout_view(request):
    # Log out Django Auth User (for admin)
    if request.user.is_authenticated:
        auth_logout(request)
        
    # Clear custom student session
    if 'student_id' in request.session:
        # Save student name/dept for a friendly logout message
        logout_message = f"{request.session.get('student_name', 'Student')} has been logged out."
        del request.session['student_id']
        if 'student_name' in request.session:
             del request.session['student_name']
        messages.info(request, logout_message)

    # Clear custom department session
    elif 'department_id' in request.session:
        logout_message = f"{request.session.get('department_name', 'Department')} admin has been logged out."
        del request.session['department_id']
        if 'department_name' in request.session:
             del request.session['department_name']
        messages.info(request, logout_message)
    
    else:
        messages.info(request, "You have been logged out.")

    return redirect('home')


# --- Login Views ---
def admin_login(request):
    if request.method == 'POST':
        form = AuthenticationForm(request, data=request.POST)
        if form.is_valid():
            username = form.cleaned_data.get('username')
            password = form.cleaned_data.get('password')
            user = authenticate(username=username, password=password)
            if user is not None:
                auth_login(request, user)
                return redirect('admin:index')
            else:
                form.add_error(None, 'Invalid username or password.')
        messages.error(request, 'Invalid username or password.')
    else:
        form = AuthenticationForm()
    return render(request, 'performance_monitoring/admin_login.html', {'form': form})

def student_login(request):
    if request.method == 'POST':
        matriculation_number = request.POST.get('matriculation_number')
        password = request.POST.get('password')
        try:
            student = Student.objects.get(student_id=matriculation_number)
            # NOTE: Using plaintext password check as per original models/views context
            if student.custom_password == password:
                request.session['student_id'] = student.student_id
                request.session['student_name'] = student.name # Store name for base template
                return redirect('student_dashboard')
            else:
                messages.error(request, "Invalid Matriculation Number or Password.")
        except Student.DoesNotExist:
            messages.error(request, "Invalid Matriculation Number or Password.")
        return render(request, 'performance_monitoring/student_login.html')
    return render(request, 'performance_monitoring/student_login.html')

def admin_department_login(request):
    departments = Department.objects.all()
    if request.method == 'POST':
        department_id = request.POST.get('department')
        password = request.POST.get('password')
        try:
            department_password = DepartmentPassword.objects.get(department_id=department_id)
            # NOTE: Using plaintext password check as per original models/views context
            if department_password.password == password:
                department = department_password.department
                request.session['department_id'] = department_id
                request.session['department_name'] = department.name # Store name for base template
                return redirect('department_dashboard')
            else:
                messages.error(request, "Invalid Department or Password.")
        except DepartmentPassword.DoesNotExist:
            messages.error(request, "Invalid Department or Password.")
        return render(request, 'performance_monitoring/admin_department_login.html', {'departments': departments})
    else:
        return render(request, 'performance_monitoring/admin_department_login.html', {'departments': departments})


# --- Dashboard Views ---
def student_dashboard(request, student_id=None):
    # Determine the student to display based on URL param (for admin/dept) or session (for student)
    
    # 1. Determine Student Context
    if student_id:
        # Admin or Dept viewing a report (should use student_performance_report, but kept here for flexibility)
        try:
            student = Student.objects.get(student_id=student_id)
        except Student.DoesNotExist:
            messages.error(request, f"Student with ID {student_id} not found.")
            return redirect('department_dashboard')
        
    else:
        # Must be logged in as a student (standard student dashboard view)
        session_student_id = request.session.get('student_id')
        if not session_student_id:
            messages.error(request, "Please log in to view your dashboard.")
            return redirect('student_login')
        try:
            student = Student.objects.get(student_id=session_student_id)
        except Student.DoesNotExist:
            messages.error(request, "Student not found. Please log in again.")
            return redirect('student_login')

    # 2. Fetch Enrollments
    # Use prefetch_related if possible, but basic filter is safe
    enrollments = Enrollment.objects.filter(student=student).order_by('semester__academic_year', 'semester__name')

    # 3. Initialize Calculation Variables
    semester_data_raw = {}
    course_performance_data = [] # For the Chart (JSON)
    overall_total_credit_units = 0
    overall_weighted_grade_points = 0
    overall_total_attendance_percentage_sum = 0
    total_enrollments_for_attendance_avg = 0
    total_unique_courses = set() # For Total Courses Count

    # 4. Process Enrollments (Combines Overall, Semester, and Chart Data Generation)
    for enrollment in enrollments:
        semester = enrollment.semester
        current_total_score = enrollment.total_score
        grade_point = get_grade_point(current_total_score)
        
        # Initialize semester data structure if it's the first time seeing this semester
        if semester not in semester_data_raw:
            semester_data_raw[semester] = {
                'enrollments': [],
                'total_credit_units': 0,
                'weighted_grade_points': 0,
                'total_attendance': 0,
                'num_courses': 0,
            }

        semester_data_raw[semester]['enrollments'].append(enrollment)
        
        # CGPA calculation logic
        if current_total_score is not None and enrollment.course.credit_unit > 0:
            semester_data_raw[semester]['total_credit_units'] += enrollment.course.credit_unit
            semester_data_raw[semester]['weighted_grade_points'] += grade_point * enrollment.course.credit_unit
            
            # Overall totals (only count valid CGPA courses)
            overall_total_credit_units += enrollment.course.credit_unit
            overall_weighted_grade_points += grade_point * enrollment.course.credit_unit
            
        # Attendance calculation logic
        semester_data_raw[semester]['total_attendance'] += enrollment.attendance_percentage
        semester_data_raw[semester]['num_courses'] += 1
        
        # Overall totals (count all enrollments for overall average attendance)
        overall_total_attendance_percentage_sum += enrollment.attendance_percentage
        total_enrollments_for_attendance_avg += 1
        
        # Total Unique Courses
        total_unique_courses.add(enrollment.course.pk)

        # Prepare JSON data for Chart.js
        course_performance_data.append({
            'course_code': enrollment.course.course_code,
            # Ensure data is float for JSON dump compatibility
            'total_score': float(current_total_score) if current_total_score is not None else 0.0, 
            'attendance_percentage': float(enrollment.attendance_percentage),
        })


    # 5. Finalize Semester Data (CGPA and Avg Attendance)
    processed_semester_data = {}
    sorted_semesters = sorted(semester_data_raw.keys(), key=lambda s: (s.academic_year, s.start_date if s.start_date else 0))

    for semester in sorted_semesters:
        data = semester_data_raw[semester]
        processed_semester_data[semester] = {
            'enrollments': data['enrollments'],
            'cgpa': (data['weighted_grade_points'] / data['total_credit_units']) if data['total_credit_units'] > 0 else 0,
            'average_attendance': (data['total_attendance'] / data['num_courses']) if data['num_courses'] > 0 else 0,
        }

    # 6. Finalize Overall Metrics
    overall_cgpa = (overall_weighted_grade_points / overall_total_credit_units) if overall_total_credit_units > 0 else 0
    overall_average_attendance = (overall_total_attendance_percentage_sum / total_enrollments_for_attendance_avg) if total_enrollments_for_attendance_avg > 0 else 0

    # 7. Build Context
    context = {
        'student': student,
        'semester_data': processed_semester_data,
        'overall_cgpa': overall_cgpa,
        'overall_average_attendance': overall_average_attendance,
        # *** THESE ARE THE FIXED/ADDED VARIABLES ***
        'total_unique_courses': len(total_unique_courses), 
        'course_performance_data_json': json.dumps(course_performance_data),
        # *****************************************
        'is_admin_view': student_id and request.session.get('department_id') # Flag for showing 'Back to Dashboard' etc.
    }
    return render(request, 'performance_monitoring/student_dashboard.html', context)


def department_dashboard(request):
    department_id = request.session.get('department_id')
    if not department_id:
        messages.error(request, "Please log in as a department admin to view this page.")
        return redirect('admin_department_login')

    department = get_object_or_404(Department, pk=department_id)

    # --- Department-wide Metrics ---
    total_students_in_dept = Student.objects.filter(department=department).count()
    total_courses_in_dept = Course.objects.filter(department=department).count()

    students_in_department = Student.objects.filter(department=department).prefetch_related('enrollment_set__course')

    department_overall_cgpa_sum = 0
    students_with_valid_cgpa = 0
    students_data_for_table = [] 

    for student in students_in_department:
        student_enrollments = student.enrollment_set.all()

        student_total_credit_units = 0
        student_weighted_grade_points = 0
        student_total_attendance_percentage_sum = 0
        student_courses_for_attendance_avg = 0 

        for enrollment in student_enrollments:
            total_score = enrollment.total_score
            if total_score is not None and enrollment.course.credit_unit > 0:
                grade_point = get_grade_point(total_score)
                student_total_credit_units += enrollment.course.credit_unit
                student_weighted_grade_points += grade_point * enrollment.course.credit_unit

            if enrollment.attendance_percentage is not None:
                student_total_attendance_percentage_sum += enrollment.attendance_percentage
                student_courses_for_attendance_avg += 1

        student_cgpa = (student_weighted_grade_points / student_total_credit_units) if student_total_credit_units > 0 else 0
        student_avg_attendance = (student_total_attendance_percentage_sum / student_courses_for_attendance_avg) if student_courses_for_attendance_avg > 0 else 0

        if student_total_credit_units > 0:
            department_overall_cgpa_sum += student_cgpa
            students_with_valid_cgpa += 1

        students_data_for_table.append({
            'student': student,
            'overall_cgpa': student_cgpa,
            'average_attendance': student_avg_attendance,
        })

    avg_department_cgpa = (department_overall_cgpa_sum / students_with_valid_cgpa) if students_with_valid_cgpa > 0 else 0

    # Department Courses List
    department_courses_list = []
    courses_in_department = Course.objects.filter(department=department).order_by('course_code').select_related('semester')

    for course in courses_in_department:
        # Only count enrollments for the current course, regardless of semester, for a total count
        enrolled_students_count = Enrollment.objects.filter(course=course).values('student').distinct().count()
        department_courses_list.append({
            'course': course,
            'enrolled_students_count': enrolled_students_count,
        })

    context = {
        'department': department,
        'total_students_in_dept': total_students_in_dept,
        'avg_department_cgpa': avg_department_cgpa,
        'total_courses_in_dept': total_courses_in_dept,
        'students_data': students_data_for_table,
        'department_courses': department_courses_list,
    }
    return render(request, 'performance_monitoring/department_dashboard.html', context)


def student_performance_report(request, student_id):
    student = get_object_or_404(Student, student_id=student_id)
    enrollments = Enrollment.objects.filter(student=student).order_by('semester__academic_year', 'semester__name')

    semester_data_raw = {}
    course_performance_data = []

    overall_total_credit_units = 0
    overall_weighted_grade_points = 0
    overall_total_attendance_percentage_sum = 0
    total_enrollments_for_attendance_avg = 0
    total_unique_courses = set()


    for enrollment in enrollments:
        semester = enrollment.semester
        if semester not in semester_data_raw:
            semester_data_raw[semester] = {
                'enrollments': [],
                'total_credit_units': 0,
                'weighted_grade_points': 0,
                'total_attendance': 0,
                'num_courses': 0,
            }

        current_total_score = enrollment.total_score
        grade_point = get_grade_point(current_total_score)

        semester_data_raw[semester]['enrollments'].append(enrollment)
        
        # Only include courses with credit units in CGPA calculation
        if current_total_score is not None and enrollment.course.credit_unit > 0:
            semester_data_raw[semester]['total_credit_units'] += enrollment.course.credit_unit
            semester_data_raw[semester]['weighted_grade_points'] += grade_point * enrollment.course.credit_unit
            
        semester_data_raw[semester]['total_attendance'] += enrollment.attendance_percentage
        semester_data_raw[semester]['num_courses'] += 1
        total_unique_courses.add(enrollment.course.pk) # Count unique courses for total courses metric

        # Prepare JSON data for Chart.js
        course_performance_data.append({
            'course_code': enrollment.course.course_code,
            # Ensure data is float for JSON dump compatibility
            'total_score': float(current_total_score) if current_total_score is not None else 0.0, 
            'attendance_percentage': float(enrollment.attendance_percentage),
        })


    processed_semester_data = {}
    sorted_semesters = sorted(semester_data_raw.keys(), key=lambda s: (s.academic_year, s.start_date if s.start_date else 0))

    for semester in sorted_semesters:
        data = semester_data_raw[semester]
        processed_semester_data[semester] = {
            'enrollments': data['enrollments'],
            'cgpa': (data['weighted_grade_points'] / data['total_credit_units']) if data['total_credit_units'] > 0 else 0,
            'average_attendance': (data['total_attendance'] / data['num_courses']) if data['num_courses'] > 0 else 0,
        }
        overall_total_credit_units += data['total_credit_units']
        overall_weighted_grade_points += data['weighted_grade_points']
        overall_total_attendance_percentage_sum += data['total_attendance']
        total_enrollments_for_attendance_avg += data['num_courses']


    overall_cgpa = (overall_weighted_grade_points / overall_total_credit_units) if overall_total_credit_units > 0 else 0
    overall_average_attendance = (overall_total_attendance_percentage_sum / total_enrollments_for_attendance_avg) if total_enrollments_for_attendance_avg > 0 else 0

    context = {
        'student': student,
        'semester_data': processed_semester_data,
        'overall_cgpa': overall_cgpa,
        'overall_average_attendance': overall_average_attendance,
        'total_unique_courses': len(total_unique_courses), # Use unique course count
        'course_performance_data_json': json.dumps(course_performance_data),
        'is_admin_view': True # Always True if accessed from a department context
    }

    return render(request, 'performance_monitoring/student_report.html', context)