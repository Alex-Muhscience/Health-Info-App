import csv
import io
from datetime import datetime
from typing import Dict, Any, Optional, List

from flask import make_response, current_app
from marshmallow.fields import List
from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_LEFT
from reportlab.lib.pagesizes import letter, landscape
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle,
    PageBreak
)
from sqlalchemy import or_, and_

from backend import db
from backend.models import Client, Program, Visit, User
from backend.utils.helpers import DateUtils


class DataExporter:
    """Utility class for exporting data to various formats (CSV, PDF)"""

    @staticmethod
    def _register_fonts() -> None:
        """Register custom fonts for PDF generation"""
        try:
            pdfmetrics.registerFont(TTFont('Roboto', 'Roboto-Regular.ttf'))
            pdfmetrics.registerFont(TTFont('Roboto-Bold', 'Roboto-Bold.ttf'))
        except Exception as e:
            current_app.logger.warning(f"Failed to register custom fonts: {str(e)}")
            # Fallback to default fonts

    @staticmethod
    def _export_clients_csv(clients: List[Client],
                          include_programs: bool,
                          include_visits: bool) -> Any:
        """Export clients data to CSV format"""
        si = io.StringIO()
        writer = csv.writer(si)

        headers = [
            'ID', 'First Name', 'Last Name', 'Email', 'Phone', 'Gender',
            'Date of Birth', 'Address', 'Emergency Contact', 'Status',
            'Created Date'
        ]

        if include_programs:
            headers.extend(['Programs Enrolled', 'Program Status'])
        if include_visits:
            headers.extend(['Last Visit Date', 'Total Visits'])

        writer.writerow(headers)

        for client in clients:
            row = [
                client.id,
                client.first_name,
                client.last_name,
                client.email,
                client.phone,
                client.gender,
                DateUtils.format_date(client.dob) if client.dob else '',
                client.address,
                f"{client.emergency_contact_name or ''} {client.emergency_contact_phone or ''}".strip(),
                'Active' if client.is_active else 'Inactive',
                DateUtils.format_date(client.created_at) if client.created_at else ''
            ]

            if include_programs:
                programs = ", ".join([p.program.name for p in client.programs])
                program_statuses = ", ".join([p.status for p in client.programs])
                row.extend([programs, program_statuses])

            if include_visits:
                last_visit = client.visits.order_by(Visit.visit_date.desc()).first()
                total_visits = client.visits.count()
                row.extend([
                    DateUtils.format_date(last_visit.visit_date) if last_visit else '',
                    total_visits
                ])

            writer.writerow(row)

        return si.getvalue()

    @staticmethod
    def _export_programs_csv(programs: List[Program]) -> Any:
        """Export programs data to CSV format"""
        si = io.StringIO()
        writer = csv.writer(si)

        headers = [
            'ID', 'Program Name', 'Description', 'Status',
            'Total Enrollments', 'Active Enrollments', 'Created Date'
        ]
        writer.writerow(headers)

        for program in programs:
            total = len(program.clients)
            active = len([c for c in program.clients if c.status == 'active'])

            writer.writerow([
                program.id,
                program.name,
                program.description or '',
                'Active' if program.is_active else 'Inactive',
                total,
                active,
                DateUtils.format_date(program.created_at) if program.created_at else ''
            ])

        return si.getvalue()

    @staticmethod
    def _export_visits_csv(visits: List[Visit]) -> Any:
        """Export visits data to CSV format"""
        si = io.StringIO()
        writer = csv.writer(si)

        headers = [
            'ID', 'Visit Date', 'Client', 'Practitioner',
            'Purpose', 'Status', 'Program', 'Notes'
        ]
        writer.writerow(headers)

        for visit in visits:
            writer.writerow([
                visit.id,
                DateUtils.format_date(visit.visit_date, '%Y-%m-%d %H:%M'),
                f"{visit.client.first_name} {visit.client.last_name}",
                f"{visit.practitioner.first_name} {visit.practitioner.last_name}",
                visit.purpose,
                visit.status.capitalize(),
                visit.program.name if visit.program else '',
                visit.notes or ''
            ])

        return si.getvalue()

    @staticmethod
    def _create_pdf_response(content: bytes, filename_prefix: str) -> Any:
        """Create a Flask response for PDF downloads"""
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        response = make_response(content)
        response.headers['Content-Type'] = 'application/pdf'
        response.headers['Content-Disposition'] = (
            f'attachment; filename={filename_prefix}_export_{timestamp}.pdf'
        )
        return response

    @staticmethod
    def _create_csv_response(content: str, filename_prefix: str) -> Any:
        """Create a Flask response for CSV downloads"""
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        response = make_response(content)
        response.headers["Content-Disposition"] = (
            f"attachment; filename={filename_prefix}_export_{timestamp}.csv"
        )
        response.headers["Content-type"] = "text/csv"
        return response

    @staticmethod
    def export_clients(
            format: str = 'csv',
            filters: Optional[Dict[str, Any]] = None,
            include_programs: bool = False,
            include_visits: bool = False
    ) -> Any:
        """Export clients data in specified format"""
        query = Client.query
        if filters:
            if 'is_active' in filters:
                query = query.filter_by(is_active=filters['is_active'])
            if 'created_after' in filters:
                query = query.filter(Client.created_at >= filters['created_after'])
            if 'created_before' in filters:
                query = query.filter(Client.created_at <= filters['created_before'])
            if 'search' in filters:
                search = f"%{filters['search']}%"
                query = query.filter(
                    or_(
                        Client.first_name.ilike(search),
                        Client.last_name.ilike(search),
                        Client.email.ilike(search),
                        Client.phone.ilike(search)
                    )
                )

        clients = query.order_by(Client.last_name, Client.first_name).all()

        if format.lower() == 'pdf':
            content = DataExporter._export_clients_pdf(clients, include_programs, include_visits)
            return DataExporter._create_pdf_response(content, "clients")
        else:
            content = DataExporter._export_clients_csv(clients, include_programs, include_visits)
            return DataExporter._create_csv_response(content, "clients")

    @staticmethod
    def export_programs(format: str = 'csv') -> Any:
        """Export programs data in specified format"""
        programs = Program.query.options(
            db.joinedload(Program.clients)
        ).order_by(Program.name).all()

        if format.lower() == 'pdf':
            content = DataExporter._export_programs_pdf(programs)
            return DataExporter._create_pdf_response(content, "programs")
        else:
            content = DataExporter._export_programs_csv(programs)
            return DataExporter._create_csv_response(content, "programs")

    @staticmethod
    def export_visits(format: str = 'csv', filters: Optional[Dict[str, Any]] = None) -> Any:
        """Export visits data in specified format"""
        query = Visit.query.join(Client).join(User).options(
            db.joinedload(Visit.client),
            db.joinedload(Visit.practitioner)
        )

        if filters:
            if 'date_range' in filters:
                start_date, end_date = DateUtils.parse_date_range(filters['date_range'])
                if start_date and end_date:
                    query = query.filter(
                        and_(
                            Visit.visit_date >= start_date,
                            Visit.visit_date <= end_date
                        )
                    )
            if 'status' in filters:
                query = query.filter(Visit.status == filters['status'])
            if 'client_id' in filters:
                query = query.filter(Visit.client_id == filters['client_id'])
            if 'practitioner_id' in filters:
                query = query.filter(Visit.created_by == filters['practitioner_id'])

        visits = query.order_by(Visit.visit_date.desc()).all()

        if format.lower() == 'pdf':
            content = DataExporter._export_visits_pdf(visits)
            return DataExporter._create_pdf_response(content, "visits")
        else:
            content = DataExporter._export_visits_csv(visits)
            return DataExporter._create_csv_response(content, "visits")

    @staticmethod
    def _export_clients_pdf(clients: List[Client],
                          include_programs: bool,
                          include_visits: bool) -> bytes:
        """Export clients data to PDF format"""
        buffer = io.BytesIO()
        doc = SimpleDocTemplate(
            buffer,
            pagesize=landscape(letter),
            rightMargin=inch/2,
            leftMargin=inch/2,
            topMargin=inch/2,
            bottomMargin=inch/2
        )

        styles = getSampleStyleSheet()
        styles.add(ParagraphStyle(
            name='Header1',
            fontSize=14,
            leading=16,
            alignment=TA_CENTER,
            fontName='Roboto-Bold'
        ))
        styles.add(ParagraphStyle(
            name='Body',
            fontSize=10,
            leading=12,
            alignment=TA_LEFT,
            fontName='Roboto'
        ))

        elements = []

        # Add title
        elements.append(Paragraph("Client Export Report", styles['Header1']))
        elements.append(Spacer(1, 0.2*inch))

        # Prepare data for table
        data = [[
            'ID', 'Name', 'Contact', 'Gender', 'Status',
            'DOB', 'Created Date'
        ]]

        if include_programs:
            data[0].extend(['Programs', 'Status'])
        if include_visits:
            data[0].extend(['Last Visit', 'Total Visits'])

        for client in clients:
            row = [
                str(client.id),
                f"{client.first_name} {client.last_name}",
                f"{client.phone}\n{client.email}",
                client.gender,
                'Active' if client.is_active else 'Inactive',
                DateUtils.format_date(client.dob) if client.dob else 'N/A',
                DateUtils.format_date(client.created_at) if client.created_at else 'N/A'
            ]

            if include_programs:
                programs = "\n".join([p.program.name for p in client.programs])
                statuses = "\n".join([p.status for p in client.programs])
                row.extend([programs, statuses])

            if include_visits:
                last_visit = client.visits.order_by(Visit.visit_date.desc()).first()
                total_visits = client.visits.count()
                row.extend([
                    DateUtils.format_date(last_visit.visit_date) if last_visit else 'N/A',
                    str(total_visits)
                ])

            data.append(row)

        # Create table
        table = Table(data)
        table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#4472C4')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (-1, 0), 'Roboto-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 10),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('BACKGROUND', (0, 1), (-1, -1), colors.HexColor('#D9E1F2')),
            ('GRID', (0, 0), (-1, -1), 1, colors.black),
            ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ]))

        elements.append(table)
        elements.append(Spacer(1, 0.2*inch))

        # Add footer
        elements.append(Paragraph(
            f"Generated on {DateUtils.format_date(datetime.now(), '%Y-%m-%d %H:%M')}",
            styles['Body']
        ))

        # Build PDF
        doc.build(elements)

        buffer.seek(0)
        return buffer.getvalue()

    @staticmethod
    def _export_programs_pdf(programs: List[Program]) -> bytes:
        """Export programs data to PDF format"""
        buffer = io.BytesIO()
        doc = SimpleDocTemplate(
            buffer,
            pagesize=letter,
            rightMargin=inch/2,
            leftMargin=inch/2,
            topMargin=inch/2,
            bottomMargin=inch/2
        )

        styles = getSampleStyleSheet()
        styles.add(ParagraphStyle(
            name='Header1',
            fontSize=14,
            leading=16,
            alignment=TA_CENTER,
            fontName='Roboto-Bold'
        ))

        elements = []
        elements.append(Paragraph("Programs Export Report", styles['Header1']))
        elements.append(Spacer(1, 0.2*inch))

        # Program summary table
        summary_data = [[
            'ID', 'Program Name', 'Status', 'Enrollments',
            'Active', 'Created Date'
        ]]

        for program in programs:
            total = len(program.clients)
            active = len([c for c in program.clients if c.status == 'active'])

            summary_data.append([
                str(program.id),
                program.name,
                'Active' if program.is_active else 'Inactive',
                str(total),
                str(active),
                DateUtils.format_date(program.created_at) if program.created_at else 'N/A'
            ])

        summary_table = Table(summary_data, colWidths=[0.5*inch, 2*inch, 0.8*inch, 0.8*inch, 0.8*inch, 1*inch])
        summary_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor("#4472C4")),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (-1, 0), 'Roboto-Bold'),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('BACKGROUND', (0, 1), (-1, -1), colors.HexColor("#D9E1F2")),
            ('GRID', (0, 0), (-1, -1), 1, colors.black),
        ]))

        elements.append(summary_table)
        elements.append(Spacer(1, 0.3*inch))

        # Add detailed program information
        for program in programs:
            elements.append(Paragraph(
                f"Program: {program.name}",
                ParagraphStyle(
                    name='ProgramHeader',
                    fontSize=12,
                    leading=14,
                    fontName='Roboto-Bold',
                    textColor=colors.HexColor('#2F5597'),
                    spaceAfter=6
                )
            ))

            if program.description:
                elements.append(Paragraph(
                    program.description,
                    ParagraphStyle(
                        name='ProgramDesc',
                        fontSize=10,
                        leading=12,
                        fontName='Roboto',
                        spaceAfter=12
                    )
                ))

            # Client enrollment table for this program
            enrollment_data = [['Client ID', 'Client Name', 'Status', 'Enrollment Date']]
            for enrollment in program.clients:
                enrollment_data.append([
                    str(enrollment.client.id),
                    f"{enrollment.client.first_name} {enrollment.client.last_name}",
                    enrollment.status.capitalize(),
                    DateUtils.format_date(enrollment.enrollment_date) if enrollment.enrollment_date else 'N/A'
                ])

            enrollment_table = Table(enrollment_data)
            enrollment_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#70AD47')),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                ('FONTNAME', (0, 0), (-1, 0), 'Roboto-Bold'),
                ('FONTSIZE', (0, 0), (-1, 0), 10),
                ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                ('BACKGROUND', (0, 1), (-1, -1), colors.HexColor('#E2EFDA')),
                ('GRID', (0, 0), (-1, -1), 1, colors.black),
            ]))

            elements.append(enrollment_table)
            elements.append(PageBreak())

        # Add footer
        elements.append(Spacer(1, 0.2*inch))
        elements.append(Paragraph(
            f"Generated on {DateUtils.format_date(datetime.now(), '%Y-%m-%d %H:%M')}",
            ParagraphStyle(
                name='Footer',
                fontSize=8,
                fontName='Roboto',
                alignment=TA_CENTER,
                spaceBefore=20
            )
        ))

        doc.build(elements)
        buffer.seek(0)
        return buffer.getvalue()

    @staticmethod
    def _export_visits_pdf(visits: List[Visit]) -> bytes:
        """Export visits data to PDF format"""
        buffer = io.BytesIO()
        doc = SimpleDocTemplate(
            buffer,
            pagesize=letter,
            rightMargin=inch/2,
            leftMargin=inch/2,
            topMargin=inch/2,
            bottomMargin=inch/2
        )

        styles = getSampleStyleSheet()
        styles.add(ParagraphStyle(
            name='Header1',
            fontSize=14,
            leading=16,
            alignment=TA_CENTER,
            fontName='Roboto-Bold'
        ))

        elements = [Paragraph("Visits Export Report", styles['Header1']), Spacer(1, 0.2*inch)]

        if visits:
            # Summary statistics
            completed = sum(1 for v in visits if v.status == 'completed')
            scheduled = sum(1 for v in visits if v.status == 'scheduled')
            cancelled = sum(1 for v in visits if v.status == 'canceled')

            stats = [
                ["Total Visits", len(visits)],
                ["Completed", completed],
                ["Scheduled", scheduled],
                ["Canceled", cancelled],
                ["Completion Rate", f"{round(completed / len(visits) * 100) if visits else 0}%"]
            ]

            stats_table = Table(stats, colWidths=[2*inch, 1*inch])
            stats_table.setStyle(TableStyle([
                ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#4472C4")),
                ("TEXTCOLOR", (0, 0), (-1, 0), colors.whitesmoke),
                ("ALIGN", (0, 0), (-1, 0), 'LEFT'),
                ("FONTNAME", (0, 0), (-1, 0), 'Roboto-Bold'),
                ("BACKGROUND", (0, 1), (-1, -1), colors.HexColor("#D9E1F2")),
                ("GRID", (0, 0), (-1, -1), 1, colors.black),
            ]))

            elements.append(stats_table)
            elements.append(Spacer(1, 0.3*inch))

            # Visits table
            visits_data = [[
                'Date', 'Client', 'Practitioner', 'Purpose', 'Status', 'Program'
            ]]

            for visit in visits:
                visits_data.append([
                    DateUtils.format_date(visit.visit_date, '%Y-%m-%d %H:%M'),
                    f"{visit.client.first_name} {visit.client.last_name}",
                    f"{visit.practitioner.first_name} {visit.practitioner.last_name}",
                    visit.purpose[:30] + '...' if len(visit.purpose) > 30 else visit.purpose,
                    visit.status.capitalize(),
                    visit.program.name if visit.program else 'N/A'
                ])

            visits_table = Table(visits_data,
                               colWidths=[1.2*inch, 1.5*inch, 1.5*inch, 1.5*inch, 0.8*inch, 1*inch])
            visits_table.setStyle(TableStyle([
                ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#4472C4")),
                ("TEXTCOLOR", (0, 0), (-1, 0), colors.whitesmoke),
                ("ALIGN", (0, 0), (-1, -1), 'LEFT'),
                ("FONTNAME", (0, 0), (-1, 0), 'Roboto-Bold'),
                ("FONTSIZE", (0, 0), (-1, 0), 10),
                ("BOTTOMPADDING", (0, 0), (-1, 0), 12),
                ("BACKGROUND", (0, 1), (-1, -1), colors.HexColor("#D9E1F2")),
                ("GRID", (0, 0), (-1, -1), 1, colors.black),
            ]))

            elements.append(visits_table)
        else:
            elements.append(Paragraph("No visits found matching the criteria", styles['Normal']))

        # Add footer
        elements.append(Spacer(1, 0.2*inch))
        elements.append(Paragraph(
            f"Generated on {DateUtils.format_date(datetime.now(), '%Y-%m-%d %H:%M')}",
            ParagraphStyle(
                name='Footer',
                fontSize=8,
                fontName='Roboto',
                alignment=TA_CENTER,
                spaceBefore=20
            )
        ))

        doc.build(elements)
        buffer.seek(0)
        return buffer.getvalue()


# Initialize fonts when module loads
DataExporter._register_fonts()