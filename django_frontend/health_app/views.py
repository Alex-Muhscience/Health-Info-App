"""
Django views for the Health Management System frontend.
These views handle the UI and proxy requests to the Flask backend.
"""

import requests
import json
import logging
from datetime import datetime, timedelta
from django.shortcuts import render, redirect
from django.contrib.auth import login, logout
# from django.contrib.auth.decorators import login_required  # Not using Django auth
from django.contrib import messages
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.conf import settings
from django.views.decorators.http import require_http_methods
from .models import UserSession
from .services import FlaskBackendService

logger = logging.getLogger(__name__)


def flask_auth_required(view_func):
    """Custom decorator to check Flask authentication"""
    def wrapper(request, *args, **kwargs):
        if 'flask_token' not in request.session:
            messages.error(request, 'Please log in to access this page.')
            return redirect('login')
        return view_func(request, *args, **kwargs)
    return wrapper


def home(request):
    """Home page view"""
    return render(request, 'health_app/home.html')


def login_view(request):
    """Login page view"""
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        
        # Authenticate with Flask backend
        backend_service = FlaskBackendService()
        auth_result = backend_service.authenticate(username, password)
        
        if auth_result['success']:
            # Store the Flask token in session
            request.session['flask_token'] = auth_result['token']
            request.session['flask_user'] = auth_result['user']
            messages.success(request, 'Successfully logged in!')
            return redirect('dashboard')
        else:
            messages.error(request, auth_result['message'])
    
    return render(request, 'health_app/login.html')


def logout_view(request):
    """Logout view"""
    # Clear Flask token from session
    if 'flask_token' in request.session:
        del request.session['flask_token']
    if 'flask_user' in request.session:
        del request.session['flask_user']
    
    messages.success(request, 'Successfully logged out!')
    return redirect('login')


@flask_auth_required
def dashboard(request):
    """Dashboard view"""
    # Get dashboard data from Flask backend
    backend_service = FlaskBackendService()
    dashboard_data = backend_service.get_dashboard_data(request.session['flask_token'])
    
    context = {
        'user': request.session.get('flask_user', {}),
        'dashboard_data': dashboard_data
    }
    return render(request, 'health_app/dashboard.html', context)


@flask_auth_required
def clients_list(request):
    """Clients list view"""
    try:
        backend_service = FlaskBackendService()
        response = backend_service.get_clients(request.session['flask_token'])
        
        # Handle search and filtering
        search = request.GET.get('search', '')
        gender = request.GET.get('gender', '')
        status = request.GET.get('status', '')
        
        # Extract clients from response
        if isinstance(response, dict) and 'clients' in response:
            clients = response['clients']
        elif isinstance(response, list):
            clients = response
        else:
            clients = []
        
        # Apply client-side filtering if needed
        if search:
            clients = [c for c in clients if search.lower() in f"{c.get('first_name', '')} {c.get('last_name', '')}".lower()]
        if gender:
            clients = [c for c in clients if c.get('gender') == gender]
        
        context = {
            'clients': clients,
            'search': search,
            'gender': gender,
            'status': status,
            'total_clients': len(clients)
        }
        return render(request, 'health_app/clients/list.html', context)
    except Exception as e:
        messages.error(request, f'Error loading clients: {str(e)}')
        return render(request, 'health_app/clients/list.html', {'clients': [], 'total_clients': 0})


@flask_auth_required
def client_detail(request, client_id):
    """Client detail view"""
    backend_service = FlaskBackendService()
    client = backend_service.get_client(client_id, request.session['flask_token'])
    
    if not client:
        messages.error(request, 'Client not found.')
        return redirect('clients_list')
    
    context = {
        'client': client
    }
    return render(request, 'health_app/clients/detail.html', context)


