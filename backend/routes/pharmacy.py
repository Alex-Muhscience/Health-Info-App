from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from backend.database import db
from backend.models import Prescription, Client, Staff, Appointment, Inventory
from backend.utils.helpers import handle_validation_error
from backend.utils.auth import role_required
from datetime import datetime, date, timedelta
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

pharmacy_bp = Blueprint('pharmacy', __name__)


# Prescription Routes
@pharmacy_bp.route('/prescriptions', methods=['GET'])
@jwt_required()
@role_required(['admin', 'doctor', 'pharmacy', 'nurse'])
def get_prescriptions():
    """Get prescriptions with filtering options."""
    try:
        client_id = request.args.get('client_id')
        doctor_id = request.args.get('doctor_id')
        status = request.args.get('status')
        date_from = request.args.get('date_from')
        date_to = request.args.get('date_to')
        dispensed = request.args.get('dispensed')
        page = int(request.args.get('page', 1))
        per_page = min(int(request.args.get('per_page', 20)), 100)
        
        query = Prescription.query
        
        if client_id:
            query = query.filter(Prescription.client_id == client_id)
        if doctor_id:
            query = query.filter(Prescription.doctor_id == doctor_id)
        if status:
            query = query.filter(Prescription.status == status)
        if date_from:
            query = query.filter(Prescription.prescribed_date >= datetime.strptime(date_from, '%Y-%m-%d'))
        if date_to:
            query = query.filter(Prescription.prescribed_date <= datetime.strptime(date_to, '%Y-%m-%d'))
        if dispensed is not None:
            query = query.filter(Prescription.dispensed == (dispensed.lower() == 'true'))
        
        prescriptions = query.order_by(Prescription.prescribed_date.desc()).paginate(
            page=page, per_page=per_page, error_out=False
        )
        
        result = []
        for prescription in prescriptions.items:
            prescription_data = {
                'id': prescription.id,
                'client_id': prescription.client_id,
                'client_name': f"{prescription.client.first_name} {prescription.client.last_name}" if prescription.client else None,
                'appointment_id': prescription.appointment_id,
                'doctor_id': prescription.doctor_id,
                'doctor_name': f"{prescription.doctor.first_name} {prescription.doctor.last_name}" if prescription.doctor else None,
                'medication_name': prescription.medication_name,
                'dosage': prescription.dosage,
                'frequency': prescription.frequency,
                'duration': prescription.duration,
                'quantity': prescription.quantity,
                'refills': prescription.refills,
                'instructions': prescription.instructions,
                'status': prescription.status,
                'prescribed_date': prescription.prescribed_date.isoformat(),
                'start_date': prescription.start_date.isoformat() if prescription.start_date else None,
                'end_date': prescription.end_date.isoformat() if prescription.end_date else None,
                'dispensed': prescription.dispensed,
                'dispensed_date': prescription.dispensed_date.isoformat() if prescription.dispensed_date else None,
                'dispensed_by': prescription.dispensed_by,
                'created_at': prescription.created_at.isoformat()
            }
            result.append(prescription_data)
        
        return jsonify({
            'prescriptions': result,
            'pagination': {
                'page': prescriptions.page,
                'pages': prescriptions.pages,
                'per_page': prescriptions.per_page,
                'total': prescriptions.total,
                'has_next': prescriptions.has_next,
                'has_prev': prescriptions.has_prev
            }
        }), 200
    
    except Exception as e:
        logger.error(f"Error fetching prescriptions: {str(e)}")
        return jsonify({'error': 'Failed to fetch prescriptions'}), 500


