from django.db import models
from django.core.validators import MaxValueValidator, MinValueValidator
from django.utils import timezone # Important for default date values in migrations

class Department(models.Model):
    name = models.CharField(max_length=100, unique=True)

    def __str__(self):
        return self.name

class Semester(models.Model):
    name = models.CharField(max_length=50)
    academic_year = models.IntegerField()
    start_date = models.DateField(null=True, blank=True)
    end_date = models.DateField(null=True, blank=True)

    class Meta:
        unique_together = ('name', 'academic_year')
        ordering = ['academic_year', 'start_date']

    def __str__(self):
        return f"{self.name} - {self.academic_year}"

class Student(models.Model):
    student_id = models.CharField(max_length=20, unique=True)
    name = models.CharField(max_length=100)
    email = models.EmailField(unique=True)
    phone_number = models.CharField(max_length=15, blank=True, null=True)
    department = models.ForeignKey(Department, on_delete=models.CASCADE)
    custom_password = models.CharField(max_length=128, blank=True, null=True)

    def __str__(self):
        return self.name

class Course(models.Model):
    course_code = models.CharField(max_length=10, unique=True)
    course_title = models.CharField(max_length=200)
    credit_unit = models.IntegerField()
    department = models.ForeignKey(Department, on_delete=models.CASCADE)
    semester = models.ForeignKey(Semester, on_delete=models.CASCADE)

    def __str__(self):
        return f"{self.course_code} - {self.course_title} ({self.semester})"

# This is the EXACT Enrollment model you provided without alteration.
class Enrollment(models.Model):
    student = models.ForeignKey(Student, on_delete=models.CASCADE)
    course = models.ForeignKey(Course, on_delete=models.CASCADE)
    semester = models.ForeignKey(Semester, on_delete=models.CASCADE)
    enrollment_date = models.DateField(auto_now_add=True)
    classes_attended = models.IntegerField(default=0, help_text="Number of classes attended (out of 10)")
    ca_score = models.IntegerField(default=0, validators=[MaxValueValidator(30)], help_text="Continuous Assessment Score (max 30)")
    exam_score = models.IntegerField(default=0, validators=[MaxValueValidator(70)], help_text="Exam Score (max 70)")
    # attendance_percentage is a property, not a database field

    class Meta:
        unique_together = ('student', 'course', 'semester')

    def __str__(self):
        return f"{self.student.name} - {self.course.course_code} - {self.semester}"

    @property
    def attendance_percentage(self):
        if self.classes_attended is not None:
            return (self.classes_attended / 10) * 100
        return 0.0

    @property
    def total_score(self):
        return self.ca_score + self.exam_score

    @property
    def grade(self):
        total = self.total_score
        if 40 <= total <= 44:
            return 'E'
        elif 45 <= total <= 49:
            return 'D'
        elif 50 <= total <= 59:
            return 'C'
        elif 60 <= total <= 69:
            return 'B'
        elif 70 <= total <= 100:
            return 'A'
        else:
            return 'F' # You might want to adjust the default for scores outside the range

# The AttendanceSession model has been REMOVED to synchronize with Enrollment's direct attendance tracking.
# If you decide later to track individual sessions, you'd re-add this model and
# remove 'classes_attended' from Enrollment, then adjust Enrollment's properties.
# class AttendanceSession(models.Model):
#     enrollment = models.ForeignKey(Enrollment, on_delete=models.CASCADE, related_name='attendance_sessions')
#     session_number = models.IntegerField(choices=[(i, f'Session {i}') for i in range(1, 8)])
#     attended = models.BooleanField(default=False)
#     date = models.DateField(auto_now_add=True)
#
#     class Meta:
#         unique_together = ('enrollment', 'session_number', 'date')
#         ordering = ['date', 'session_number']
#
#     def __str__(self):
#         return f"{self.enrollment.student.name} - {self.enrollment.course.course_code} - Session {self.session_number} ({'Attended' if self.attended else 'Absent'}) on {self.date}"

class DepartmentPassword(models.Model):
    department = models.OneToOneField(Department, on_delete=models.CASCADE, primary_key=True)
    password = models.CharField(max_length=128)

    def __str__(self):
        return f"Password for {self.department.name}"