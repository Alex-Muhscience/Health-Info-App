from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from backend.database import db
from backend.models import Billing, BillingItem, Client, Visit, Admission, InsuranceProvider, ClientInsurance
from backend.utils.helpers import handle_validation_error
from backend.utils.auth import role_required
from datetime import datetime, date
import logging
import uuid

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

billing_bp = Blueprint('billing', __name__)


# Billing Routes
@billing_bp.route('/billing', methods=['GET'])
@jwt_required()
@role_required(['admin', 'doctor', 'receptionist'])
def get_billings():
    """Get billings with filtering options."""
    try:
        client_id = request.args.get('client_id')
        status = request.args.get('status')
        payment_method = request.args.get('payment_method')
        date_from = request.args.get('date_from')
        date_to = request.args.get('date_to')
        overdue = request.args.get('overdue') == 'true'
        page = int(request.args.get('page', 1))
        per_page = min(int(request.args.get('per_page', 20)), 100)
        
        query = Billing.query
        
        if client_id:
            query = query.filter(Billing.client_id == client_id)
        if status:
            query = query.filter(Billing.status == status)
        if payment_method:
            query = query.filter(Billing.payment_method == payment_method)
        if date_from:
            query = query.filter(Billing.created_at >= datetime.strptime(date_from, '%Y-%m-%d'))
        if date_to:
            query = query.filter(Billing.created_at <= datetime.strptime(date_to, '%Y-%m-%d'))
        if overdue:
            today = datetime.utcnow().date()
            query = query.filter(Billing.due_date < today, Billing.status.in_(['pending', 'partially_paid']))
        
        billings = query.order_by(Billing.created_at.desc()).paginate(
            page=page, per_page=per_page, error_out=False
        )
        
        result = []
        for billing in billings.items:
            billing_data = {
                'id': billing.id,
                'client_id': billing.client_id,
                'client_name': f"{billing.client.first_name} {billing.client.last_name}" if billing.client else None,
                'visit_id': billing.visit_id,
                'admission_id': billing.admission_id,
                'invoice_number': billing.invoice_number,
                'total_amount': float(billing.total_amount),
                'paid_amount': float(billing.paid_amount),
                'balance': float(billing.total_amount - billing.paid_amount),
                'status': billing.status,
                'payment_method': billing.payment_method,
                'insurance_provider': billing.insurance_provider,
                'due_date': billing.due_date.isoformat() if billing.due_date else None,
                'payment_date': billing.payment_date.isoformat() if billing.payment_date else None,
                'created_at': billing.created_at.isoformat(),
                'is_overdue': billing.due_date < datetime.utcnow().date() if billing.due_date else False
            }
            result.append(billing_data)
        
        return jsonify({
            'billings': result,
            'pagination': {
                'page': billings.page,
                'pages': billings.pages,
                'per_page': billings.per_page,
                'total': billings.total,
                'has_next': billings.has_next,
                'has_prev': billings.has_prev
            }
        }), 200
    
    except Exception as e:
        logger.error(f"Error fetching billings: {str(e)}")
        return jsonify({'error': 'Failed to fetch billings'}), 500


