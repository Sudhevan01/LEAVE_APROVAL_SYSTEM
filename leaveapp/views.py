from django.shortcuts import render,redirect
# pyrefly: ignore [missing-import]
from .models import Employee,LeaveRequest

def login_view(request):
    return render(request, 'login.html')


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

def admin_dashboard(request):

    leaves = LeaveRequest.objects.all()

    context = {
        'leaves': leaves
    }

    return render(request, 'admin_dashboard.html', context)


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

    return render(request,
                  'admin_dashboard.html',
                  context)