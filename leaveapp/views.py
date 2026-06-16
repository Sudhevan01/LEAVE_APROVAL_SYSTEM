from django.contrib.auth.models import User
from django.http import HttpResponse
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.shortcuts import render,redirect
# pyrefly: ignore [missing-import]
from .models import Employee,LeaveRequest

def login_view(request):

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
            if user.isstaff:
                return redirect('admin-dashboard')
            else:
                return redirect('dashboard')
    return render(request, 'login.html')


def logout_view(request):

    logout(request)

    return redirect('login')

@login_required
def dashboard(request):

    employee = Employee.objects.first()

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

    leaves = LeaveRequest.objects.all()

    context = {
        'leaves': leaves,
        'total': leaves.count(),
        'pending': leaves.filter(status='Pending').count(),
        'approved': leaves.filter(status='Approved').count(),
        'rejected': leaves.filter(status='Rejected').count(),
    }

    return render(request,
                  'admin_dashboard.html',
                  context)


def approve_leave(request, leave_id):

    leave = LeaveRequest.objects.get(id=leave_id)

    leave.status = 'Approved'

    leave.save()

    return redirect('admin_dashboard')


def reject_leave(request, leave_id):

    leave = LeaveRequest.objects.get(id=leave_id)

    leave.status = 'Rejected'

    leave.save()

    return redirect('admin_dashboard')

def admin_dashboard(request):

    leaves = LeaveRequest.objects.all()

    context = {
        'leaves': leaves,
        'total': leaves.count(),
        'pending': leaves.filter(status='Pending').count(),
        'approved': leaves.filter(status='Approved').count(),
        'rejected': leaves.filter(status='Rejected').count(),
    }

    return render(request,
                  'admin_dashboard.html',
                  context)

def admin_dashboard(request):

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

    return render(request,'admin_dashboard.html',context)

def register_view(request):

    if request.method == 'POST':

        username = request.POST.get('username')
        email = request.POST.get('email')
        password = request.POST.get('password')

        User.objects.create_user(
            username=username,
            email=email,
            password=password
        )

        return redirect('login')

    return render(request, 'register.html')