@billing_bp.route('/billing', methods=['POST'])
@jwt_required()
@role_required(['admin', 'doctor', 'receptionist'])
def create_billing():
    """Create a new billing record."""
    try:
        data = request.get_json()
        current_user = get_jwt_identity()
        
        # Validate required fields
        required_fields = ['client_id', 'total_amount', 'items']
        for field in required_fields:
            if not data.get(field):
                return jsonify({'error': f'{field} is required'}), 400
        
        # Verify client exists
        client = Client.query.get_or_404(data['client_id'])
        
        # Generate invoice number
        invoice_number = f"INV-{datetime.utcnow().strftime('%Y%m%d')}-{str(uuid.uuid4())[:8].upper()}"
        
        # Create billing record
        billing = Billing(
            client_id=data['client_id'],
            visit_id=data.get('visit_id'),
            admission_id=data.get('admission_id'),
            invoice_number=invoice_number,
            total_amount=data['total_amount'],
            payment_method=data.get('payment_method'),
            insurance_provider=data.get('insurance_provider'),
            insurance_claim_number=data.get('insurance_claim_number'),
            due_date=datetime.strptime(data['due_date'], '%Y-%m-%d').date() if data.get('due_date') else None,
            notes=data.get('notes'),
            created_by=current_user
        )
        
        db.session.add(billing)
        db.session.flush()  # Get the billing ID
        
        # Create billing items
        for item_data in data['items']:
            item = BillingItem(
                billing_id=billing.id,
                item_type=item_data['item_type'],
                description=item_data['description'],
                quantity=item_data.get('quantity', 1),
                unit_price=item_data['unit_price'],
                total_price=item_data['total_price'],
                discount=item_data.get('discount', 0)
            )
            db.session.add(item)
        
        db.session.commit()
        
        logger.info(f"Created billing record {invoice_number} for client {client.first_name} {client.last_name}")
        
        return jsonify({
            'message': 'Billing record created successfully',
            'billing': {
                'id': billing.id,
                'invoice_number': billing.invoice_number,
                'client_id': billing.client_id,
                'total_amount': float(billing.total_amount),
                'status': billing.status,
                'created_at': billing.created_at.isoformat()
            }
        }), 201
    
    except Exception as e:
        db.session.rollback()
        logger.error(f"Error creating billing record: {str(e)}")
        return jsonify({'error': 'Failed to create billing record'}), 500


@billing_bp.route('/billing/<billing_id>', methods=['GET'])
@jwt_required()
@role_required(['admin', 'doctor', 'receptionist'])
def get_billing(billing_id):
    """Get a specific billing record by ID."""
    try:
        billing = Billing.query.get_or_404(billing_id)
        
        # Get billing items
        items = []
        for item in billing.items:
            items.append({
                'id': item.id,
                'item_type': item.item_type,
                'description': item.description,
                'quantity': item.quantity,
                'unit_price': float(item.unit_price),
                'total_price': float(item.total_price),
                'discount': float(item.discount)
            })
        
        return jsonify({
            'id': billing.id,
            'client_id': billing.client_id,
            'client_name': f"{billing.client.first_name} {billing.client.last_name}" if billing.client else None,
            'visit_id': billing.visit_id,
            'admission_id': billing.admission_id,
            'invoice_number': billing.invoice_number,
            'total_amount': float(billing.total_amount),
            'paid_amount': float(billing.paid_amount),
            'balance': float(billing.total_amount - billing.paid_amount),
            'status': billing.status,
            'payment_method': billing.payment_method,
            'insurance_provider': billing.insurance_provider,
            'insurance_claim_number': billing.insurance_claim_number,
            'due_date': billing.due_date.isoformat() if billing.due_date else None,
            'payment_date': billing.payment_date.isoformat() if billing.payment_date else None,
            'notes': billing.notes,
            'items': items,
            'created_by': billing.created_by,
            'created_at': billing.created_at.isoformat(),
            'updated_at': billing.updated_at.isoformat()
        }), 200
    
    except Exception as e:
        logger.error(f"Error fetching billing record {billing_id}: {str(e)}")
        return jsonify({'error': 'Billing record not found'}), 404


@billing_bp.route('/billing/<billing_id>', methods=['PUT'])
@jwt_required()
@role_required(['admin', 'receptionist'])
def update_billing(billing_id):
    """Update a billing record."""
    try:
        billing = Billing.query.get_or_404(billing_id)
        data = request.get_json()
        
        # Update fields
        if 'payment_method' in data:
            billing.payment_method = data['payment_method']
        if 'insurance_provider' in data:
            billing.insurance_provider = data['insurance_provider']
        if 'insurance_claim_number' in data:
            billing.insurance_claim_number = data['insurance_claim_number']
        if 'due_date' in data:
            billing.due_date = datetime.strptime(data['due_date'], '%Y-%m-%d').date()
        if 'notes' in data:
            billing.notes = data['notes']
        if 'status' in data:
            billing.status = data['status']
        
        db.session.commit()
        
        logger.info(f"Updated billing record {billing.invoice_number}")
        
        return jsonify({
            'message': 'Billing record updated successfully',
            'billing': {
                'id': billing.id,
                'invoice_number': billing.invoice_number,
                'status': billing.status,
                'updated_at': billing.updated_at.isoformat()
            }
        }), 200
    
    except Exception as e:
        db.session.rollback()
        logger.error(f"Error updating billing record {billing_id}: {str(e)}")
        return jsonify({'error': 'Failed to update billing record'}), 500


