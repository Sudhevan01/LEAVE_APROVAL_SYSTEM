import logging
import calendar as cal
from datetime import date, timedelta

from django.core.mail import send_mail
from django.conf import settings
from django.contrib.auth.models import User
from django.http import HttpResponse
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
# pyrefly: ignore [missing-import]
from .models import Employee, LeaveRequest

logger = logging.getLogger(__name__)


def get_employee(user):
    try:
        return Employee.objects.get(user=user)
    except Employee.DoesNotExist:
        return Employee.objects.create(
            user=user,
            name=user.get_full_name() or user.username,
            email=user.email,
            department='General',
            role='Admin' if user.is_staff else 'Employee',
        )


def landing_view(request):
    return render(request, 'landing.html')


def login_view(request):
    role = request.GET.get('role', request.POST.get('role', 'employee'))

    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')

        user = authenticate(request, username=username, password=password)

        if user is not None:
            login(request, user)
            role = request.POST.get('role', 'employee')
            if role == 'admin' and user.is_staff:
                return redirect('admin_dashboard')
            else:
                return redirect('dashboard')
        else:
            messages.error(request, 'Invalid username or password.')

    return render(request, 'login.html', {'role': role})


def logout_view(request):
    logout(request)
    return redirect('landing')


@login_required
def dashboard(request):
    employee = get_employee(request.user)
    leaves = LeaveRequest.objects.filter(employee=employee).order_by('-applied_on')

    context = {
        'active_page': 'dashboard',
        'leaves': leaves,
        'total_leaves': leaves.count(),
        'pending_leaves': leaves.filter(status='Pending').count(),
        'approved_leaves': leaves.filter(status='Approved').count(),
        'rejected_leaves': leaves.filter(status='Rejected').count(),
    }

    return render(request, 'dashboard.html', context)


@login_required
def apply_leave(request):
    employee = get_employee(request.user)

    if request.method == 'POST':
        leave_type = request.POST.get('leave_type')
        start_date = request.POST.get('start_date')
        end_date = request.POST.get('end_date')
        reason = request.POST.get('reason')

        LeaveRequest.objects.create(
            employee=employee,
            leave_type=leave_type,
            start_date=start_date,
            end_date=end_date,
            reason=reason
        )

        messages.success(request, 'Leave request submitted successfully!')
        return redirect('dashboard')

    context = {
        'active_page': 'apply_leave',
    }
    return render(request, 'apply_leave.html', context)


@login_required
def leave_history(request):
    employee = get_employee(request.user)
    leaves = LeaveRequest.objects.filter(employee=employee).order_by('-applied_on')

    context = {
        'active_page': 'leave_history',
        'leaves': leaves,
    }
    return render(request, 'leave_history.html', context)


@login_required
def profile_view(request):
    employee = get_employee(request.user)

    if request.method == 'POST':
        employee.name = request.POST.get('name', employee.name)
        employee.email = request.POST.get('email', employee.email)
        employee.department = request.POST.get('department', employee.department)
        if request.user.is_staff:
            employee.role = request.POST.get('role', employee.role)
        employee.save()
        messages.success(request, 'Profile updated successfully!')
        return redirect('profile')

    leaves = LeaveRequest.objects.filter(employee=employee)

    context = {
        'active_page': 'profile',
        'employee': employee,
        'total_leaves': leaves.count(),
        'approved_leaves': leaves.filter(status='Approved').count(),
        'pending_leaves': leaves.filter(status='Pending').count(),
    }
    return render(request, 'profile.html', context)


@login_required
def calendar_view(request):
    employee = get_employee(request.user)
    today = date.today()
    month = int(request.GET.get('month', today.month))
    year = int(request.GET.get('year', today.year))

    month_calendar = cal.monthcalendar(year, month)
    month_name = cal.month_name[month]

    leaves = LeaveRequest.objects.filter(
        employee=employee,
        status__in=['Approved', 'Pending'],
        start_date__lte=date(year, month, cal.monthrange(year, month)[1]),
        end_date__gte=date(year, month, 1),
    )

    leave_map = {}
    for leave in leaves:
        current = max(leave.start_date, date(year, month, 1))
        end = min(leave.end_date, date(year, month, cal.monthrange(year, month)[1]))
        while current <= end:
            if current.day not in leave_map:
                leave_map[current.day] = []
            leave_map[current.day].append({
                'leave_type': leave.leave_type,
                'status': leave.status,
                'employee': leave.employee.name,
            })
            current += timedelta(days=1)

    calendar_days = []

    first_weekday = cal.monthrange(year, month)[0]
    first_weekday_sun = (first_weekday + 1) % 7

    if first_weekday_sun > 0:
        if month == 1:
            prev_month, prev_year = 12, year - 1
        else:
            prev_month, prev_year = month - 1, year
        prev_days = cal.monthrange(prev_year, prev_month)[1]
        for i in range(first_weekday_sun):
            day_num = prev_days - first_weekday_sun + 1 + i
            calendar_days.append({
                'day': day_num,
                'other_month': True,
                'is_today': False,
                'events': [],
            })

    days_in_month = cal.monthrange(year, month)[1]
    for d in range(1, days_in_month + 1):
        calendar_days.append({
            'day': d,
            'other_month': False,
            'is_today': (d == today.day and month == today.month and year == today.year),
            'events': leave_map.get(d, []),
        })

    remaining = 42 - len(calendar_days)
    for i in range(1, remaining + 1):
        calendar_days.append({
            'day': i,
            'other_month': True,
            'is_today': False,
            'events': [],
        })

    context = {
        'active_page': 'calendar',
        'calendar_days': calendar_days,
        'month': month,
        'year': year,
        'month_name': month_name,
    }
    return render(request, 'calendar.html', context)


