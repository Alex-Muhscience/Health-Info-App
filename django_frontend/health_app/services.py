"""
Service to communicate with the Flask backend API.
"""

import requests
import logging
from django.conf import settings
from typing import Dict, Any, Optional

logger = logging.getLogger(__name__)


class FlaskBackendService:
    """Service class to handle communication with Flask backend"""
    
    def __init__(self):
        self.base_url = settings.FLASK_API_URL
        self.session = requests.Session()
        self.session.headers.update({
            'Content-Type': 'application/json',
            'Accept': 'application/json'
        })
    
    def _make_request(self, method: str, endpoint: str, data: Optional[Dict] = None, 
                     token: Optional[str] = None) -> Dict[str, Any]:
        """Make a request to the Flask backend"""
        url = f"{self.base_url}/{endpoint.lstrip('/')}"
        headers = {}
        
        if token:
            headers['Authorization'] = f'Bearer {token}'
        
        try:
            response = self.session.request(
                method=method.upper(),
                url=url,
                json=data,
                headers=headers,
                timeout=30
            )
            
            if response.status_code == 200:
                return {
                    'success': True,
                    'data': response.json()
                }
            else:
                error_msg = response.json().get('error', 'Unknown error') if response.text else 'Request failed'
                return {
                    'success': False,
                    'message': error_msg,
                    'status_code': response.status_code
                }
                
        except requests.exceptions.RequestException as e:
            logger.error(f"Request to Flask backend failed: {e}")
            return {
                'success': False,
                'message': f'Connection error: {str(e)}'
            }
        except Exception as e:
            logger.error(f"Unexpected error: {e}")
            return {
                'success': False,
                'message': f'Unexpected error: {str(e)}'
            }
    
    def authenticate(self, username: str, password: str) -> Dict[str, Any]:
        """Authenticate user with Flask backend"""
        data = {
            'username': username,
            'password': password
        }
        
        result = self._make_request('POST', 'auth/login', data)
        
        if result['success']:
            user_data = result['data']
            return {
                'success': True,
                'token': user_data.get('access_token'),
                'user': user_data.get('user', {}),
                'message': 'Login successful'
            }
        else:
            return {
                'success': False,
                'message': result.get('message', 'Authentication failed')
            }
    
    def get_dashboard_data(self, token: str) -> Dict[str, Any]:
        """Get dashboard data from Flask backend"""
        result = self._make_request('GET', 'dashboard/stats', token=token)
        
        if result['success']:
            return result['data']
        else:
            logger.error(f"Failed to get dashboard data: {result.get('message')}")
            return {
                'total_clients': 0,
                'total_appointments': 0,
                'total_visits': 0,
                'recent_activities': []
            }
    
    def get_clients(self, token: str) -> list:
        """Get clients list from Flask backend"""
        result = self._make_request('GET', 'clients', token=token)
        
        if result['success']:
            return result['data'].get('clients', [])
        else:
            logger.error(f"Failed to get clients: {result.get('message')}")
            return []
    
    def get_client(self, client_id: str, token: str) -> Optional[Dict]:
        """Get specific client from Flask backend"""
        result = self._make_request('GET', f'clients/{client_id}', token=token)
        
        if result['success']:
            return result['data']
        else:
            logger.error(f"Failed to get client {client_id}: {result.get('message')}")
            return None
    
    def create_client(self, client_data: Dict, token: str) -> Dict[str, Any]:
        """Create new client via Flask backend"""
        result = self._make_request('POST', 'clients', data=client_data, token=token)
        
        if result['success']:
            return {
                'success': True,
                'client': result['data'],
                'message': 'Client created successfully'
            }
        else:
            return {
                'success': False,
                'message': result.get('message', 'Failed to create client')
            }
    
    def get_appointments(self, token: str) -> list:
        """Get appointments list from Flask backend"""
        result = self._make_request('GET', 'appointments', token=token)
        
        if result['success']:
            return result['data'].get('appointments', [])
        else:
            logger.error(f"Failed to get appointments: {result.get('message')}")
            return []
    
    def get_visits(self, token: str) -> list:
        """Get visits list from Flask backend"""
        result = self._make_request('GET', 'visits', token=token)
        
        if result['success']:
            return result['data'].get('visits', [])
        else:
            logger.error(f"Failed to get visits: {result.get('message')}")
            return []
    
    def get_programs(self, token: str) -> list:
        """Get programs list from Flask backend"""
        result = self._make_request('GET', 'programs', token=token)
        
        if result['success']:
            return result['data']
        else:
            logger.error(f"Failed to get programs: {result.get('message')}")
            return []
    
    def get_staff(self, token: str) -> list:
        """Get staff list from Flask backend"""
        result = self._make_request('GET', 'staff', token=token)
        
        if result['success']:
            return result['data']
        else:
            logger.error(f"Failed to get staff: {result.get('message')}")
            return []
    
    def get_departments(self, token: str) -> list:
        """Get departments list from Flask backend"""
        result = self._make_request('GET', 'departments', token=token)
        
        if result['success']:
            return result['data']
        else:
            logger.error(f"Failed to get departments: {result.get('message')}")
            return []
    
    def get_medical_records(self, token: str, client_id: str = None) -> list:
        """Get medical records from Flask backend"""
        endpoint = f'medical-records?client_id={client_id}' if client_id else 'medical-records'
        result = self._make_request('GET', endpoint, token=token)
        
        if result['success']:
            return result['data']
        else:
            logger.error(f"Failed to get medical records: {result.get('message')}")
            return []
    
    def get_comprehensive_analytics(self, token: str, days: int = 30) -> Dict[str, Any]:
        """Get comprehensive analytics dashboard data from Flask backend"""
        result = self._make_request('GET', f'analytics/dashboard/comprehensive?days={days}', token=token)
        
        if result['success']:
            return result['data']
        else:
            logger.error(f"Failed to get comprehensive analytics: {result.get('message')}")
            return {}
    
    def get_patient_flow_analytics(self, token: str, days: int = 30) -> Dict[str, Any]:
        """Get patient flow analytics from Flask backend"""
        result = self._make_request('GET', f'analytics/patient-flow?days={days}', token=token)
        
        if result['success']:
            return result['data']
        else:
            logger.error(f"Failed to get patient flow analytics: {result.get('message')}")
            return {}
    
    def get_revenue_analytics(self, token: str, days: int = 30) -> Dict[str, Any]:
        """Get revenue analytics from Flask backend"""
        result = self._make_request('GET', f'analytics/revenue?days={days}', token=token)
        
        if result['success']:
            return result['data']
        else:
            logger.error(f"Failed to get revenue analytics: {result.get('message')}")
            return {}
    
    def get_clinical_quality_metrics(self, token: str, days: int = 30) -> Dict[str, Any]:
        """Get clinical quality metrics from Flask backend"""
        result = self._make_request('GET', f'analytics/clinical-quality?days={days}', token=token)
        
        if result['success']:
            return result['data']
        else:
            logger.error(f"Failed to get clinical quality metrics: {result.get('message')}")
            return {}
    
    def get_operational_efficiency(self, token: str) -> Dict[str, Any]:
        """Get operational efficiency metrics from Flask backend"""
        result = self._make_request('GET', 'analytics/operational-efficiency', token=token)
        
        if result['success']:
            return result['data']
        else:
            logger.error(f"Failed to get operational efficiency: {result.get('message')}")
            return {}
    
    def get_predictive_insights(self, token: str, days: int = 90) -> Dict[str, Any]:
        """Get predictive insights from Flask backend"""
        result = self._make_request('GET', f'analytics/predictive-insights?days={days}', token=token)
        
        if result['success']:
            return result['data']
        else:
            logger.error(f"Failed to get predictive insights: {result.get('message')}")
            return {}
    
    def get_lab_orders(self, token: str) -> list:
        """Get lab orders from Flask backend"""
        result = self._make_request('GET', 'lab-orders', token=token)
        
        if result['success']:
            return result['data']
        else:
            logger.error(f"Failed to get lab orders: {result.get('message')}")
            return []
    
    def get_medications(self, token: str) -> list:
        """Get medications from Flask backend"""
        result = self._make_request('GET', 'medications', token=token)
        
        if result['success']:
            return result['data']
        else:
            logger.error(f"Failed to get medications: {result.get('message')}")
            return []
    
    def get_prescriptions(self, token: str) -> list:
        """Get prescriptions from Flask backend"""
        result = self._make_request('GET', 'prescriptions', token=token)
        
        if result['success']:
            return result['data']
        else:
            logger.error(f"Failed to get prescriptions: {result.get('message')}")
            return []
    
    def get_admissions(self, token: str) -> list:
        """Get admissions from Flask backend"""
        result = self._make_request('GET', 'admissions', token=token)
        
        if result['success']:
            return result['data']
        else:
            logger.error(f"Failed to get admissions: {result.get('message')}")
            return []
    
    def get_billing(self, token: str) -> list:
        """Get billing records from Flask backend"""
        result = self._make_request('GET', 'billing', token=token)
        
        if result['success']:
            return result['data']
        else:
            logger.error(f"Failed to get billing records: {result.get('message')}")
            return []
    
    def create_appointment(self, appointment_data: Dict, token: str) -> Dict[str, Any]:
        """Create new appointment via Flask backend"""
        result = self._make_request('POST', 'appointments', data=appointment_data, token=token)
        
        if result['success']:
            return {
                'success': True,
                'appointment': result['data'],
                'message': 'Appointment created successfully'
            }
        else:
            return {
                'success': False,
                'message': result.get('message', 'Failed to create appointment')
            }
    
    def create_visit(self, visit_data: Dict, token: str) -> Dict[str, Any]:
        """Create new visit via Flask backend"""
        result = self._make_request('POST', 'visits', data=visit_data, token=token)
        
        if result['success']:
            return {
                'success': True,
                'visit': result['data'],
                'message': 'Visit created successfully'
            }
        else:
            return {
                'success': False,
                'message': result.get('message', 'Failed to create visit')
            }
    
    def make_request(self, endpoint: str, method: str = 'GET', 
                    data: Optional[Dict] = None, token: Optional[str] = None) -> Dict[str, Any]:
        """Generic method to make requests to Flask backend"""
        return self._make_request(method, endpoint, data, token)
