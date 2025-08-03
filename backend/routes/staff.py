from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from backend.database import db
from backend.models import Staff, Department, User
from backend.utils.helpers import handle_validation_error
from backend.utils.auth import role_required
from datetime import datetime
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

staff_bp = Blueprint('staff', __name__)


@staff_bp.route('/staff', methods=['GET'])
@jwt_required()
@role_required(['admin', 'doctor'])
def get_all_staff():
    """Get all staff members with filtering options."""
    try:
        # Get query parameters
        department_id = request.args.get('department_id')
        specialization = request.args.get('specialization')
        employment_type = request.args.get('employment_type')
        is_active = request.args.get('is_active', 'true').lower() == 'true'
        page = int(request.args.get('page', 1))
        per_page = min(int(request.args.get('per_page', 10)), 100)
        
        # Build query
        query = Staff.query
        
        if department_id:
            query = query.filter(Staff.department_id == department_id)
        if specialization:
            query = query.filter(Staff.specialization == specialization)
        if employment_type:
            query = query.filter(Staff.employment_type == employment_type)
        
        query = query.filter(Staff.is_active == is_active)
        
        # Apply pagination
        staff_list = query.paginate(
            page=page, per_page=per_page, error_out=False
        )
        
        result = []
        for staff in staff_list.items:
            staff_data = {
                'id': staff.id,
                'employee_id': staff.employee_id,
                'first_name': staff.first_name,
                'last_name': staff.last_name,
                'full_name': f"{staff.first_name} {staff.last_name}",
                'specialization': staff.specialization,
                'license_number': staff.license_number,
                'department': staff.department.name if staff.department else None,
                'phone': staff.phone,
                'email': staff.email,
                'employment_type': staff.employment_type,
                'hire_date': staff.hire_date.isoformat() if staff.hire_date else None,
                'is_active': staff.is_active,
                'created_at': staff.created_at.isoformat()
            }
            result.append(staff_data)
        
        return jsonify({
            'staff': result,
            'pagination': {
                'page': staff_list.page,
                'pages': staff_list.pages,
                'per_page': staff_list.per_page,
                'total': staff_list.total,
                'has_next': staff_list.has_next,
                'has_prev': staff_list.has_prev
            }
        }), 200
    
    except Exception as e:
        logger.error(f"Error fetching staff: {str(e)}")
        return jsonify({'error': 'Failed to fetch staff'}), 500


@staff_bp.route('/staff', methods=['POST'])
@jwt_required()
@role_required(['admin'])
def create_staff():
    """Create a new staff member."""
    try:
        data = request.get_json()
        
        # Validate required fields
        required_fields = ['employee_id', 'first_name', 'last_name', 'email']
        for field in required_fields:
            if not data.get(field):
                return jsonify({'error': f'{field} is required'}), 400
        
        # Check if employee ID already exists
        if Staff.query.filter_by(employee_id=data['employee_id']).first():
            return jsonify({'error': 'Employee ID already exists'}), 400
        
        # Create staff member
        staff = Staff(
            employee_id=data['employee_id'],
            first_name=data['first_name'],
            last_name=data['last_name'],
            specialization=data.get('specialization'),
            license_number=data.get('license_number'),
            department_id=data.get('department_id'),
            phone=data.get('phone'),
            email=data['email'],
            employment_type=data.get('employment_type', 'full_time'),
            hire_date=datetime.strptime(data['hire_date'], '%Y-%m-%d').date() if data.get('hire_date') else datetime.utcnow().date(),
            salary=data.get('salary')
        )
        
        db.session.add(staff)
        db.session.commit()
        
        logger.info(f"Created new staff member: {staff.employee_id}")
        
        return jsonify({
            'message': 'Staff member created successfully',
            'staff': {
                'id': staff.id,
                'employee_id': staff.employee_id,
                'first_name': staff.first_name,
                'last_name': staff.last_name,
                'email': staff.email
            }
        }), 201
    
    except ValueError as e:
        return handle_validation_error(e)
    except Exception as e:
        db.session.rollback()
        logger.error(f"Error creating staff: {str(e)}")
        return jsonify({'error': 'Failed to create staff member'}), 500


@staff_bp.route('/staff/<staff_id>', methods=['GET'])
@jwt_required()
@role_required(['admin', 'doctor'])
def get_staff(staff_id):
    """Get a specific staff member by ID."""
    try:
        staff = Staff.query.get_or_404(staff_id)
        
        return jsonify({
            'id': staff.id,
            'employee_id': staff.employee_id,
            'first_name': staff.first_name,
            'last_name': staff.last_name,
            'full_name': f"{staff.first_name} {staff.last_name}",
            'specialization': staff.specialization,
            'license_number': staff.license_number,
            'department_id': staff.department_id,
            'department': staff.department.name if staff.department else None,
            'phone': staff.phone,
            'email': staff.email,
            'employment_type': staff.employment_type,
            'hire_date': staff.hire_date.isoformat() if staff.hire_date else None,
            'salary': float(staff.salary) if staff.salary else None,
            'is_active': staff.is_active,
            'created_at': staff.created_at.isoformat(),
            'updated_at': staff.updated_at.isoformat()
        }), 200
    
    except Exception as e:
        logger.error(f"Error fetching staff {staff_id}: {str(e)}")
        return jsonify({'error': 'Staff member not found'}), 404


