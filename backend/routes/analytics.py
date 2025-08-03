"""
Advanced Analytics API Routes
Comprehensive healthcare analytics and reporting endpoints
"""

from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from backend.database import db
from backend.analytics_engine import AdvancedAnalytics
from backend.utils.auth import roles_required
from backend.security_system import audit_logger, SecurityEventType, RiskLevel
from datetime import datetime, timedelta
import logging

# Configure analytics logger
analytics_logger = logging.getLogger('analytics')

analytics_bp = Blueprint('analytics', __name__)

@analytics_bp.route('/dashboard/comprehensive', methods=['GET'])
@jwt_required()
@roles_required('admin', 'doctor')
def get_comprehensive_dashboard(current_user):
    """Get comprehensive dashboard analytics"""
    try:
        current_user = get_jwt_identity()
        days = request.args.get('days', 30, type=int)
        
        # Log analytics access
        audit_logger.log_security_event(
            SecurityEventType.DATA_ACCESS,
            user_id=current_user,
            resource_accessed="comprehensive_analytics",
            risk_level=RiskLevel.LOW
        )
        
        # Generate comprehensive report
        report = AdvancedAnalytics.generate_comprehensive_report(days)
        
        analytics_logger.info(f"Comprehensive dashboard accessed by user {current_user}")
        
        return jsonify({
            'status': 'success',
            'data': report
        }), 200
        
    except Exception as e:
        analytics_logger.error(f"Error generating comprehensive dashboard: {e}")
        return jsonify({
            'status': 'error',
            'message': 'Failed to generate analytics report'
        }), 500

@analytics_bp.route('/patient-flow', methods=['GET'])
@jwt_required()
@roles_required('admin', 'doctor', 'nurse')
def get_patient_flow_analytics(current_user):
    """Get patient flow analytics"""
    try:
        current_user = get_jwt_identity()
        days = request.args.get('days', 30, type=int)
        
        flow_data = AdvancedAnalytics.get_patient_flow_analytics(days)
        
        return jsonify({
            'status': 'success',
            'data': flow_data
        }), 200
        
    except Exception as e:
        analytics_logger.error(f"Error getting patient flow analytics: {e}")
        return jsonify({
            'status': 'error',
            'message': 'Failed to retrieve patient flow data'
        }), 500

@analytics_bp.route('/revenue', methods=['GET'])
@jwt_required()
@roles_required('admin', 'billing')
def get_revenue_analytics(current_user):
    """Get revenue analytics"""
    try:
        current_user = get_jwt_identity()
        days = request.args.get('days', 30, type=int)
        
        # Log sensitive financial data access
        audit_logger.log_security_event(
            SecurityEventType.DATA_ACCESS,
            user_id=current_user,
            resource_accessed="revenue_analytics",
            risk_level=RiskLevel.MEDIUM
        )
        
        revenue_data = AdvancedAnalytics.get_revenue_analytics(days)
        
        return jsonify({
            'status': 'success',
            'data': revenue_data
        }), 200
        
    except Exception as e:
        analytics_logger.error(f"Error getting revenue analytics: {e}")
        return jsonify({
            'status': 'error',
            'message': 'Failed to retrieve revenue data'
        }), 500

@analytics_bp.route('/clinical-quality', methods=['GET'])
@jwt_required()
@roles_required('admin', 'doctor')
def get_clinical_quality_metrics(current_user):
    """Get clinical quality metrics"""
    try:
        current_user = get_jwt_identity()
        days = request.args.get('days', 30, type=int)
        
        quality_metrics = AdvancedAnalytics.get_clinical_quality_metrics(days)
        
        return jsonify({
            'status': 'success',
            'data': quality_metrics
        }), 200
        
    except Exception as e:
        analytics_logger.error(f"Error getting clinical quality metrics: {e}")
        return jsonify({
            'status': 'error',
            'message': 'Failed to retrieve quality metrics'
        }), 500

@analytics_bp.route('/operational-efficiency', methods=['GET'])
@jwt_required()
@roles_required('admin')
def get_operational_efficiency(current_user):
    """Get operational efficiency metrics"""
    try:
        current_user = get_jwt_identity()
        
        efficiency_data = AdvancedAnalytics.get_operational_efficiency_metrics()
        
        return jsonify({
            'status': 'success',
            'data': efficiency_data
        }), 200
        
    except Exception as e:
        analytics_logger.error(f"Error getting operational efficiency: {e}")
        return jsonify({
            'status': 'error',
            'message': 'Failed to retrieve efficiency metrics'
        }), 500

@analytics_bp.route('/predictive-insights', methods=['GET'])
@jwt_required()
@roles_required('admin', 'doctor')
def get_predictive_insights(current_user):
    """Get predictive healthcare insights"""
    try:
        current_user = get_jwt_identity()
        days = request.args.get('days', 90, type=int)
        
        insights = AdvancedAnalytics.get_predictive_insights(days)
        
        return jsonify({
            'status': 'success',
            'data': insights
        }), 200
        
    except Exception as e:
        analytics_logger.error(f"Error getting predictive insights: {e}")
        return jsonify({
            'status': 'error',
            'message': 'Failed to retrieve predictive insights'
        }), 500

@analytics_bp.route('/export/report', methods=['POST'])
@jwt_required()
@roles_required('admin')
def export_analytics_report(current_user):
    """Export comprehensive analytics report"""
    try:
        current_user = get_jwt_identity()
        data = request.get_json()
        
        report_type = data.get('report_type', 'comprehensive')
        format_type = data.get('format', 'json')  # json, csv, pdf
        days = data.get('days', 30)
        
        # Log data export
        audit_logger.log_security_event(
            SecurityEventType.DATA_EXPORT,
            user_id=current_user,
            resource_accessed=f"analytics_export_{report_type}",
            details={'format': format_type, 'days': days},
            risk_level=RiskLevel.HIGH
        )
        
        if report_type == 'comprehensive':
            report_data = AdvancedAnalytics.generate_comprehensive_report(days)
        else:
            return jsonify({
                'status': 'error',
                'message': 'Invalid report type'
            }), 400
        
        # In a real implementation, you'd format the data according to format_type
        # For now, return JSON
        
        return jsonify({
            'status': 'success',
            'data': report_data,
            'export_info': {
                'format': format_type,
                'generated_at': datetime.utcnow().isoformat(),
                'generated_by': current_user
            }
        }), 200
        
    except Exception as e:
        analytics_logger.error(f"Error exporting analytics report: {e}")
        return jsonify({
            'status': 'error',
            'message': 'Failed to export report'
        }), 500
