from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from backend.database import db
from backend.models import Department, Staff
from backend.utils.helpers import handle_validation_error
from backend.utils.auth import role_required
from datetime import datetime
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

departments_bp = Blueprint('departments', __name__)


@departments_bp.route('/departments', methods=['GET'])
@jwt_required()
def get_all_departments():
    """Get all departments with filtering and pagination options."""
    try:
        # Get query parameters
        is_active = request.args.get('is_active', 'true').lower() == 'true'
        search = request.args.get('search', '').strip()
        page = int(request.args.get('page', 1))
        per_page = min(int(request.args.get('per_page', 10)), 100)
        
        # Build query
        query = Department.query
        
        if is_active is not None:
            query = query.filter(Department.is_active == is_active)
        
        if search:
            query = query.filter(
                Department.name.ilike(f'%{search}%') |
                Department.description.ilike(f'%{search}%')
            )
        
        # Apply pagination
        departments_list = query.paginate(
            page=page, per_page=per_page, error_out=False
        )
        
        result = []
        for dept in departments_list.items:
            # Get head of department details
            head_info = None
            if dept.head_id:
                head = Staff.query.get(dept.head_id)
                if head:
                    head_info = {
                        'id': head.id,
                        'name': f"{head.first_name} {head.last_name}",
                        'employee_id': head.employee_id
                    }
            
            dept_data = {
                'id': dept.id,
                'name': dept.name,
                'description': dept.description,
                'location': dept.location,
                'phone': dept.phone,
                'email': dept.email,
                'head_id': dept.head_id,
                'head': head_info,
                'staff_count': len(dept.staff),
                'is_active': dept.is_active,
                'created_at': dept.created_at.isoformat(),
                'updated_at': dept.updated_at.isoformat()
            }
            result.append(dept_data)
        
        return jsonify({
            'departments': result,
            'pagination': {
                'page': departments_list.page,
                'pages': departments_list.pages,
                'per_page': departments_list.per_page,
                'total': departments_list.total,
                'has_next': departments_list.has_next,
                'has_prev': departments_list.has_prev
            }
        }), 200
    
    except Exception as e:
        logger.error(f"Error fetching departments: {str(e)}")
        return jsonify({'error': 'Failed to fetch departments'}), 500


@departments_bp.route('/departments', methods=['POST'])
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
        existing_dept = Department.query.filter_by(name=data['name']).first()
        if existing_dept:
            return jsonify({'error': 'Department with this name already exists'}), 400
        
        # Validate head_id if provided
        if data.get('head_id'):
            head = Staff.query.get(data['head_id'])
            if not head:
                return jsonify({'error': 'Invalid head of department ID'}), 400
            if not head.is_active:
                return jsonify({'error': 'Head of department must be an active staff member'}), 400
        
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
                'description': department.description,
                'location': department.location,
                'phone': department.phone,
                'email': department.email,
                'head_id': department.head_id
            }
        }), 201
    
    except Exception as e:
        db.session.rollback()
        logger.error(f"Error creating department: {str(e)}")
        return jsonify({'error': 'Failed to create department'}), 500


@departments_bp.route('/departments/<department_id>', methods=['GET'])
@jwt_required()
def get_department(department_id):
    """Get a specific department by ID."""
    try:
        department = Department.query.get_or_404(department_id)
        
        # Get head of department details
        head_info = None
        if department.head_id:
            head = Staff.query.get(department.head_id)
            if head:
                head_info = {
                    'id': head.id,
                    'name': f"{head.first_name} {head.last_name}",
                    'employee_id': head.employee_id,
                    'specialization': head.specialization
                }
        
        # Get department staff
        staff_list = []
        for staff in department.staff:
            if staff.is_active:
                staff_list.append({
                    'id': staff.id,
                    'employee_id': staff.employee_id,
                    'name': f"{staff.first_name} {staff.last_name}",
                    'specialization': staff.specialization,
                    'employment_type': staff.employment_type
                })
        
        return jsonify({
            'id': department.id,
            'name': department.name,
            'description': department.description,
            'location': department.location,
            'phone': department.phone,
            'email': department.email,
            'head_id': department.head_id,
            'head': head_info,
            'staff': staff_list,
            'staff_count': len(staff_list),
            'is_active': department.is_active,
            'created_at': department.created_at.isoformat(),
            'updated_at': department.updated_at.isoformat()
        }), 200
    
    except Exception as e:
        logger.error(f"Error fetching department {department_id}: {str(e)}")
        return jsonify({'error': 'Department not found'}), 404