@pharmacy_bp.route('/prescriptions', methods=['POST'])
@jwt_required()
@role_required(['admin', 'doctor'])
def create_prescription():
    """Create a new prescription."""
    try:
        data = request.get_json()
        current_user = get_jwt_identity()
        
        # Validate required fields
        required_fields = ['client_id', 'doctor_id', 'medication_name', 'dosage', 'frequency']
        for field in required_fields:
            if not data.get(field):
                return jsonify({'error': f'{field} is required'}), 400
        
        # Verify client and doctor exist
        client = Client.query.get_or_404(data['client_id'])
        doctor = Staff.query.get_or_404(data['doctor_id'])
        
        # Create prescription
        prescription = Prescription(
            client_id=data['client_id'],
            appointment_id=data.get('appointment_id'),
            doctor_id=data['doctor_id'],
            medication_name=data['medication_name'],
            dosage=data['dosage'],
            frequency=data['frequency'],
            duration=data.get('duration'),
            quantity=data.get('quantity'),
            refills=data.get('refills', 0),
            instructions=data.get('instructions'),
            start_date=datetime.strptime(data['start_date'], '%Y-%m-%d').date() if data.get('start_date') else None,
            end_date=datetime.strptime(data['end_date'], '%Y-%m-%d').date() if data.get('end_date') else None
        )
        
        db.session.add(prescription)
        db.session.commit()
        
        logger.info(f"Created prescription for client {client.first_name} {client.last_name} - Medication: {prescription.medication_name}")
        
        return jsonify({
            'message': 'Prescription created successfully',
            'prescription': {
                'id': prescription.id,
                'client_id': prescription.client_id,
                'medication_name': prescription.medication_name,
                'status': prescription.status,
                'prescribed_date': prescription.prescribed_date.isoformat()
            }
        }), 201
    
    except Exception as e:
        db.session.rollback()
        logger.error(f"Error creating prescription: {str(e)}")
        return jsonify({'error': 'Failed to create prescription'}), 500


@pharmacy_bp.route('/prescriptions/<prescription_id>', methods=['GET'])
@jwt_required()
@role_required(['admin', 'doctor', 'pharmacy', 'nurse'])
def get_prescription(prescription_id):
    """Get a specific prescription by ID."""
    try:
        prescription = Prescription.query.get_or_404(prescription_id)
        
        return jsonify({
            'id': prescription.id,
            'client_id': prescription.client_id,
            'client_name': f"{prescription.client.first_name} {prescription.client.last_name}" if prescription.client else None,
            'appointment_id': prescription.appointment_id,
            'doctor_id': prescription.doctor_id,
            'doctor_name': f"{prescription.doctor.first_name} {prescription.doctor.last_name}" if prescription.doctor else None,
            'medication_name': prescription.medication_name,
            'dosage': prescription.dosage,
            'frequency': prescription.frequency,
            'duration': prescription.duration,
            'quantity': prescription.quantity,
            'refills': prescription.refills,
            'instructions': prescription.instructions,
            'status': prescription.status,
            'prescribed_date': prescription.prescribed_date.isoformat(),
            'start_date': prescription.start_date.isoformat() if prescription.start_date else None,
            'end_date': prescription.end_date.isoformat() if prescription.end_date else None,
            'dispensed': prescription.dispensed,
            'dispensed_date': prescription.dispensed_date.isoformat() if prescription.dispensed_date else None,
            'dispensed_by': prescription.dispensed_by,
            'created_at': prescription.created_at.isoformat(),
            'updated_at': prescription.updated_at.isoformat()
        }), 200
    
    except Exception as e:
        logger.error(f"Error fetching prescription {prescription_id}: {str(e)}")
        return jsonify({'error': 'Prescription not found'}), 404


@pharmacy_bp.route('/prescriptions/<prescription_id>', methods=['PUT'])
@jwt_required()
@role_required(['admin', 'doctor', 'pharmacy'])
def update_prescription(prescription_id):
    """Update a prescription."""
    try:
        prescription = Prescription.query.get_or_404(prescription_id)
        data = request.get_json()
        current_user = get_jwt_identity()
        
        # Update fields
        if 'medication_name' in data:
            prescription.medication_name = data['medication_name']
        if 'dosage' in data:
            prescription.dosage = data['dosage']
        if 'frequency' in data:
            prescription.frequency = data['frequency']
        if 'duration' in data:
            prescription.duration = data['duration']
        if 'quantity' in data:
            prescription.quantity = data['quantity']
        if 'refills' in data:
            prescription.refills = data['refills']
        if 'instructions' in data:
            prescription.instructions = data['instructions']
        if 'status' in data:
            prescription.status = data['status']
        if 'start_date' in data:
            prescription.start_date = datetime.strptime(data['start_date'], '%Y-%m-%d').date()
        if 'end_date' in data:
            prescription.end_date = datetime.strptime(data['end_date'], '%Y-%m-%d').date()
        
        # Handle dispensing
        if 'dispensed' in data and data['dispensed'] and not prescription.dispensed:
            prescription.dispensed = True
            prescription.dispensed_date = datetime.utcnow()
            prescription.dispensed_by = current_user
        
        db.session.commit()
        
        logger.info(f"Updated prescription {prescription_id}")
        
        return jsonify({
            'message': 'Prescription updated successfully',
            'prescription': {
                'id': prescription.id,
                'status': prescription.status,
                'dispensed': prescription.dispensed,
                'updated_at': prescription.updated_at.isoformat()
            }
        }), 200
    
    except Exception as e:
        db.session.rollback()
        logger.error(f"Error updating prescription {prescription_id}: {str(e)}")
        return jsonify({'error': 'Failed to update prescription'}), 500


