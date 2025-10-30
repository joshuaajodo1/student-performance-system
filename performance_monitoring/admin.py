from django.contrib import admin
# Ensure all models are imported. AttendanceSession is no longer imported as it's removed from models.py.
from .models import Department, Semester, Student, Course, Enrollment, DepartmentPassword
from django import forms
from django.contrib import messages
# You might need this if you use MaxValueValidator in admin.py itself, but usually only needed in models.py
# from django.core.validators import MaxValueValidator

# --- Admin Actions Forms ---
class EnrollInSemesterForm(forms.Form):
    academic_year = forms.IntegerField(label="Academic Year")
    semester_name = forms.CharField(max_length=50, label="Semester Name")
    action = forms.CharField(widget=forms.HiddenInput(), initial='enroll_in_semester')
    select_across = forms.CharField(widget=forms.HiddenInput(), initial='1')

# --- Admin Actions ---
def enroll_in_semester(modeladmin, request, queryset):
    from .models import Course, Enrollment, Semester # Import models inside function to avoid circular imports
    academic_year = request.POST.get('academic_year')
    semester_name = request.POST.get('semester_name')

    if not academic_year or not semester_name:
        messages.error(request, "Please select an academic year and semester.")
        return

    try:
        semester = Semester.objects.get(academic_year=academic_year, name=semester_name)
    except Semester.DoesNotExist:
        messages.error(request, f'Semester "{semester_name} {academic_year}" does not exist.')
        return

    enrolled_count = 0
    for student in queryset:
        # Filter courses by both department and semester to ensure correct courses are enrolled
        courses = Course.objects.filter(department=student.department, semester=semester)
        for course in courses:
            # get_or_create prevents duplicate enrollments
            enrollment, created = Enrollment.objects.get_or_create(student=student, course=course, semester=semester)
            if created:
                enrolled_count += 1

    if enrolled_count:
        messages.success(request, f'{enrolled_count} new enrollments were successfully created for {semester}.')
    else:
        messages.info(request, 'No new enrollments were created (students might already be enrolled in these courses).')

enroll_in_semester.short_description = "Enroll selected students in a specific semester's courses"

# --- Admin Model Configurations ---

@admin.register(Department)
class DepartmentAdmin(admin.ModelAdmin):
    list_display = ('id', 'name')
    search_fields = ('name',) # Added search field for Department

@admin.register(Semester)
class SemesterAdmin(admin.ModelAdmin):
    list_display = ('name', 'academic_year', 'start_date', 'end_date')
    search_fields = ('name', 'academic_year')
    list_filter = ('academic_year',) # Added list filter for academic year

@admin.register(Student)
class StudentAdmin(admin.ModelAdmin):
    list_display = ('student_id', 'name', 'email', 'department')
    search_fields = ('student_id', 'name', 'email', 'department__name') # Added department search
    list_filter = ('department',) # Added department filter
    actions = [enroll_in_semester]
    action_form = EnrollInSemesterForm
    # custom_password might be sensitive, consider making it readonly or not visible by default
    fields = ('student_id', 'name', 'email', 'phone_number', 'department', 'custom_password')

@admin.register(Course)
class CourseAdmin(admin.ModelAdmin):
    list_display = ('course_code', 'course_title', 'credit_unit', 'department', 'semester')
    search_fields = ('course_code', 'course_title', 'department__name', 'semester__name', 'semester__academic_year')
    list_filter = ('department', 'semester__academic_year', 'semester__name')

# The AttendanceSessionInline is REMOVED as the AttendanceSession model no longer exists.
# class AttendanceSessionInline(admin.TabularInline):
#     model = AttendanceSession
#     extra = 1
#     fields = ('session_number', 'attended', 'date')
#     readonly_fields = ('date',)

@admin.register(Enrollment)
class EnrollmentAdmin(admin.ModelAdmin):
    # list_display fields are now completely in sync with the Enrollment model's fields/properties
    list_display = (
        'id', 'student', 'course', 'semester', 'enrollment_date',
        'classes_attended', 'attendance_percentage', # classes_attended is a field, attendance_percentage is a property
        'ca_score', 'exam_score', 'total_score', 'grade' # ca_score, exam_score are fields, total_score, grade are properties
    )
    search_fields = ('student__name', 'course__course_code', 'semester__name', 'semester__academic_year')
    list_filter = (
        'semester__academic_year', 'semester__name', 'course__course_code',
        'student__department' # Filter by student's department
    )
    # fields directly map to the Enrollment model's editable fields
    fields = ('student', 'course', 'semester', 'classes_attended', 'ca_score', 'exam_score')
    # readonly_fields correctly include auto_now_add and properties
    readonly_fields = ('enrollment_date', 'attendance_percentage', 'total_score', 'grade')
    # inlines is REMOVED as AttendanceSessionInline no longer exists
    # inlines = [AttendanceSessionInline]

@admin.register(DepartmentPassword)
class DepartmentPasswordAdmin(admin.ModelAdmin):
    list_display = ('department',) # Only display the department name
    fields = ('department', 'password')