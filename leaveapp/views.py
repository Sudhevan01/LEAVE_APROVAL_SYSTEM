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