@billing_bp.route('/billing/<billing_id>/payment', methods=['POST'])
@jwt_required()
@role_required(['admin', 'receptionist'])
def process_payment(billing_id):
    """Process payment for a billing record."""
    try:
        billing = Billing.query.get_or_404(billing_id)
        data = request.get_json()
        
        # Validate payment amount
        payment_amount = float(data.get('payment_amount', 0))
        if payment_amount <= 0:
            return jsonify({'error': 'Payment amount must be greater than 0'}), 400
        
        remaining_balance = billing.total_amount - billing.paid_amount
        if payment_amount > remaining_balance:
            return jsonify({'error': 'Payment amount exceeds remaining balance'}), 400
        
        # Update payment information
        billing.paid_amount += payment_amount
        billing.payment_method = data.get('payment_method', billing.payment_method)
        
        # Update status based on payment
        if billing.paid_amount >= billing.total_amount:
            billing.status = 'paid'
            billing.payment_date = datetime.utcnow()
        elif billing.paid_amount > 0:
            billing.status = 'partially_paid'
        
        db.session.commit()
        
        logger.info(f"Processed payment of {payment_amount} for billing {billing.invoice_number}")
        
        return jsonify({
            'message': 'Payment processed successfully',
            'billing': {
                'id': billing.id,
                'invoice_number': billing.invoice_number,
                'paid_amount': float(billing.paid_amount),
                'balance': float(billing.total_amount - billing.paid_amount),
                'status': billing.status,
                'payment_date': billing.payment_date.isoformat() if billing.payment_date else None
            }
        }), 200
    
    except Exception as e:
        db.session.rollback()
        logger.error(f"Error processing payment for billing {billing_id}: {str(e)}")
        return jsonify({'error': 'Failed to process payment'}), 500


@billing_bp.route('/clients/<client_id>/billing', methods=['GET'])
@jwt_required()
@role_required(['admin', 'doctor', 'receptionist'])
def get_client_billing(client_id):
    """Get all billing records for a specific client."""
    try:
        # Verify client exists
        client = Client.query.get_or_404(client_id)
        
        page = int(request.args.get('page', 1))
        per_page = min(int(request.args.get('per_page', 20)), 100)
        
        billings = Billing.query.filter_by(client_id=client_id)\
            .order_by(Billing.created_at.desc())\
            .paginate(page=page, per_page=per_page, error_out=False)
        
        result = []
        for billing in billings.items:
            billing_data = {
                'id': billing.id,
                'invoice_number': billing.invoice_number,
                'total_amount': float(billing.total_amount),
                'paid_amount': float(billing.paid_amount),
                'balance': float(billing.total_amount - billing.paid_amount),
                'status': billing.status,
                'due_date': billing.due_date.isoformat() if billing.due_date else None,
                'payment_date': billing.payment_date.isoformat() if billing.payment_date else None,
                'created_at': billing.created_at.isoformat()
            }
            result.append(billing_data)
        
        return jsonify({
            'billings': result,
            'client': {
                'id': client.id,
                'name': f"{client.first_name} {client.last_name}"
            },
            'pagination': {
                'page': billings.page,
                'pages': billings.pages,
                'per_page': billings.per_page,
                'total': billings.total,
                'has_next': billings.has_next,
                'has_prev': billings.has_prev
            }
        }), 200
    
    except Exception as e:
        logger.error(f"Error fetching billing records for client {client_id}: {str(e)}")
        return jsonify({'error': 'Failed to fetch billing records'}), 500