@login_required
def admin_dashboard(request):
    if not request.user.is_staff:
        return HttpResponse("Unauthorized Access")

    search = request.GET.get('search')
    leaves = LeaveRequest.objects.all().order_by('-applied_on')

    if search:
        leaves = leaves.filter(employee__name__icontains=search)

    context = {
        'active_page': 'admin_dashboard',
        'leaves': leaves,
        'total': leaves.count(),
        'pending': leaves.filter(status='Pending').count(),
        'approved': leaves.filter(status='Approved').count(),
        'rejected': leaves.filter(status='Rejected').count(),
    }

    return render(request, 'admin_dashboard.html', context)


@login_required
def approve_leave(request, leave_id):
    if not request.user.is_staff:
        return HttpResponse("Unauthorized Access", status=403)

    leave = get_object_or_404(LeaveRequest, id=leave_id)
    leave.status = 'Approved'
    leave.save()

    recipient_email = leave.employee.email
    if not recipient_email and hasattr(leave.employee, 'user') and leave.employee.user:
        recipient_email = leave.employee.user.email

    logger.info(
        f"[APPROVE] Leave #{leave_id} | Employee: {leave.employee.name} | Email: '{recipient_email}'"
    )

    if recipient_email:
        try:
            send_mail(
                'Leave Approved',
                f'Dear {leave.employee.name},\n\n'
                f'Your leave request from {leave.start_date} to {leave.end_date} has been approved.\n\n'
                f'Regards,\nHR Department',
                settings.EMAIL_HOST_USER,
                [recipient_email],
                fail_silently=False,
            )
            logger.info(f"[APPROVE] Email sent successfully to {recipient_email}")
        except Exception as e:
            logger.error(f"[APPROVE] Email FAILED for leave #{leave_id}: {e}")
    else:
        logger.warning(
            f"[APPROVE] No email found for employee '{leave.employee.name}' — skipping notification"
        )

    messages.success(request, f'Leave request for {leave.employee.name} has been approved.')
    return redirect('admin_dashboard')


@login_required
def reject_leave(request, leave_id):
    if not request.user.is_staff:
        return HttpResponse("Unauthorized Access", status=403)

    leave = get_object_or_404(LeaveRequest, id=leave_id)
    leave.status = 'Rejected'
    leave.save()

    recipient_email = leave.employee.email
    if not recipient_email and hasattr(leave.employee, 'user') and leave.employee.user:
        recipient_email = leave.employee.user.email

    logger.info(
        f"[REJECT] Leave #{leave_id} | Employee: {leave.employee.name} | Email: '{recipient_email}'"
    )

    if recipient_email:
        try:
            send_mail(
                'Leave Rejected',
                f'Dear {leave.employee.name},\n\n'
                f'Your leave request from {leave.start_date} to {leave.end_date} has been rejected.\n\n'
                f'Regards,\nHR Department',
                settings.EMAIL_HOST_USER,
                [recipient_email],
                fail_silently=False,
            )
            logger.info(f"[REJECT] Email sent successfully to {recipient_email}")
        except Exception as e:
            logger.error(f"[REJECT] Email FAILED for leave #{leave_id}: {e}")
    else:
        logger.warning(
            f"[REJECT] No email found for employee '{leave.employee.name}' — skipping notification"
        )

    messages.error(request, f'Leave request for {leave.employee.name} has been rejected.')
    return redirect('admin_dashboard')


def register_view(request):
    if request.method == 'POST':
        username = request.POST.get('username')
        email = request.POST.get('email')
        password = request.POST.get('password')

        if User.objects.filter(username=username).exists():
            messages.error(request, 'Username already exists.')
            return render(request, 'register.html')

        if User.objects.filter(email=email).exists():
            messages.error(request, 'Email already registered.')
            return render(request, 'register.html')

        user = User.objects.create_user(
            username=username,
            email=email,
            password=password
        )

        Employee.objects.create(
            user=user,
            name=username,
            email=email,
            department='General',
            role='Employee',
        )

        messages.success(request, 'Account created successfully! Please login.')
        return redirect('login')

    return render(request, 'register.html')
