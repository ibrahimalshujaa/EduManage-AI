from reportlab.lib.pagesizes import LETTER
from reportlab.pdfgen import canvas
from reportlab.lib import colors
from reportlab.lib.units import inch
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
import os

def export_student_report(student_name, student_class, gpa, success_prob, risk_level, grades, recommendations, output_path):
    doc = SimpleDocTemplate(output_path, pagesize=LETTER)
    elements = []
    
    styles = getSampleStyleSheet()
    title_style = ParagraphStyle(
        'TitleStyle',
        parent=styles['Heading1'],
        fontSize=24,
        textColor=colors.HexColor("#0F172A"),
        spaceAfter=20,
        alignment=1
    )
    
    # Header
    elements.append(Paragraph("EduManage AI - Academic Performance Report", title_style))
    elements.append(Spacer(1, 0.2 * inch))
    
    # Student Info
    elements.append(Paragraph(f"<b>Student Name:</b> {student_name}", styles['Normal']))
    elements.append(Paragraph(f"<b>Class:</b> {student_class}", styles['Normal']))
    elements.append(Paragraph(f"<b>Date:</b> 2024-05-10", styles['Normal']))
    elements.append(Spacer(1, 0.3 * inch))
    
    # Key Stats Table
    data = [
        ["Overall GPA", "Success Probability", "Risk Level"],
        [f"{gpa:.1f}", f"{success_prob:.1f}%", risk_level]
    ]
    t = Table(data, colWidths=[2*inch, 2*inch, 2*inch])
    t.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor("#38BDF8")),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 12),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
        ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
        ('GRID', (0, 0), (-1, -1), 1, colors.grey)
    ]))
    elements.append(t)
    elements.append(Spacer(1, 0.4 * inch))
    
    # Grades Table
    elements.append(Paragraph("<b>Subject Breakdown</b>", styles['Heading2']))
    grade_data = [["Subject", "Grade"]]
    for sub, grade in grades:
        grade_data.append([sub, f"{grade:.1f}"])
        
    gt = Table(grade_data, colWidths=[3*inch, 1*inch])
    gt.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor("#1E293B")),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.grey)
    ]))
    elements.append(gt)
    elements.append(Spacer(1, 0.4 * inch))
    
    # AI Recommendations
    elements.append(Paragraph("<b>AI Smart Recommendations</b>", styles['Heading2']))
    for rec in recommendations:
        elements.append(Paragraph(f"• <b>{rec['title']}:</b> {rec['description']}", styles['Normal']))
        elements.append(Spacer(1, 0.1 * inch))
        
    # Signature Section
    elements.append(Spacer(1, 0.5 * inch))
    elements.append(Paragraph("_" * 30, styles['Normal']))
    elements.append(Paragraph("Teacher Signature", styles['Normal']))
    
    doc.build(elements)
    print(f"Report exported to {output_path}")

if __name__ == "__main__":
    # Test export
    export_student_report(
        "Alice Johnson", "Grade 10-A", 88.5, 92.4, "Low Risk",
        [("Math", 90), ("Science", 85)],
        [{"title": "Great Progress", "description": "Keep up the good work!"}],
        "test_report.pdf"
    )