# Insurance Management Routes
@billing_bp.route('/insurance-providers', methods=['GET'])
@jwt_required()
@role_required(['admin', 'receptionist'])
def get_insurance_providers():
    """Get all insurance providers."""
    try:
        is_active = request.args.get('is_active', 'true').lower() == 'true'
        
        providers = InsuranceProvider.query.filter_by(is_active=is_active)\
            .order_by(InsuranceProvider.name).all()
        
        result = []
        for provider in providers:
            provider_data = {
                'id': provider.id,
                'name': provider.name,
                'contact_person': provider.contact_person,
                'phone': provider.phone,
                'email': provider.email,
                'address': provider.address,
                'coverage_details': provider.coverage_details,
                'is_active': provider.is_active,
                'created_at': provider.created_at.isoformat()
            }
            result.append(provider_data)
        
        return jsonify({'insurance_providers': result}), 200
    
    except Exception as e:
        logger.error(f"Error fetching insurance providers: {str(e)}")
        return jsonify({'error': 'Failed to fetch insurance providers'}), 500


@billing_bp.route('/insurance-providers', methods=['POST'])
@jwt_required()
@role_required(['admin'])
def create_insurance_provider():
    """Create a new insurance provider."""
    try:
        data = request.get_json()
        
        # Validate required fields
        if not data.get('name'):
            return jsonify({'error': 'Provider name is required'}), 400
        
        # Check if provider already exists
        if InsuranceProvider.query.filter_by(name=data['name']).first():
            return jsonify({'error': 'Insurance provider already exists'}), 400
        
        # Create provider
        provider = InsuranceProvider(
            name=data['name'],
            contact_person=data.get('contact_person'),
            phone=data.get('phone'),
            email=data.get('email'),
            address=data.get('address'),
            coverage_details=data.get('coverage_details')
        )
        
        db.session.add(provider)
        db.session.commit()
        
        logger.info(f"Created insurance provider: {provider.name}")
        
        return jsonify({
            'message': 'Insurance provider created successfully',
            'provider': {
                'id': provider.id,
                'name': provider.name,
                'created_at': provider.created_at.isoformat()
            }
        }), 201
    
    except Exception as e:
        db.session.rollback()
        logger.error(f"Error creating insurance provider: {str(e)}")
        return jsonify({'error': 'Failed to create insurance provider'}), 500


@billing_bp.route('/clients/<client_id>/insurance', methods=['GET'])
@jwt_required()
@role_required(['admin', 'doctor', 'receptionist'])
def get_client_insurance(client_id):
    """Get insurance information for a client."""
    try:
        # Verify client exists
        client = Client.query.get_or_404(client_id)
        
        insurances = ClientInsurance.query.filter_by(client_id=client_id)\
            .order_by(ClientInsurance.is_primary.desc()).all()
        
        result = []
        for insurance in insurances:
            insurance_data = {
                'id': insurance.id,
                'provider_id': insurance.provider_id,
                'provider_name': insurance.provider.name if insurance.provider else None,
                'policy_number': insurance.policy_number,
                'group_number': insurance.group_number,
                'status': insurance.status,
                'effective_date': insurance.effective_date.isoformat(),
                'expiry_date': insurance.expiry_date.isoformat() if insurance.expiry_date else None,
                'copay_amount': float(insurance.copay_amount) if insurance.copay_amount else None,
                'deductible': float(insurance.deductible) if insurance.deductible else None,
                'coverage_percentage': insurance.coverage_percentage,
                'is_primary': insurance.is_primary,
                'created_at': insurance.created_at.isoformat()
            }
            result.append(insurance_data)
        
        return jsonify({
            'insurances': result,
            'client': {
                'id': client.id,
                'name': f"{client.first_name} {client.last_name}"
            }
        }), 200
    
    except Exception as e:
        logger.error(f"Error fetching insurance for client {client_id}: {str(e)}")
        return jsonify({'error': 'Failed to fetch client insurance'}), 500