@pharmacy_bp.route('/prescriptions/<prescription_id>/dispense', methods=['POST'])
@jwt_required()
@role_required(['admin', 'pharmacy'])
def dispense_prescription(prescription_id):
    """Dispense a prescription."""
    try:
        prescription = Prescription.query.get_or_404(prescription_id)
        current_user = get_jwt_identity()
        
        if prescription.dispensed:
            return jsonify({'error': 'Prescription already dispensed'}), 400
        
        # Mark as dispensed
        prescription.dispensed = True
        prescription.dispensed_date = datetime.utcnow()
        prescription.dispensed_by = current_user
        
        # Update inventory if medication exists in inventory
        inventory_item = Inventory.query.filter(
            Inventory.name.ilike(f"%{prescription.medication_name}%"),
            Inventory.category == 'medication'
        ).first()
        
        if inventory_item and prescription.quantity:
            if inventory_item.quantity_in_stock >= prescription.quantity:
                inventory_item.quantity_in_stock -= prescription.quantity
            else:
                logger.warning(f"Insufficient stock for {prescription.medication_name}")
        
        db.session.commit()
        
        logger.info(f"Dispensed prescription {prescription_id} for {prescription.medication_name}")
        
        return jsonify({
            'message': 'Prescription dispensed successfully',
            'prescription': {
                'id': prescription.id,
                'dispensed': prescription.dispensed,
                'dispensed_date': prescription.dispensed_date.isoformat()
            }
        }), 200
    
    except Exception as e:
        db.session.rollback()
        logger.error(f"Error dispensing prescription {prescription_id}: {str(e)}")
        return jsonify({'error': 'Failed to dispense prescription'}), 500


@pharmacy_bp.route('/clients/<client_id>/prescriptions', methods=['GET'])
@jwt_required()
@role_required(['admin', 'doctor', 'pharmacy', 'nurse'])
def get_client_prescriptions(client_id):
    """Get all prescriptions for a specific client."""
    try:
        # Verify client exists
        client = Client.query.get_or_404(client_id)
        
        page = int(request.args.get('page', 1))
        per_page = min(int(request.args.get('per_page', 20)), 100)
        
        prescriptions = Prescription.query.filter_by(client_id=client_id)\
            .order_by(Prescription.prescribed_date.desc())\
            .paginate(page=page, per_page=per_page, error_out=False)
        
        result = []
        for prescription in prescriptions.items:
            prescription_data = {
                'id': prescription.id,
                'medication_name': prescription.medication_name,
                'dosage': prescription.dosage,
                'frequency': prescription.frequency,
                'duration': prescription.duration,
                'status': prescription.status,
                'prescribed_date': prescription.prescribed_date.isoformat(),
                'dispensed': prescription.dispensed,
                'dispensed_date': prescription.dispensed_date.isoformat() if prescription.dispensed_date else None,
                'doctor_name': f"{prescription.doctor.first_name} {prescription.doctor.last_name}" if prescription.doctor else None
            }
            result.append(prescription_data)
        
        return jsonify({
            'prescriptions': result,
            'client': {
                'id': client.id,
                'name': f"{client.first_name} {client.last_name}"
            },
            'pagination': {
                'page': prescriptions.page,
                'pages': prescriptions.pages,
                'per_page': prescriptions.per_page,
                'total': prescriptions.total,
                'has_next': prescriptions.has_next,
                'has_prev': prescriptions.has_prev
            }
        }), 200
    
    except Exception as e:
        logger.error(f"Error fetching prescriptions for client {client_id}: {str(e)}")
        return jsonify({'error': 'Failed to fetch prescriptions'}), 500


