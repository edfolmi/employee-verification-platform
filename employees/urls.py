"""
URL configuration for employees app.
"""
from django.urls import path
from . import views

urlpatterns = [
    path('', views.home, name='home'),
    path('add/', views.add_employee, name='add_employee'),
    path('verify/', views.verify_employee, name='verify_employee'),
    path('employees/', views.employee_list, name='employee_list'),
]