@billing_bp.route('/clients/<client_id>/insurance', methods=['POST'])
@jwt_required()
@role_required(['admin', 'receptionist'])
def add_client_insurance(client_id):
    """Add insurance for a client."""
    try:
        data = request.get_json()
        
        # Verify client exists
        client = Client.query.get_or_404(client_id)
        
        # Validate required fields
        required_fields = ['provider_id', 'policy_number', 'effective_date']
        for field in required_fields:
            if not data.get(field):
                return jsonify({'error': f'{field} is required'}), 400
        
        # Verify provider exists
        provider = InsuranceProvider.query.get_or_404(data['provider_id'])
        
        # Check if this policy already exists for the client
        existing = ClientInsurance.query.filter_by(
            client_id=client_id,
            provider_id=data['provider_id'],
            policy_number=data['policy_number']
        ).first()
        
        if existing:
            return jsonify({'error': 'This insurance policy already exists for the client'}), 400
        
        # If this is primary insurance, make others non-primary
        if data.get('is_primary', False):
            ClientInsurance.query.filter_by(client_id=client_id, is_primary=True)\
                .update({'is_primary': False})
        
        # Create client insurance
        insurance = ClientInsurance(
            client_id=client_id,
            provider_id=data['provider_id'],
            policy_number=data['policy_number'],
            group_number=data.get('group_number'),
            effective_date=datetime.strptime(data['effective_date'], '%Y-%m-%d').date(),
            expiry_date=datetime.strptime(data['expiry_date'], '%Y-%m-%d').date() if data.get('expiry_date') else None,
            copay_amount=data.get('copay_amount'),
            deductible=data.get('deductible'),
            coverage_percentage=data.get('coverage_percentage'),
            is_primary=data.get('is_primary', False)
        )
        
        db.session.add(insurance)
        db.session.commit()
        
        logger.info(f"Added insurance for client {client.first_name} {client.last_name}")
        
        return jsonify({
            'message': 'Client insurance added successfully',
            'insurance': {
                'id': insurance.id,
                'provider_name': provider.name,
                'policy_number': insurance.policy_number,
                'is_primary': insurance.is_primary
            }
        }), 201
    
    except Exception as e:
        db.session.rollback()
        logger.error(f"Error adding client insurance: {str(e)}")
        return jsonify({'error': 'Failed to add client insurance'}), 500


@billing_bp.route('/billing/statistics', methods=['GET'])
@jwt_required()
@role_required(['admin', 'receptionist'])
def get_billing_statistics():
    """Get billing statistics."""
    try:
        # Status counts
        status_counts = {}
        for status in Billing.STATUSES:
            count = Billing.query.filter_by(status=status).count()
            status_counts[status] = count
        
        # Revenue statistics
        total_revenue = db.session.query(db.func.sum(Billing.paid_amount)).scalar() or 0
        pending_amount = db.session.query(db.func.sum(Billing.total_amount - Billing.paid_amount))\
            .filter(Billing.status.in_(['pending', 'partially_paid'])).scalar() or 0
        
        # Today's collections
        today = datetime.utcnow().date()
        today_collections = db.session.query(db.func.sum(Billing.paid_amount))\
            .filter(db.func.date(Billing.payment_date) == today).scalar() or 0
        
        # Overdue bills
        overdue_bills = Billing.query.filter(
            Billing.due_date < today,
            Billing.status.in_(['pending', 'partially_paid'])
        ).count()
        
        return jsonify({
            'status_counts': status_counts,
            'revenue': {
                'total_revenue': float(total_revenue),
                'pending_amount': float(pending_amount),
                'today_collections': float(today_collections)
            },
            'overdue_bills': overdue_bills,
            'total_bills': sum(status_counts.values())
        }), 200
    
    except Exception as e:
        logger.error(f"Error fetching billing statistics: {str(e)}")
        return jsonify({'error': 'Failed to fetch billing statistics'}), 500


@billing_bp.route('/billing/statuses', methods=['GET'])
@jwt_required()
def get_billing_statuses():
    """Get all billing statuses."""
    return jsonify({
        'statuses': [
            {'value': status, 'label': status.replace('_', ' ').title()}
            for status in Billing.STATUSES
        ]
    }), 200


@billing_bp.route('/billing/payment-methods', methods=['GET'])
@jwt_required()
def get_payment_methods():
    """Get all payment methods."""
    return jsonify({
        'payment_methods': [
            {'value': method, 'label': method.replace('_', ' ').title()}
            for method in Billing.PAYMENT_METHODS
        ]
    }), 200


@billing_bp.route('/billing/item-types', methods=['GET'])
@jwt_required()
def get_billing_item_types():
    """Get all billing item types."""
    return jsonify({
        'item_types': [
            {'value': item_type, 'label': item_type.replace('_', ' ').title()}
            for item_type in BillingItem.ITEM_TYPES
        ]
    }), 200