@flask_auth_required
def add_client(request):
    """Add new client view"""
    if request.method == 'POST':
        backend_service = FlaskBackendService()
        client_data = {
            'first_name': request.POST.get('first_name'),
            'last_name': request.POST.get('last_name'),
            'dob': request.POST.get('dob'),
            'gender': request.POST.get('gender'),
            'phone': request.POST.get('phone'),
            'email': request.POST.get('email'),
            'address': request.POST.get('address'),
            'emergency_contact_name': request.POST.get('emergency_contact_name'),
            'emergency_contact_phone': request.POST.get('emergency_contact_phone'),
            'notes': request.POST.get('notes', '')
        }
        
        result = backend_service.create_client(client_data, request.session['flask_token'])
        
        if result['success']:
            messages.success(request, 'Client added successfully!')
            return redirect('client_detail', client_id=result['client']['id'])
        else:
            messages.error(request, result['message'])
    
    return render(request, 'health_app/clients/add.html')


@flask_auth_required
def appointments_list(request):
    """Appointments list view"""
    try:
        backend_service = FlaskBackendService()
        response = backend_service.get_appointments(request.session['flask_token'])
        
        # Extract appointments from response
        if isinstance(response, dict) and 'appointments' in response:
            appointments = response['appointments']
        elif isinstance(response, list):
            appointments = response
        else:
            appointments = []
        
        # Handle filtering by status
        status_filter = request.GET.get('status', '')
        if status_filter:
            appointments = [a for a in appointments if a.get('status') == status_filter]
        
        context = {
            'appointments': appointments,
            'status_filter': status_filter,
            'total_appointments': len(appointments)
        }
        return render(request, 'health_app/appointments/list.html', context)
    except Exception as e:
        messages.error(request, f'Error loading appointments: {str(e)}')
        return render(request, 'health_app/appointments/list.html', {'appointments': [], 'total_appointments': 0})


@flask_auth_required
def comprehensive_analytics(request):
    """Comprehensive analytics dashboard view"""
    try:
        backend_service = FlaskBackendService()
        token = request.session['flask_token']
        
        # Get analytics data from Flask backend
        days = request.GET.get('days', 30)
        analytics_data = backend_service.get_comprehensive_analytics(token, days)
        
        context = {
            'analytics_data': analytics_data,
            'period_days': days,
            'user': request.session.get('flask_user', {})
        }
        return render(request, 'health_app/analytics/dashboard.html', context)
    except Exception as e:
        logger.error(f'Error loading comprehensive analytics: {str(e)}')
        messages.error(request, f'Error loading analytics: {str(e)}')
        return render(request, 'health_app/analytics/dashboard.html', {'analytics_data': {}, 'period_days': 30})


@flask_auth_required
def patient_flow_analytics(request):
    """Patient flow analytics view"""
    try:
        backend_service = FlaskBackendService()
        token = request.session['flask_token']
        
        days = request.GET.get('days', 30)
        flow_data = backend_service.get_patient_flow_analytics(token, days)
        
        context = {
            'flow_data': flow_data,
            'period_days': days
        }
        return render(request, 'health_app/analytics/patient_flow.html', context)
    except Exception as e:
        logger.error(f'Error loading patient flow analytics: {str(e)}')
        messages.error(request, f'Error loading patient flow data: {str(e)}')
        return render(request, 'health_app/analytics/patient_flow.html', {'flow_data': {}, 'period_days': 30})


@flask_auth_required
def revenue_analytics(request):
    """Revenue analytics view"""
    try:
        backend_service = FlaskBackendService()
        token = request.session['flask_token']
        
        days = request.GET.get('days', 30)
        revenue_data = backend_service.get_revenue_analytics(token, days)
        
        context = {
            'revenue_data': revenue_data,
            'period_days': days
        }
        return render(request, 'health_app/analytics/revenue.html', context)
    except Exception as e:
        logger.error(f'Error loading revenue analytics: {str(e)}')
        messages.error(request, f'Error loading revenue data: {str(e)}')
        return render(request, 'health_app/analytics/revenue.html', {'revenue_data': {}, 'period_days': 30})