@departments_bp.route('/departments/<department_id>', methods=['PUT'])
@jwt_required()
@role_required(['admin'])
def update_department(department_id):
    """Update a department."""
    try:
        department = Department.query.get_or_404(department_id)
        data = request.get_json()
        
        # Check if another department has the same name (if name is being updated)
        if 'name' in data and data['name'] != department.name:
            existing_dept = Department.query.filter_by(name=data['name']).first()
            if existing_dept:
                return jsonify({'error': 'Department with this name already exists'}), 400
        
        # Validate head_id if provided
        if 'head_id' in data and data['head_id']:
            head = Staff.query.get(data['head_id'])
            if not head:
                return jsonify({'error': 'Invalid head of department ID'}), 400
            if not head.is_active:
                return jsonify({'error': 'Head of department must be an active staff member'}), 400
        
        # Update fields
        if 'name' in data:
            department.name = data['name']
        if 'description' in data:
            department.description = data['description']
        if 'location' in data:
            department.location = data['location']
        if 'phone' in data:
            department.phone = data['phone']
        if 'email' in data:
            department.email = data['email']
        if 'head_id' in data:
            department.head_id = data['head_id']
        if 'is_active' in data:
            department.is_active = data['is_active']
        
        db.session.commit()
        
        logger.info(f"Updated department: {department.name}")
        
        return jsonify({
            'message': 'Department updated successfully',
            'department': {
                'id': department.id,
                'name': department.name,
                'description': department.description,
                'location': department.location,
                'phone': department.phone,
                'email': department.email,
                'head_id': department.head_id
            }
        }), 200
    
    except ValueError as e:
        return handle_validation_error(e)
    except Exception as e:
        db.session.rollback()
        logger.error(f"Error updating department {department_id}: {str(e)}")
        return jsonify({'error': 'Failed to update department'}), 500


@departments_bp.route('/departments/<department_id>', methods=['DELETE'])
@jwt_required()
@role_required(['admin'])
def delete_department(department_id):
    """Delete (deactivate) a department."""
    try:
        department = Department.query.get_or_404(department_id)
        
        # Check if department has active staff
        active_staff_count = Staff.query.filter_by(
            department_id=department_id, 
            is_active=True
        ).count()
        
        if active_staff_count > 0:
            return jsonify({
                'error': f'Cannot delete department with {active_staff_count} active staff members. Please reassign staff first.'
            }), 400
        
        department.is_active = False
        db.session.commit()
        
        logger.info(f"Deactivated department: {department.name}")
        
        return jsonify({'message': 'Department deactivated successfully'}), 200
    
    except Exception as e:
        db.session.rollback()
        logger.error(f"Error deleting department {department_id}: {str(e)}")
        return jsonify({'error': 'Failed to delete department'}), 500


@departments_bp.route('/departments/<department_id>/staff', methods=['GET'])
@jwt_required()
def get_department_staff(department_id):
    """Get all staff members for a specific department."""
    try:
        department = Department.query.get_or_404(department_id)
        
        # Get query parameters
        is_active = request.args.get('is_active', 'true').lower() == 'true'
        page = int(request.args.get('page', 1))
        per_page = min(int(request.args.get('per_page', 10)), 100)
        
        # Build query
        query = Staff.query.filter_by(department_id=department_id)
        
        if is_active is not None:
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
                'phone': staff.phone,
                'email': staff.email,
                'employment_type': staff.employment_type,
                'hire_date': staff.hire_date.isoformat() if staff.hire_date else None,
                'is_active': staff.is_active,
                'created_at': staff.created_at.isoformat()
            }
            result.append(staff_data)
        
        return jsonify({
            'department': {
                'id': department.id,
                'name': department.name
            },
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
        logger.error(f"Error fetching staff for department {department_id}: {str(e)}")
        return jsonify({'error': 'Failed to fetch department staff'}), 500


@departments_bp.route('/departments/active', methods=['GET'])
@jwt_required()
def get_active_departments():
    """Get all active departments for dropdowns and selection lists."""
    try:
        departments = Department.query.filter_by(is_active=True).order_by(Department.name).all()
        
        result = []
        for dept in departments:
            result.append({
                'id': dept.id,
                'name': dept.name,
                'description': dept.description,
                'location': dept.location
            })
        
        return jsonify({'departments': result}), 200
    
    except Exception as e:
        logger.error(f"Error fetching active departments: {str(e)}")
        return jsonify({'error': 'Failed to fetch active departments'}), 500