@staff_bp.route('/staff/<staff_id>', methods=['PUT'])
@jwt_required()
@role_required(['admin'])
def update_staff(staff_id):
    """Update a staff member."""
    try:
        staff = Staff.query.get_or_404(staff_id)
        data = request.get_json()
        
        # Update fields
        if 'first_name' in data:
            staff.first_name = data['first_name']
        if 'last_name' in data:
            staff.last_name = data['last_name']
        if 'specialization' in data:
            staff.specialization = data['specialization']
        if 'license_number' in data:
            staff.license_number = data['license_number']
        if 'department_id' in data:
            staff.department_id = data['department_id']
        if 'phone' in data:
            staff.phone = data['phone']
        if 'email' in data:
            staff.email = data['email']
        if 'employment_type' in data:
            staff.employment_type = data['employment_type']
        if 'salary' in data:
            staff.salary = data['salary']
        if 'is_active' in data:
            staff.is_active = data['is_active']
        
        db.session.commit()
        
        logger.info(f"Updated staff member: {staff.employee_id}")
        
        return jsonify({
            'message': 'Staff member updated successfully',
            'staff': {
                'id': staff.id,
                'employee_id': staff.employee_id,
                'first_name': staff.first_name,
                'last_name': staff.last_name,
                'email': staff.email
            }
        }), 200
    
    except ValueError as e:
        return handle_validation_error(e)
    except Exception as e:
        db.session.rollback()
        logger.error(f"Error updating staff {staff_id}: {str(e)}")
        return jsonify({'error': 'Failed to update staff member'}), 500


@staff_bp.route('/staff/<staff_id>', methods=['DELETE'])
@jwt_required()
@role_required(['admin'])
def delete_staff(staff_id):
    """Delete (deactivate) a staff member."""
    try:
        staff = Staff.query.get_or_404(staff_id)
        staff.is_active = False
        db.session.commit()
        
        logger.info(f"Deactivated staff member: {staff.employee_id}")
        
        return jsonify({'message': 'Staff member deactivated successfully'}), 200
    
    except Exception as e:
        db.session.rollback()
        logger.error(f"Error deleting staff {staff_id}: {str(e)}")
        return jsonify({'error': 'Failed to delete staff member'}), 500


@staff_bp.route('/departments', methods=['GET'])
@jwt_required()
def get_departments():
    """Get all active departments."""
    try:
        departments = Department.query.filter_by(is_active=True).all()
        
        result = []
        for dept in departments:
            dept_data = {
                'id': dept.id,
                'name': dept.name,
                'description': dept.description,
                'location': dept.location,
                'phone': dept.phone,
                'email': dept.email,
                'head': dept.head_id,
                'staff_count': len(dept.staff),
                'created_at': dept.created_at.isoformat()
            }
            result.append(dept_data)
        
        return jsonify({'departments': result}), 200
    
    except Exception as e:
        logger.error(f"Error fetching departments: {str(e)}")
        return jsonify({'error': 'Failed to fetch departments'}), 500


@staff_bp.route('/departments', methods=['POST'])
@jwt_required()
@role_required(['admin'])
def create_department():
    """Create a new department."""
    try:
        data = request.get_json()
        
        # Validate required fields
        if not data.get('name'):
            return jsonify({'error': 'Department name is required'}), 400
        
        # Check if department already exists
        if Department.query.filter_by(name=data['name']).first():
            return jsonify({'error': 'Department already exists'}), 400
        
        # Create department
        department = Department(
            name=data['name'],
            description=data.get('description'),
            location=data.get('location'),
            phone=data.get('phone'),
            email=data.get('email'),
            head_id=data.get('head_id')
        )
        
        db.session.add(department)
        db.session.commit()
        
        logger.info(f"Created new department: {department.name}")
        
        return jsonify({
            'message': 'Department created successfully',
            'department': {
                'id': department.id,
                'name': department.name,
                'description': department.description
            }
        }), 201
    
    except Exception as e:
        db.session.rollback()
        logger.error(f"Error creating department: {str(e)}")
        return jsonify({'error': 'Failed to create department'}), 500


@staff_bp.route('/staff/specializations', methods=['GET'])
@jwt_required()
def get_specializations():
    """Get all available specializations."""
    return jsonify({
        'specializations': [
            {'value': spec, 'label': spec.replace('_', ' ').title()}
            for spec in Staff.SPECIALIZATIONS
        ]
    }), 200


@staff_bp.route('/staff/employment-types', methods=['GET'])
@jwt_required()
def get_employment_types():
    """Get all employment types."""
    return jsonify({
        'employment_types': [
            {'value': emp_type, 'label': emp_type.replace('_', ' ').title()}
            for emp_type in Staff.EMPLOYMENT_TYPES
        ]
    }), 200
