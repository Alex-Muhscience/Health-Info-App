from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from backend.database import db
from backend.models import LabTest, LabOrder, Client, Staff, Appointment
from backend.utils.helpers import handle_validation_error
from backend.utils.auth import role_required
from datetime import datetime
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

laboratory_bp = Blueprint('laboratory', __name__)


# Lab Tests Routes
@laboratory_bp.route('/lab-tests', methods=['GET'])
@jwt_required()
def get_lab_tests():
    """Get all available lab tests."""
    try:
        category = request.args.get('category')
        is_active = request.args.get('is_active', 'true').lower() == 'true'
        page = int(request.args.get('page', 1))
        per_page = min(int(request.args.get('per_page', 20)), 100)
        
        query = LabTest.query.filter_by(is_active=is_active)
        
        if category:
            query = query.filter(LabTest.category == category)
        
        tests = query.order_by(LabTest.name).paginate(
            page=page, per_page=per_page, error_out=False
        )
        
        result = []
        for test in tests.items:
            test_data = {
                'id': test.id,
                'name': test.name,
                'code': test.code,
                'category': test.category,
                'description': test.description,
                'normal_range': test.normal_range,
                'unit': test.unit,
                'cost': float(test.cost) if test.cost else None,
                'turnaround_time': test.turnaround_time,
                'is_active': test.is_active,
                'created_at': test.created_at.isoformat()
            }
            result.append(test_data)
        
        return jsonify({
            'lab_tests': result,
            'pagination': {
                'page': tests.page,
                'pages': tests.pages,
                'per_page': tests.per_page,
                'total': tests.total,
                'has_next': tests.has_next,
                'has_prev': tests.has_prev
            }
        }), 200
    
    except Exception as e:
        logger.error(f"Error fetching lab tests: {str(e)}")
        return jsonify({'error': 'Failed to fetch lab tests'}), 500


@laboratory_bp.route('/lab-tests', methods=['POST'])
@jwt_required()
@role_required(['admin', 'lab_tech'])
def create_lab_test():
    """Create a new lab test."""
    try:
        data = request.get_json()
        
        # Validate required fields
        required_fields = ['name', 'category']
        for field in required_fields:
            if not data.get(field):
                return jsonify({'error': f'{field} is required'}), 400
        
        # Check if test name already exists
        if LabTest.query.filter_by(name=data['name']).first():
            return jsonify({'error': 'Lab test with this name already exists'}), 400
        
        # Create lab test
        test = LabTest(
            name=data['name'],
            code=data.get('code'),
            category=data['category'],
            description=data.get('description'),
            normal_range=data.get('normal_range'),
            unit=data.get('unit'),
            cost=data.get('cost'),
            turnaround_time=data.get('turnaround_time')
        )
        
        db.session.add(test)
        db.session.commit()
        
        logger.info(f"Created new lab test: {test.name}")
        
        return jsonify({
            'message': 'Lab test created successfully',
            'test': {
                'id': test.id,
                'name': test.name,
                'code': test.code,
                'category': test.category
            }
        }), 201
    
    except Exception as e:
        db.session.rollback()
        logger.error(f"Error creating lab test: {str(e)}")
        return jsonify({'error': 'Failed to create lab test'}), 500


@laboratory_bp.route('/lab-tests/<test_id>', methods=['PUT'])
@jwt_required()
@role_required(['admin', 'lab_tech'])
def update_lab_test(test_id):
    """Update a lab test."""
    try:
        test = LabTest.query.get_or_404(test_id)
        data = request.get_json()
        
        # Update fields
        if 'name' in data:
            test.name = data['name']
        if 'code' in data:
            test.code = data['code']
        if 'category' in data:
            test.category = data['category']
        if 'description' in data:
            test.description = data['description']
        if 'normal_range' in data:
            test.normal_range = data['normal_range']
        if 'unit' in data:
            test.unit = data['unit']
        if 'cost' in data:
            test.cost = data['cost']
        if 'turnaround_time' in data:
            test.turnaround_time = data['turnaround_time']
        if 'is_active' in data:
            test.is_active = data['is_active']
        
        db.session.commit()
        
        logger.info(f"Updated lab test: {test.name}")
        
        return jsonify({
            'message': 'Lab test updated successfully',
            'test': {
                'id': test.id,
                'name': test.name,
                'updated_at': test.updated_at.isoformat()
            }
        }), 200
    
    except Exception as e:
        db.session.rollback()
        logger.error(f"Error updating lab test {test_id}: {str(e)}")
        return jsonify({'error': 'Failed to update lab test'}), 500