# Inventory Routes
@pharmacy_bp.route('/inventory', methods=['GET'])
@jwt_required()
@role_required(['admin', 'pharmacy'])
def get_inventory():
    """Get inventory items with filtering options."""
    try:
        category = request.args.get('category')
        low_stock = request.args.get('low_stock') == 'true'
        expiring_soon = request.args.get('expiring_soon') == 'true'
        is_active = request.args.get('is_active', 'true').lower() == 'true'
        page = int(request.args.get('page', 1))
        per_page = min(int(request.args.get('per_page', 20)), 100)
        
        query = Inventory.query.filter_by(is_active=is_active)
        
        if category:
            query = query.filter(Inventory.category == category)
        
        if low_stock:
            query = query.filter(Inventory.quantity_in_stock <= Inventory.minimum_stock_level)
        
        if expiring_soon:
            # Items expiring within 30 days
            thirty_days_from_now = datetime.utcnow().date() + timedelta(days=30)
            query = query.filter(Inventory.expiry_date <= thirty_days_from_now)
        
        items = query.order_by(Inventory.name).paginate(
            page=page, per_page=per_page, error_out=False
        )
        
        result = []
        for item in items.items:
            item_data = {
                'id': item.id,
                'name': item.name,
                'code': item.code,
                'category': item.category,
                'description': item.description,
                'manufacturer': item.manufacturer,
                'batch_number': item.batch_number,
                'expiry_date': item.expiry_date.isoformat() if item.expiry_date else None,
                'unit': item.unit,
                'quantity_in_stock': item.quantity_in_stock,
                'minimum_stock_level': item.minimum_stock_level,
                'unit_price': float(item.unit_price) if item.unit_price else None,
                'supplier': item.supplier,
                'location': item.location,
                'is_active': item.is_active,
                'low_stock': item.quantity_in_stock <= item.minimum_stock_level,
                'created_at': item.created_at.isoformat()
            }
            result.append(item_data)
        
        return jsonify({
            'inventory': result,
            'pagination': {
                'page': items.page,
                'pages': items.pages,
                'per_page': items.per_page,
                'total': items.total,
                'has_next': items.has_next,
                'has_prev': items.has_prev
            }
        }), 200
    
    except Exception as e:
        logger.error(f"Error fetching inventory: {str(e)}")
        return jsonify({'error': 'Failed to fetch inventory'}), 500


@pharmacy_bp.route('/inventory', methods=['POST'])
@jwt_required()
@role_required(['admin', 'pharmacy'])
def create_inventory_item():
    """Create a new inventory item."""
    try:
        data = request.get_json()
        
        # Validate required fields
        required_fields = ['name', 'category']
        for field in required_fields:
            if not data.get(field):
                return jsonify({'error': f'{field} is required'}), 400
        
        # Create inventory item
        item = Inventory(
            name=data['name'],
            code=data.get('code'),
            category=data['category'],
            description=data.get('description'),
            manufacturer=data.get('manufacturer'),
            batch_number=data.get('batch_number'),
            expiry_date=datetime.strptime(data['expiry_date'], '%Y-%m-%d').date() if data.get('expiry_date') else None,
            unit=data.get('unit'),
            quantity_in_stock=data.get('quantity_in_stock', 0),
            minimum_stock_level=data.get('minimum_stock_level', 0),
            unit_price=data.get('unit_price'),
            supplier=data.get('supplier'),
            location=data.get('location')
        )
        
        db.session.add(item)
        db.session.commit()
        
        logger.info(f"Created inventory item: {item.name}")
        
        return jsonify({
            'message': 'Inventory item created successfully',
            'item': {
                'id': item.id,
                'name': item.name,
                'category': item.category,
                'quantity_in_stock': item.quantity_in_stock
            }
        }), 201
    
    except Exception as e:
        db.session.rollback()
        logger.error(f"Error creating inventory item: {str(e)}")
        return jsonify({'error': 'Failed to create inventory item'}), 500