@flask_auth_required
def clinical_quality_metrics(request):
    """Clinical quality metrics view"""
    try:
        backend_service = FlaskBackendService()
        token = request.session['flask_token']
        
        days = request.GET.get('days', 30)
        quality_data = backend_service.get_clinical_quality_metrics(token, days)
        
        context = {
            'quality_data': quality_data,
            'period_days': days
        }
        return render(request, 'health_app/analytics/clinical_quality.html', context)
    except Exception as e:
        logger.error(f'Error loading clinical quality metrics: {str(e)}')
        messages.error(request, f'Error loading quality metrics: {str(e)}')
        return render(request, 'health_app/analytics/clinical_quality.html', {'quality_data': {}, 'period_days': 30})


@flask_auth_required
def operational_efficiency(request):
    """Operational efficiency metrics view"""
    try:
        backend_service = FlaskBackendService()
        token = request.session['flask_token']
        
        efficiency_data = backend_service.get_operational_efficiency(token)
        
        context = {
            'efficiency_data': efficiency_data
        }
        return render(request, 'health_app/analytics/operational_efficiency.html', context)
    except Exception as e:
        logger.error(f'Error loading operational efficiency: {str(e)}')
        messages.error(request, f'Error loading efficiency data: {str(e)}')
        return render(request, 'health_app/analytics/operational_efficiency.html', {'efficiency_data': {}})


@flask_auth_required
def predictive_insights(request):
    """Predictive insights view"""
    try:
        backend_service = FlaskBackendService()
        token = request.session['flask_token']
        
        days = request.GET.get('days', 90)
        insights_data = backend_service.get_predictive_insights(token, days)
        
        context = {
            'insights_data': insights_data,
            'period_days': days
        }
        return render(request, 'health_app/analytics/predictive_insights.html', context)
    except Exception as e:
        logger.error(f'Error loading predictive insights: {str(e)}')
        messages.error(request, f'Error loading insights data: {str(e)}')
        return render(request, 'health_app/analytics/predictive_insights.html', {'insights_data': {}, 'period_days': 90})


@flask_auth_required
def visits_list(request):
    """Visits list view"""
    try:
        backend_service = FlaskBackendService()
        response = backend_service.get_visits(request.session['flask_token'])
        
        # Extract visits from response
        if isinstance(response, dict) and 'visits' in response:
            visits = response['visits']
        elif isinstance(response, list):
            visits = response
        else:
            visits = []
        
        # Handle filtering
        client_id = request.GET.get('client_id', '')
        if client_id:
            visits = [v for v in visits if str(v.get('client_id')) == client_id]
        
        context = {
            'visits': visits,
            'client_id': client_id,
            'total_visits': len(visits)
        }
        return render(request, 'health_app/visits/list.html', context)
    except Exception as e:
        messages.error(request, f'Error loading visits: {str(e)}')
        return render(request, 'health_app/visits/list.html', {'visits': [], 'total_visits': 0})


@flask_auth_required
def programs_list(request):
    """Programs list view"""
    backend_service = FlaskBackendService()
    programs = backend_service.get_programs(request.session['flask_token'])
    
    context = {
        'programs': programs
    }
    return render(request, 'health_app/programs/list.html', context)


@flask_auth_required
def add_appointment(request):
    """Add new appointment view"""
    if request.method == 'POST':
        backend_service = FlaskBackendService()
        appointment_data = {
            'client_id': request.POST.get('client_id'),
            'date': request.POST.get('date'),
            'reason': request.POST.get('reason'),
            'duration_minutes': request.POST.get('duration_minutes', 30),
            'notes': request.POST.get('notes', '')
        }
        
        result = backend_service.create_appointment(appointment_data, request.session['flask_token'])
        
        if result['success']:
            messages.success(request, 'Appointment scheduled successfully!')
            return redirect('appointments_list')
        else:
            messages.error(request, result['message'])
    
    # Get clients for dropdown
    backend_service = FlaskBackendService()
    clients = backend_service.get_clients(request.session['flask_token'])
    
    context = {
        'clients': clients
    }
    return render(request, 'health_app/appointments/add.html', context)


