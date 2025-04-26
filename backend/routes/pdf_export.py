from flask import Blueprint, make_response
from reportlab.pdfgen import canvas
from io import BytesIO
from backend.models import Client
from backend.utils.auth import token_required

export_pdf_bp = Blueprint('pdf_export', __name__, url_prefix='/api/export')

@export_pdf_bp.route('/clients', methods=['GET'])
@token_required
def export_clients_pdf(current_user):
    buffer = BytesIO()
    p = canvas.Canvas(buffer)
    p.drawString(100, 800, "Client Report")

    clients = Client.query.all()
    y = 770
    for c in clients:
        line = f"{c.first_name} {c.last_name}, {c.gender}, {c.phone}"
        p.drawString(100, y, line)
        y -= 20
        if y < 100:
            p.showPage()
            y = 800

    p.save()
    buffer.seek(0)
    response = make_response(buffer.read())
    response.headers["Content-Disposition"] = "attachment; filename=clients_report.pdf"
    response.headers["Content-Type"] = "application/pdf"
    return response