# Lab Orders Routes
@laboratory_bp.route('/lab-orders', methods=['GET'])
@jwt_required()
@role_required(['admin', 'doctor', 'lab_tech', 'nurse'])
def get_lab_orders():
    """Get lab orders with filtering options."""
    try:
        client_id = request.args.get('client_id')
        status = request.args.get('status')
        priority = request.args.get('priority')
        date_from = request.args.get('date_from')
        date_to = request.args.get('date_to')
        page = int(request.args.get('page', 1))
        per_page = min(int(request.args.get('per_page', 20)), 100)
        
        query = LabOrder.query
        
        if client_id:
            query = query.filter(LabOrder.client_id == client_id)
        if status:
            query = query.filter(LabOrder.status == status)
        if priority:
            query = query.filter(LabOrder.priority == priority)
        if date_from:
            query = query.filter(LabOrder.created_at >= datetime.strptime(date_from, '%Y-%m-%d'))
        if date_to:
            query = query.filter(LabOrder.created_at <= datetime.strptime(date_to, '%Y-%m-%d'))
        
        orders = query.order_by(LabOrder.created_at.desc()).paginate(
            page=page, per_page=per_page, error_out=False
        )
        
        result = []
        for order in orders.items:
            order_data = {
                'id': order.id,
                'client_id': order.client_id,
                'client_name': f"{order.client.first_name} {order.client.last_name}" if order.client else None,
                'appointment_id': order.appointment_id,
                'test_id': order.test_id,
                'test_name': order.test.name if order.test else None,
                'test_category': order.test.category if order.test else None,
                'ordered_by': order.ordered_by,
                'ordered_by_name': f"{order.ordered_by_staff.first_name} {order.ordered_by_staff.last_name}" if order.ordered_by_staff else None,
                'status': order.status,
                'priority': order.priority,
                'clinical_notes': order.clinical_notes,
                'specimen_type': order.specimen_type,
                'collection_date': order.collection_date.isoformat() if order.collection_date else None,
                'result_date': order.result_date.isoformat() if order.result_date else None,
                'result_value': order.result_value,
                'result_notes': order.result_notes,
                'abnormal_flag': order.abnormal_flag,
                'processed_by': order.processed_by,
                'created_at': order.created_at.isoformat()
            }
            result.append(order_data)
        
        return jsonify({
            'lab_orders': result,
            'pagination': {
                'page': orders.page,
                'pages': orders.pages,
                'per_page': orders.per_page,
                'total': orders.total,
                'has_next': orders.has_next,
                'has_prev': orders.has_prev
            }
        }), 200
    
    except Exception as e:
        logger.error(f"Error fetching lab orders: {str(e)}")
        return jsonify({'error': 'Failed to fetch lab orders'}), 500


@laboratory_bp.route('/lab-orders', methods=['POST'])
@jwt_required()
@role_required(['admin', 'doctor'])
def create_lab_order():
    """Create a new lab order."""
    try:
        data = request.get_json()
        current_user = get_jwt_identity()
        
        # Validate required fields
        required_fields = ['client_id', 'test_id', 'ordered_by']
        for field in required_fields:
            if not data.get(field):
                return jsonify({'error': f'{field} is required'}), 400
        
        # Verify client and test exist
        client = Client.query.get_or_404(data['client_id'])
        test = LabTest.query.get_or_404(data['test_id'])
        staff = Staff.query.get_or_404(data['ordered_by'])
        
        # Create lab order
        order = LabOrder(
            client_id=data['client_id'],
            appointment_id=data.get('appointment_id'),
            test_id=data['test_id'],
            ordered_by=data['ordered_by'],
            priority=data.get('priority', 'routine'),
            clinical_notes=data.get('clinical_notes'),
            specimen_type=data.get('specimen_type')
        )
        
        db.session.add(order)
        db.session.commit()
        
        logger.info(f"Created lab order for client {client.first_name} {client.last_name} - Test: {test.name}")
        
        return jsonify({
            'message': 'Lab order created successfully',
            'order': {
                'id': order.id,
                'client_id': order.client_id,
                'test_name': test.name,
                'status': order.status,
                'created_at': order.created_at.isoformat()
            }
        }), 201
    
    except Exception as e:
        db.session.rollback()
        logger.error(f"Error creating lab order: {str(e)}")
        return jsonify({'error': 'Failed to create lab order'}), 500