@flask_auth_required
def add_visit(request):
    """Add new visit view"""
    if request.method == 'POST':
        backend_service = FlaskBackendService()
        visit_data = {
            'client_id': request.POST.get('client_id'),
            'visit_date': request.POST.get('visit_date'),
            'reason': request.POST.get('reason'),
            'notes': request.POST.get('notes', ''),
            'vital_signs': {
                'blood_pressure_systolic': request.POST.get('blood_pressure_systolic'),
                'blood_pressure_diastolic': request.POST.get('blood_pressure_diastolic'),
                'heart_rate': request.POST.get('heart_rate'),
                'temperature': request.POST.get('temperature'),
                'weight': request.POST.get('weight'),
                'height': request.POST.get('height')
            }
        }
        
        result = backend_service.create_visit(visit_data, request.session['flask_token'])
        
        if result['success']:
            messages.success(request, 'Visit recorded successfully!')
            return redirect('visits_list')
        else:
            messages.error(request, result['message'])
    
    # Get clients for dropdown
    backend_service = FlaskBackendService()
    clients = backend_service.get_clients(request.session['flask_token'])
    
    context = {
        'clients': clients
    }
    return render(request, 'health_app/visits/add_visit.html', context)


@flask_auth_required
def staff_list(request):
    """Staff list view with enhanced error handling and filtering."""
    try:
        backend_service = FlaskBackendService()
        response = backend_service.get_staff(request.session['flask_token'])
        
        # Extract staff from response
        if isinstance(response, dict) and 'staff' in response:
            staff = response['staff']
        elif isinstance(response, list):
            staff = response
        else:
            staff = []
        
        # Handle filtering
        department = request.GET.get('department', '')
        specialization = request.GET.get('specialization', '')
        employment_type = request.GET.get('employment_type', '')
        
        if department:
            staff = [s for s in staff if s.get('department_name', '').lower() == department.lower()]
        if specialization:
            staff = [s for s in staff if s.get('specialization', '').lower() == specialization.lower()]
        if employment_type:
            staff = [s for s in staff if s.get('employment_type', '').lower() == employment_type.lower()]
        
        context = {
            'staff': staff,
            'department': department,
            'specialization': specialization,
            'employment_type': employment_type,
            'total_staff': len(staff)
        }
        return render(request, 'health_app/staff/list.html', context)
    except Exception as e:
        logger.error(f"Error loading staff: {e}")
        messages.error(request, f'Error loading staff: {str(e)}')
        return render(request, 'health_app/staff/list.html', {'staff': [], 'total_staff': 0})


@flask_auth_required
def departments_list(request):
    """Departments list view with enhanced error handling."""
    try:
        backend_service = FlaskBackendService()
        response = backend_service.get_departments(request.session['flask_token'])
        
        # Extract departments from response
        if isinstance(response, dict) and 'departments' in response:
            departments = response['departments']
        elif isinstance(response, list):
            departments = response
        else:
            departments = []
        
        # Handle filtering
        location = request.GET.get('location', '')
        is_active = request.GET.get('is_active', '')
        
        if location:
            departments = [d for d in departments if location.lower() in d.get('location', '').lower()]
        if is_active:
            active_filter = is_active.lower() == 'true'
            departments = [d for d in departments if d.get('is_active', True) == active_filter]
        
        context = {
            'departments': departments,
            'location': location,
            'is_active': is_active,
            'total_departments': len(departments)
        }
        return render(request, 'health_app/departments/list.html', context)
    except Exception as e:
        logger.error(f"Error loading departments: {e}")
        messages.error(request, f'Error loading departments: {str(e)}')
        return render(request, 'health_app/departments/list.html', {'departments': [], 'total_departments': 0})


