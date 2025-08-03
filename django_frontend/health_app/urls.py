"""
URL configuration for the health_app Django application.
"""

from django.urls import path
from . import views

urlpatterns = [
    # Authentication
    path('', views.home, name='home'),
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    
    # Dashboard
    path('dashboard/', views.dashboard, name='dashboard'),
    
    # Clients
    path('clients/', views.clients_list, name='clients_list'),
    path('clients/add/', views.add_client, name='add_client'),
    path('clients/<str:client_id>/', views.client_detail, name='client_detail'),
    
    # Appointments
    path('appointments/', views.appointments_list, name='appointments_list'),
    path('appointments/add/', views.add_appointment, name='add_appointment'),
    
    # Visits
    path('visits/', views.visits_list, name='visits_list'),
    path('visits/add/', views.add_visit, name='add_visit'),
    
    # Programs
    path('programs/', views.programs_list, name='programs_list'),
    
    # Staff Management
    path('staff/', views.staff_list, name='staff_list'),
    
    # Departments
    path('departments/', views.departments_list, name='departments_list'),
    
    # Medical Records
    path('medical-records/', views.medical_records_list, name='medical_records_list'),
    
    # Laboratory
    path('laboratory/', views.laboratory_list, name='laboratory_list'),
    
    # Pharmacy
    path('pharmacy/', views.pharmacy_list, name='pharmacy_list'),
    
    # Hospital Admissions
    path('admissions/', views.admissions_list, name='admissions_list'),
    
    # Billing & Insurance
    path('billing/', views.billing_list, name='billing_list'),
    
    # Analytics
    path('analytics/', views.comprehensive_analytics, name='comprehensive_analytics'),
    path('analytics/patient-flow/', views.patient_flow_analytics, name='patient_flow_analytics'),
    path('analytics/revenue/', views.revenue_analytics, name='revenue_analytics'),
    path('analytics/clinical-quality/', views.clinical_quality_metrics, name='clinical_quality_metrics'),
    path('analytics/operational/', views.operational_efficiency, name='operational_efficiency'),
    path('analytics/predictive/', views.predictive_insights, name='predictive_insights'),
    
    # API proxy
    path('api/proxy/', views.api_proxy, name='api_proxy'),
]