@laboratory_bp.route('/lab-orders/<order_id>', methods=['GET'])
@jwt_required()
@role_required(['admin', 'doctor', 'lab_tech', 'nurse'])
def get_lab_order(order_id):
    """Get a specific lab order by ID."""
    try:
        order = LabOrder.query.get_or_404(order_id)
        
        return jsonify({
            'id': order.id,
            'client_id': order.client_id,
            'client_name': f"{order.client.first_name} {order.client.last_name}" if order.client else None,
            'appointment_id': order.appointment_id,
            'test_id': order.test_id,
            'test_name': order.test.name if order.test else None,
            'test_description': order.test.description if order.test else None,
            'test_normal_range': order.test.normal_range if order.test else None,
            'test_unit': order.test.unit if order.test else None,
            'ordered_by': order.ordered_by,
            'ordered_by_name': f"{order.ordered_by_staff.first_name} {order.ordered_by_staff.last_name}" if order.ordered_by_staff else None,
            'status': order.status,
            'priority': order.priority,
            'clinical_notes': order.clinical_notes,
            'specimen_type': order.specimen_type,
            'collection_date': order.collection_date.isoformat() if order.collection_date else None,
            'result_date': order.result_date.isoformat() if order.result_date else None,
            'result_value': order.result_value,
            'result_notes': order.result_notes,
            'abnormal_flag': order.abnormal_flag,
            'processed_by': order.processed_by,
            'created_at': order.created_at.isoformat(),
            'updated_at': order.updated_at.isoformat()
        }), 200
    
    except Exception as e:
        logger.error(f"Error fetching lab order {order_id}: {str(e)}")
        return jsonify({'error': 'Lab order not found'}), 404


@laboratory_bp.route('/lab-orders/<order_id>', methods=['PUT'])
@jwt_required()
@role_required(['admin', 'lab_tech'])
def update_lab_order(order_id):
    """Update a lab order (typically to add results)."""
    try:
        order = LabOrder.query.get_or_404(order_id)
        data = request.get_json()
        current_user = get_jwt_identity()
        
        # Update fields
        if 'status' in data:
            order.status = data['status']
        if 'clinical_notes' in data:
            order.clinical_notes = data['clinical_notes']
        if 'specimen_type' in data:
            order.specimen_type = data['specimen_type']
        if 'collection_date' in data:
            order.collection_date = datetime.strptime(data['collection_date'], '%Y-%m-%dT%H:%M:%S')
        if 'result_date' in data:
            order.result_date = datetime.strptime(data['result_date'], '%Y-%m-%dT%H:%M:%S')
        if 'result_value' in data:
            order.result_value = data['result_value']
        if 'result_notes' in data:
            order.result_notes = data['result_notes']
        if 'abnormal_flag' in data:
            order.abnormal_flag = data['abnormal_flag']
        
        # Set processed_by when results are added
        if data.get('result_value') and not order.processed_by:
            order.processed_by = current_user
        
        db.session.commit()
        
        logger.info(f"Updated lab order {order_id} - Status: {order.status}")
        
        return jsonify({
            'message': 'Lab order updated successfully',
            'order': {
                'id': order.id,
                'status': order.status,
                'updated_at': order.updated_at.isoformat()
            }
        }), 200
    
    except Exception as e:
        db.session.rollback()
        logger.error(f"Error updating lab order {order_id}: {str(e)}")
        return jsonify({'error': 'Failed to update lab order'}), 500