@flask_auth_required
def medical_records_list(request):
    """Medical records list view with enhanced error handling."""
    try:
        backend_service = FlaskBackendService()
        client_id = request.GET.get('client_id')
        response = backend_service.get_medical_records(request.session['flask_token'], client_id)
        
        # Extract medical records from response
        if isinstance(response, dict) and 'medical_records' in response:
            medical_records = response['medical_records']
        elif isinstance(response, list):
            medical_records = response
        else:
            medical_records = []
        
        # Additional filtering
        date_from = request.GET.get('date_from', '')
        date_to = request.GET.get('date_to', '')
        
        if date_from or date_to:
            # Client-side date filtering (if needed)
            pass
        
        context = {
            'medical_records': medical_records,
            'client_id': client_id,
            'date_from': date_from,
            'date_to': date_to,
            'total_records': len(medical_records)
        }
        return render(request, 'health_app/medical_records/list.html', context)
    except Exception as e:
        logger.error(f"Error loading medical records: {e}")
        messages.error(request, f'Error loading medical records: {str(e)}')
        return render(request, 'health_app/medical_records/list.html', {'medical_records': [], 'total_records': 0})


@flask_auth_required
def laboratory_list(request):
    """Laboratory/Lab orders list view with enhanced error handling."""
    try:
        backend_service = FlaskBackendService()
        response = backend_service.get_lab_orders(request.session['flask_token'])
        
        # Extract lab orders from response
        if isinstance(response, dict) and 'lab_orders' in response:
            lab_orders = response['lab_orders']
        elif isinstance(response, list):
            lab_orders = response
        else:
            lab_orders = []
        
        # Handle filtering
        status = request.GET.get('status', '')
        priority = request.GET.get('priority', '')
        
        if status:
            lab_orders = [l for l in lab_orders if l.get('status', '').lower() == status.lower()]
        if priority:
            lab_orders = [l for l in lab_orders if l.get('priority', '').lower() == priority.lower()]
        
        context = {
            'lab_orders': lab_orders,
            'status': status,
            'priority': priority,
            'total_orders': len(lab_orders)
        }
        return render(request, 'health_app/laboratory/list.html', context)
    except Exception as e:
        logger.error(f"Error loading lab orders: {e}")
        messages.error(request, f'Error loading lab orders: {str(e)}')
        return render(request, 'health_app/laboratory/list.html', {'lab_orders': [], 'total_orders': 0})


@flask_auth_required
def pharmacy_list(request):
    """Pharmacy view with medications and prescriptions with enhanced error handling."""
    try:
        backend_service = FlaskBackendService()
        
        # Get prescriptions
        prescriptions_response = backend_service.get_prescriptions(request.session['flask_token'])
        if isinstance(prescriptions_response, dict) and 'prescriptions' in prescriptions_response:
            prescriptions = prescriptions_response['prescriptions']
        elif isinstance(prescriptions_response, list):
            prescriptions = prescriptions_response
        else:
            prescriptions = []
        
        # Get inventory/medications
        try:
            medications_response = backend_service.get_medications(request.session['flask_token'])
            if isinstance(medications_response, dict) and 'medications' in medications_response:
                medications = medications_response['medications']
            elif isinstance(medications_response, list):
                medications = medications_response
            else:
                medications = []
        except:
            medications = []  # In case medications endpoint doesn't exist
        
        # Handle filtering
        status = request.GET.get('status', '')
        if status:
            prescriptions = [p for p in prescriptions if p.get('status', '').lower() == status.lower()]
        
        context = {
            'medications': medications,
            'prescriptions': prescriptions,
            'status': status,
            'total_prescriptions': len(prescriptions),
            'total_medications': len(medications)
        }
        return render(request, 'health_app/pharmacy/list.html', context)
    except Exception as e:
        logger.error(f"Error loading pharmacy data: {e}")
        messages.error(request, f'Error loading pharmacy data: {str(e)}')
        return render(request, 'health_app/pharmacy/list.html', {
            'medications': [], 'prescriptions': [], 
            'total_prescriptions': 0, 'total_medications': 0
        })


