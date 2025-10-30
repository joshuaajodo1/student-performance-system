# performance_monitoring/urls.py

from django.contrib import admin
from django.urls import path, re_path # Make sure re_path is imported
from performance_monitoring import views # Import the entire views module

urlpatterns = [
    path('', views.home, name='home'),
    path('admin/login/', views.admin_login, name='admin_login'),
    path('student/login/', views.student_login, name='student_login'),

    # Student Dashboard for the logged-in student (session-based)
    path('student/dashboard/', views.student_dashboard, name='student_dashboard'), 

    # Admin's view of a specific student's dashboard/profile (allows slashes in student_id)
    # Using re_path with `.+` to capture matriculation numbers like U2021/5570183
    re_path(r'^admin/student/profile/(?P<student_id>.+)/$', views.student_dashboard, name='view_student_profile_from_admin'),
    
    # Department Admin Login
    path('department/login/', views.admin_department_login, name='admin_department_login'),
    # Department Dashboard (after successful login)
    path('department/dashboard/', views.department_dashboard, name='department_dashboard'),

    # Student Performance Report URL (requires student_id and allows slashes)
    # This URL should be linked from the student dashboard or department dashboard
    re_path(r'^student_report/(?P<student_id>.+)/$', views.student_performance_report, name='student_performance_report'),
    
    # Django Admin Site URL - always place this after your specific admin paths
    path('admin/', admin.site.urls), 
]