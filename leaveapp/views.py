import logging
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


def landing_view(request):
    return render(request, 'landing.html')


def login_view(request):
    role = request.GET.get('role', request.POST.get('role', 'employee'))

    if request.method == 'POST':

        username = request.POST.get('username')
        password = request.POST.get('password')

        user = authenticate(
            request,
            username=username,
            password=password
        )

        if user is not None:

            login(request, user)
            role = request.POST.get('role', 'employee')
            if role == 'admin' and user.is_staff:
                return redirect('admin_dashboard')
            else:
                return redirect('dashboard')

    return render(request, 'login.html', {'role': role})


def logout_view(request):

    logout(request)

    return redirect('landing')


@login_required
def dashboard(request):

    # FIX: Get employee linked to the LOGGED-IN user, not first() in DB
    try:
        employee = Employee.objects.get(user=request.user)
    except Employee.DoesNotExist:
        return HttpResponse(
            "Employee profile not found. Please contact admin.",
            status=404
        )

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

        return redirect('dashboard')

    leaves = LeaveRequest.objects.filter(employee=employee)

    context = {
        'leaves': leaves,
        'total_leaves': leaves.count(),
        'pending_leaves': leaves.filter(status='Pending').count(),
        'approved_leaves': leaves.filter(status='Approved').count(),
        'rejected_leaves': leaves.filter(status='Rejected').count(),
    }

    return render(request, 'dashboard.html', context)


@login_required
def admin_dashboard(request):

    if not request.user.is_staff:
        return HttpResponse("Unauthorized Access")

    search = request.GET.get('search')

    leaves = LeaveRequest.objects.all()

    if search:
        leaves = leaves.filter(
            employee__name__icontains=search
        )

    context = {
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

    # Resolve recipient email — prefer Employee.email, fall back to linked User.email
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

    return redirect('admin_dashboard')


@login_required
def reject_leave(request, leave_id):

    if not request.user.is_staff:
        return HttpResponse("Unauthorized Access", status=403)

    leave = get_object_or_404(LeaveRequest, id=leave_id)
    leave.status = 'Rejected'
    leave.save()

    # Resolve recipient email — prefer Employee.email, fall back to linked User.email
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

    return redirect('admin_dashboard')


def register_view(request):

    if request.method == 'POST':

        username = request.POST.get('username')
        email = request.POST.get('email')
        password = request.POST.get('password')

        user = User.objects.create_user(
            username=username,
            email=email,
            password=password
        )

        # FIX: Create an Employee record linked to this User
        Employee.objects.create(
            user=user,
            name=username,
            email=email,
            department='General',
            role='Employee',
        )

        return redirect('login')

    return render(request, 'register.html')
