from django.contrib import admin
# pyrefly: ignore [missing-import]
from .models import Employee,LeaveRequest

admin.site.register(Employee)
admin.site.register(LeaveRequest)