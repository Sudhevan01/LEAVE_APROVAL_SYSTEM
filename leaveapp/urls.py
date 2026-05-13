from django.urls import path
# pyrefly: ignore [missing-import]
from . import views

urlpatterns = [
    path('', views.login_view, name='login'),
]

urlpatterns = [
    path('', views.dashboard, name='dashboard'),
]