@flask_auth_required
def admissions_list(request):
    """Hospital admissions list view with enhanced error handling."""
    try:
        backend_service = FlaskBackendService()
        response = backend_service.get_admissions(request.session['flask_token'])
        
        # Extract admissions from response
        if isinstance(response, dict) and 'admissions' in response:
            admissions = response['admissions']
        elif isinstance(response, list):
            admissions = response
        else:
            admissions = []
        
        # Handle filtering
        status = request.GET.get('status', '')
        admission_type = request.GET.get('admission_type', '')
        
        if status:
            admissions = [a for a in admissions if a.get('status', '').lower() == status.lower()]
        if admission_type:
            admissions = [a for a in admissions if a.get('admission_type', '').lower() == admission_type.lower()]
        
        # Calculate statistics
        stats = {
            'total_admissions': len(admissions),
            'current_inpatients': len([a for a in admissions if a.get('status') == 'active']),
            'discharges_today': 0,  # Would need date filtering
            'pending_discharges': len([a for a in admissions if a.get('status') == 'pending'])
        }
        
        context = {
            'admissions': admissions,
            'status': status,
            'admission_type': admission_type,
            'stats': stats,
            'total_admissions': len(admissions)
        }
        return render(request, 'health_app/admissions/list.html', context)
    except Exception as e:
        logger.error(f"Error loading admissions: {e}")
        messages.error(request, f'Error loading admissions: {str(e)}')
        return render(request, 'health_app/admissions/list.html', {
            'admissions': [], 'total_admissions': 0, 
            'stats': {'total_admissions': 0, 'current_inpatients': 0, 'discharges_today': 0, 'pending_discharges': 0}
        })


@flask_auth_required
def billing_list(request):
    """Billing and invoices list view with enhanced error handling."""
    try:
        backend_service = FlaskBackendService()
        response = backend_service.get_billing(request.session['flask_token'])
        
        # Extract billing records from response
        if isinstance(response, dict) and 'billing_records' in response:
            billing_records = response['billing_records']
        elif isinstance(response, list):
            billing_records = response
        else:
            billing_records = []
        
        # Handle filtering
        status = request.GET.get('status', '')
        payment_method = request.GET.get('payment_method', '')
        
        if status:
            billing_records = [b for b in billing_records if b.get('status', '').lower() == status.lower()]
        if payment_method:
            billing_records = [b for b in billing_records if b.get('payment_method', '').lower() == payment_method.lower()]
        
        # Calculate statistics
        total_amount = sum(float(b.get('total_amount', 0)) for b in billing_records)
        paid_amount = sum(float(b.get('paid_amount', 0)) for b in billing_records)
        pending_bills = len([b for b in billing_records if b.get('status') == 'pending'])
        
        context = {
            'billing_records': billing_records,
            'status': status,
            'payment_method': payment_method,
            'total_records': len(billing_records),
            'total_amount': total_amount,
            'paid_amount': paid_amount,
            'pending_bills': pending_bills
        }
        return render(request, 'health_app/billing/list.html', context)
    except Exception as e:
        logger.error(f"Error loading billing records: {e}")
        messages.error(request, f'Error loading billing records: {str(e)}')
        return render(request, 'health_app/billing/list.html', {
            'billing_records': [], 'total_records': 0,
            'total_amount': 0, 'paid_amount': 0, 'pending_bills': 0
        })


# API endpoints for AJAX calls
@csrf_exempt
@require_http_methods(["POST"])
def api_proxy(request):
    """
    Proxy API calls to Flask backend
    """
    if 'flask_token' not in request.session:
        return JsonResponse({'error': 'Not authenticated'}, status=401)
    try:
        # Get the target endpoint from request
        endpoint = request.POST.get('endpoint')
        method = request.POST.get('method', 'GET')
        data = json.loads(request.POST.get('data', '{}'))
        
        if not endpoint:
            return JsonResponse({'error': 'Endpoint parameter is required'}, status=400)
        
        backend_service = FlaskBackendService()
        result = backend_service.make_request(
            endpoint=endpoint,
            method=method,
            data=data,
            token=request.session['flask_token']
        )
        
        return JsonResponse(result)
    except json.JSONDecodeError:
        return JsonResponse({'error': 'Invalid JSON data'}, status=400)
    except Exception as e:
        logger.error(f"API proxy error: {e}")
        return JsonResponse({'error': 'Internal server error'}, status=500)