@laboratory_bp.route('/clients/<client_id>/lab-orders', methods=['GET'])
@jwt_required()
@role_required(['admin', 'doctor', 'lab_tech', 'nurse'])
def get_client_lab_orders(client_id):
    """Get all lab orders for a specific client."""
    try:
        # Verify client exists
        client = Client.query.get_or_404(client_id)
        
        page = int(request.args.get('page', 1))
        per_page = min(int(request.args.get('per_page', 20)), 100)
        
        orders = LabOrder.query.filter_by(client_id=client_id)\
            .order_by(LabOrder.created_at.desc())\
            .paginate(page=page, per_page=per_page, error_out=False)
        
        result = []
        for order in orders.items:
            order_data = {
                'id': order.id,
                'test_name': order.test.name if order.test else None,
                'test_category': order.test.category if order.test else None,
                'status': order.status,
                'priority': order.priority,
                'collection_date': order.collection_date.isoformat() if order.collection_date else None,
                'result_date': order.result_date.isoformat() if order.result_date else None,
                'result_value': order.result_value,
                'abnormal_flag': order.abnormal_flag,
                'created_at': order.created_at.isoformat()
            }
            result.append(order_data)
        
        return jsonify({
            'lab_orders': result,
            'client': {
                'id': client.id,
                'name': f"{client.first_name} {client.last_name}"
            },
            'pagination': {
                'page': orders.page,
                'pages': orders.pages,
                'per_page': orders.per_page,
                'total': orders.total,
                'has_next': orders.has_next,
                'has_prev': orders.has_prev
            }
        }), 200
    
    except Exception as e:
        logger.error(f"Error fetching lab orders for client {client_id}: {str(e)}")
        return jsonify({'error': 'Failed to fetch lab orders'}), 500


@laboratory_bp.route('/lab-tests/categories', methods=['GET'])
@jwt_required()
def get_lab_test_categories():
    """Get all lab test categories."""
    return jsonify({
        'categories': [
            {'value': category, 'label': category.replace('_', ' ').title()}
            for category in LabTest.CATEGORIES
        ]
    }), 200


@laboratory_bp.route('/lab-orders/statuses', methods=['GET'])
@jwt_required()
def get_lab_order_statuses():
    """Get all lab order statuses."""
    return jsonify({
        'statuses': [
            {'value': status, 'label': status.replace('_', ' ').title()}
            for status in LabOrder.STATUSES
        ]
    }), 200


@laboratory_bp.route('/lab-orders/priorities', methods=['GET'])
@jwt_required()
def get_lab_order_priorities():
    """Get all lab order priorities."""
    return jsonify({
        'priorities': [
            {'value': priority, 'label': priority.replace('_', ' ').title()}
            for priority in LabOrder.PRIORITIES
        ]
    }), 200


@laboratory_bp.route('/lab-orders/statistics', methods=['GET'])
@jwt_required()
@role_required(['admin', 'lab_tech'])
def get_lab_statistics():
    """Get laboratory statistics."""
    try:
        # Get counts by status
        status_counts = {}
        for status in LabOrder.STATUSES:
            count = LabOrder.query.filter_by(status=status).count()
            status_counts[status] = count
        
        # Get today's orders
        today = datetime.utcnow().date()
        today_orders = LabOrder.query.filter(
            db.func.date(LabOrder.created_at) == today
        ).count()
        
        # Get pending results count
        pending_results = LabOrder.query.filter(
            LabOrder.status.in_(['collected', 'processing'])
        ).count()
        
        # Get overdue orders (more than turnaround time)
        overdue_orders = []  # This would require more complex logic based on turnaround times
        
        return jsonify({
            'status_counts': status_counts,
            'today_orders': today_orders,
            'pending_results': pending_results,
            'total_orders': sum(status_counts.values()),
            'active_tests': LabTest.query.filter_by(is_active=True).count()
        }), 200
    
    except Exception as e:
        logger.error(f"Error fetching lab statistics: {str(e)}")
        return jsonify({'error': 'Failed to fetch lab statistics'}), 500