@pharmacy_bp.route('/inventory/<item_id>', methods=['PUT'])
@jwt_required()
@role_required(['admin', 'pharmacy'])
def update_inventory_item(item_id):
    """Update an inventory item."""
    try:
        item = Inventory.query.get_or_404(item_id)
        data = request.get_json()
        
        # Update fields
        if 'name' in data:
            item.name = data['name']
        if 'code' in data:
            item.code = data['code']
        if 'category' in data:
            item.category = data['category']
        if 'description' in data:
            item.description = data['description']
        if 'manufacturer' in data:
            item.manufacturer = data['manufacturer']
        if 'batch_number' in data:
            item.batch_number = data['batch_number']
        if 'expiry_date' in data:
            item.expiry_date = datetime.strptime(data['expiry_date'], '%Y-%m-%d').date()
        if 'unit' in data:
            item.unit = data['unit']
        if 'quantity_in_stock' in data:
            item.quantity_in_stock = data['quantity_in_stock']
        if 'minimum_stock_level' in data:
            item.minimum_stock_level = data['minimum_stock_level']
        if 'unit_price' in data:
            item.unit_price = data['unit_price']
        if 'supplier' in data:
            item.supplier = data['supplier']
        if 'location' in data:
            item.location = data['location']
        if 'is_active' in data:
            item.is_active = data['is_active']
        
        db.session.commit()
        
        logger.info(f"Updated inventory item: {item.name}")
        
        return jsonify({
            'message': 'Inventory item updated successfully',
            'item': {
                'id': item.id,
                'name': item.name,
                'quantity_in_stock': item.quantity_in_stock,
                'updated_at': item.updated_at.isoformat()
            }
        }), 200
    
    except Exception as e:
        db.session.rollback()
        logger.error(f"Error updating inventory item {item_id}: {str(e)}")
        return jsonify({'error': 'Failed to update inventory item'}), 500


@pharmacy_bp.route('/prescriptions/statuses', methods=['GET'])
@jwt_required()
def get_prescription_statuses():
    """Get all prescription statuses."""
    return jsonify({
        'statuses': [
            {'value': status, 'label': status.replace('_', ' ').title()}
            for status in Prescription.STATUSES
        ]
    }), 200


@pharmacy_bp.route('/inventory/categories', methods=['GET'])
@jwt_required()
def get_inventory_categories():
    """Get all inventory categories."""
    return jsonify({
        'categories': [
            {'value': category, 'label': category.replace('_', ' ').title()}
            for category in Inventory.CATEGORIES
        ]
    }), 200


@pharmacy_bp.route('/inventory/units', methods=['GET'])
@jwt_required()
def get_inventory_units():
    """Get all inventory units."""
    return jsonify({
        'units': [
            {'value': unit, 'label': unit.replace('_', ' ').title()}
            for unit in Inventory.UNITS
        ]
    }), 200


@pharmacy_bp.route('/pharmacy/statistics', methods=['GET'])
@jwt_required()
@role_required(['admin', 'pharmacy'])
def get_pharmacy_statistics():
    """Get pharmacy statistics."""
    try:
        from datetime import timedelta
        
        # Prescription statistics
        total_prescriptions = Prescription.query.count()
        dispensed_prescriptions = Prescription.query.filter_by(dispensed=True).count()
        pending_prescriptions = Prescription.query.filter_by(dispensed=False).count()
        
        # Today's prescriptions
        today = datetime.utcnow().date()
        today_prescriptions = Prescription.query.filter(
            db.func.date(Prescription.prescribed_date) == today
        ).count()
        
        # Inventory statistics
        total_inventory_items = Inventory.query.filter_by(is_active=True).count()
        low_stock_items = Inventory.query.filter(
            Inventory.quantity_in_stock <= Inventory.minimum_stock_level,
            Inventory.is_active == True
        ).count()
        
        # Expiring items (within 30 days)
        thirty_days_from_now = today + timedelta(days=30)
        expiring_items = Inventory.query.filter(
            Inventory.expiry_date <= thirty_days_from_now,
            Inventory.expiry_date >= today,
            Inventory.is_active == True
        ).count()
        
        return jsonify({
            'prescriptions': {
                'total': total_prescriptions,
                'dispensed': dispensed_prescriptions,
                'pending': pending_prescriptions,
                'today': today_prescriptions
            },
            'inventory': {
                'total_items': total_inventory_items,
                'low_stock': low_stock_items,
                'expiring_soon': expiring_items
            }
        }), 200
    
    except Exception as e:
        logger.error(f"Error fetching pharmacy statistics: {str(e)}")
        return jsonify({'error': 'Failed to fetch pharmacy statistics'}), 500
