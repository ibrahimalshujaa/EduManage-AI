import os
import sqlite3
from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, KeepTogether
from reportlab.lib.units import inch
from database import DB_PATH
from datetime import datetime

def get_db_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def generate_pdf_report(report_type, target_id=None):
    filename = f"report_{report_type}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"
    filepath = os.path.join(os.path.dirname(__file__), 'static', 'reports', filename)
    os.makedirs(os.path.dirname(filepath), exist_ok=True)
    
    doc = SimpleDocTemplate(filepath, pagesize=letter)
    styles = getSampleStyleSheet()
    elements = []
    
    # Title
    title_style = ParagraphStyle('TitleStyle', parent=styles['Heading1'], fontSize=24, spaceAfter=20, textColor=colors.HexColor("#38bdf8"))
    
    conn = get_db_connection()
    
    if report_type == 'full':
        elements.append(Paragraph("Institutional Performance Report", title_style))
        elements.append(Paragraph(f"Generated on: {datetime.now().strftime('%Y-%m-%d %H:%M')}", styles['Normal']))
        elements.append(Spacer(1, 0.2*inch))
        
        # Stats
        total_s = conn.execute('SELECT COUNT(*) FROM Students').fetchone()[0]
        total_t = conn.execute('SELECT COUNT(*) FROM Teachers').fetchone()[0]
        avg_s = conn.execute('SELECT AVG(success_probability) FROM Predictions').fetchone()[0] or 0
        
        elements.append(Paragraph(f"Total Students: {total_s}", styles['Normal']))
        elements.append(Paragraph(f"Total Faculty: {total_t}", styles['Normal']))
        elements.append(Paragraph(f"Overall Success Rate: {avg_s:.1f}%", styles['Normal']))
        elements.append(Spacer(1, 0.3*inch))
        
        # Class Performance Table
        elements.append(Paragraph("Class Performance Summary", styles['Heading2']))
        data = [['Class Name', 'Teacher', 'Students', 'Avg Grade', 'Success %']]
        rows = conn.execute('''
            SELECT c.class_name, tu.full_name as teacher_name, COUNT(DISTINCT sc.student_id) as s_count,
                   AVG(g.grade) as avg_g, AVG(p.success_probability) as avg_p
            FROM Classes c
            LEFT JOIN Teachers t ON t.id = c.teacher_id
            LEFT JOIN Users tu ON tu.id = t.user_id
            LEFT JOIN StudentClasses sc ON sc.class_id = c.id
            LEFT JOIN Grades g ON g.student_id = sc.student_id AND g.class_id = c.id
            LEFT JOIN Predictions p ON p.student_id = sc.student_id
            GROUP BY c.id
        ''').fetchall()
        for r in rows:
            data.append([r['class_name'], r['teacher_name'] or 'N/A', str(r['s_count']), f"{r['avg_g'] or 0:.1f}", f"{r['avg_p'] or 0:.1f}"])
            
    elif report_type == 'class':
        class_info = conn.execute('SELECT c.*, u.full_name as teacher_name FROM Classes c JOIN Teachers t ON c.teacher_id = t.id JOIN Users u ON t.user_id = u.id WHERE c.id = ?', (target_id,)).fetchone()
        elements.append(Paragraph(f"Class Report: {class_info['class_name']}", title_style))
        elements.append(Paragraph(f"Instructor: {class_info['teacher_name']}", styles['Normal']))
        elements.append(Spacer(1, 0.2*inch))
        
        data = [['Student Name', 'Avg Grade', 'Success %', 'Risk Level']]
        rows = conn.execute('''
            SELECT u.full_name, AVG(g.grade) as avg_g, p.success_probability, p.risk_level
            FROM StudentClasses sc
            JOIN Students s ON sc.student_id = s.id
            JOIN Users u ON s.user_id = u.id
            LEFT JOIN Grades g ON g.student_id = s.id AND g.class_id = sc.class_id
            LEFT JOIN Predictions p ON p.student_id = s.id
            WHERE sc.class_id = ?
            GROUP BY s.id
        ''', (target_id,)).fetchall()
        for r in rows:
            data.append([r['full_name'], f"{r['avg_g'] or 0:.1f}", f"{r['success_probability'] or 0:.1f}", r['risk_level'] or 'N/A'])
        t = Table(data, hAlign='LEFT')
        t.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor("#1e293b")),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('BACKGROUND', (0, 1), (-1, -1), colors.HexColor("#f8fafc")),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.grey)
        ]))
        elements.append(t)

    elif report_type == 'student':
        student = conn.execute('SELECT u.*, s.student_number, s.study_hours, s.absences, s.family_support FROM Students s JOIN Users u ON s.user_id = u.id WHERE s.id = ?', (target_id,)).fetchone()
        
        # Header with Branding
        header_table = Table([
            [Paragraph("EDUMANAGE AI", ParagraphStyle('Logo', fontSize=22, textColor=colors.HexColor("#38bdf8"), fontWeight='BOLD', letterSpacing=1)), 
             Paragraph(f"Official Academic Statement", ParagraphStyle('Sub', fontSize=11, textColor=colors.grey, alignment=2, italic=True))]
        ], colWidths=[4.2*inch, 2.8*inch])
        elements.append(header_table)
        elements.append(Spacer(1, 0.4*inch))
        
        # Student Info Card
        elements.append(Paragraph(f"STUDENT PROFILE", ParagraphStyle('Section', fontSize=12, textColor=colors.HexColor("#38bdf8"), spaceAfter=10)))
        info_data = [
            [Paragraph(f"<b>Name:</b> {student['full_name']}", styles['Normal']), Paragraph(f"<b>ID:</b> #{student['student_number'] or 'N/A'}", styles['Normal'])],
            [Paragraph(f"<b>Email:</b> {student['email']}", styles['Normal']), Paragraph(f"<b>Status:</b> Active Member", styles['Normal'])]
        ]
        info_table = Table(info_data, colWidths=[3.5*inch, 3.5*inch])
        info_table.setStyle(TableStyle([
            ('BACKGROUND', (0,0), (-1,-1), colors.HexColor("#f8fafc")),
            ('BOX', (0,0), (-1,-1), 1, colors.HexColor("#e2e8f0")),
            ('PADDING', (0,0), (-1,-1), 12),
        ]))
        elements.append(info_table)
        elements.append(Spacer(1, 0.3*inch))
        
        # AI Insights Section
        # AI Insights Section
        pred = conn.execute('SELECT success_probability, risk_level, recommendation FROM Predictions WHERE student_id = ? ORDER BY updated_at DESC LIMIT 1', (target_id,)).fetchone()
        
        elements.append(Paragraph("AI PERFORMANCE & RISK FORECAST", ParagraphStyle('Section', fontSize=12, textColor=colors.HexColor("#38bdf8"), spaceAfter=10)))
        
        # Success Gauge Table
        prob = pred['success_probability'] if pred else 0
        gauge_color = colors.HexColor("#22c55e") if prob > 70 else (colors.HexColor("#eab308") if prob > 40 else colors.HexColor("#ef4444"))
        
        insight_data = [
            [Paragraph("Success Probability", ParagraphStyle('Label', fontSize=9, textColor=colors.grey, alignment=1)),
             Paragraph("Risk Assessment", ParagraphStyle('Label', fontSize=9, textColor=colors.grey, alignment=1))],
            [Paragraph(f"<font size=24 color='{gauge_color}'><b>{prob:.1f}%</b></font>", ParagraphStyle('Value', alignment=1, leading=30)),
             Paragraph(f"<font size=18 color='{gauge_color}'><b>{pred['risk_level'] if pred else 'N/A'}</b></font>", ParagraphStyle('Value', alignment=1, leading=30))]
        ]
        insight_table = Table(insight_data, colWidths=[3.5*inch, 3.5*inch])
        insight_table.setStyle(TableStyle([
            ('ALIGN', (0,0), (-1,-1), 'CENTER'),
            ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
            ('GRID', (0,0), (-1,-1), 0.5, colors.HexColor("#e2e8f0")),
            ('BOTTOMPADDING', (0,0), (-1,0), 0),
            ('TOPPADDING', (0,1), (-1,1), 0),
            ('BOTTOMPADDING', (0,1), (-1,1), 15),
            ('TOPPADDING', (0,0), (-1,0), 15),
        ]))
        elements.append(insight_table)
        elements.append(Spacer(1, 0.2*inch))
        
        # --- NEW: BEHAVIORAL IMPACT ANALYSIS ---
        elements.append(Paragraph("BEHAVIORAL IMPACT ANALYSIS", ParagraphStyle('Section', fontSize=10, textColor=colors.HexColor("#38bdf8"), spaceBefore=10, spaceAfter=8)))
        
        study_impact = "High" if student['study_hours'] > 15 else ("Moderate" if student['study_hours'] > 8 else "Low")
        abs_impact = "Significant" if student['absences'] > 5 else "Minimal"
        
        impact_data = [
            [Paragraph("<b>Factor</b>", styles['Normal']), Paragraph("<b>Observed Value</b>", styles['Normal']), Paragraph("<b>Impact on Success</b>", styles['Normal'])],
            ["Weekly Study Hours", f"{student['study_hours']} hrs", study_impact],
            ["Total Absences", f"{student['absences']} days", abs_impact],
            ["Family Support", f"{student['family_support']}/5", "Positive" if student['family_support'] > 3 else "Neutral"]
        ]
        impact_table = Table(impact_data, colWidths=[2.3*inch, 2.3*inch, 2.4*inch])
        impact_table.setStyle(TableStyle([
            ('BACKGROUND', (0,0), (-1,0), colors.HexColor("#f1f5f9")),
            ('GRID', (0,0), (-1,-1), 0.5, colors.HexColor("#e2e8f0")),
            ('PADDING', (0,0), (-1,-1), 8),
            ('FONTSIZE', (0,0), (-1,-1), 9),
        ]))
        elements.append(impact_table)
        elements.append(Spacer(1, 0.3*inch))

        # --- NEW: COMPARATIVE ANALYTICS ---
        elements.append(Paragraph("COMPARATIVE PERFORMANCE ANALYSIS", ParagraphStyle('Section', fontSize=12, textColor=colors.HexColor("#38bdf8"), spaceAfter=10)))
        
        # Calculate Class Averages
        class_stats = conn.execute('''
            SELECT AVG(g.midterm*0.3 + g.final*0.5 + g.homework*0.2) as class_avg
            FROM StudentClasses sc
            JOIN Grades g ON g.class_id = sc.class_id
            WHERE sc.class_id IN (SELECT class_id FROM StudentClasses WHERE student_id = ?)
        ''', (target_id,)).fetchone()
        
        class_avg = class_stats['class_avg'] or 0
        student_avg = conn.execute('SELECT AVG(midterm*0.3 + final*0.5 + homework*0.2) FROM Grades WHERE student_id = ?', (target_id,)).fetchone()[0] or 0
        
        diff = student_avg - class_avg
        standing = "Above Average" if diff > 5 else ("Below Average" if diff < -5 else "On Par with Class")
        
        comp_data = [
            [Paragraph("<b>Comparison Metric</b>", styles['Normal']), Paragraph("<b>Student</b>", styles['Normal']), Paragraph("<b>Class Average</b>", styles['Normal']), Paragraph("<b>Variance</b>", styles['Normal'])],
            ["Weighted Performance", f"{student_avg:.1f}%", f"{class_avg:.1f}%", f"{'+' if diff > 0 else ''}{diff:.1f}%"],
            ["Academic Standing", standing, "-", "-"]
        ]
        comp_table = Table(comp_data, colWidths=[2.5*inch, 1.5*inch, 1.5*inch, 1.5*inch])
        comp_table.setStyle(TableStyle([
            ('GRID', (0,0), (-1,-1), 0.5, colors.HexColor("#e2e8f0")),
            ('PADDING', (0,0), (-1,-1), 10),
            ('BACKGROUND', (0,0), (-1,0), colors.HexColor("#f8fafc")),
            ('FONTSIZE', (0,0), (-1,-1), 9),
        ]))
        elements.append(comp_table)
        elements.append(Spacer(1, 0.4*inch))
        
        # Detailed Grades
        elements.append(Paragraph("DETAILED ACADEMIC BREAKDOWN", ParagraphStyle('Section', fontSize=12, textColor=colors.HexColor("#38bdf8"), spaceAfter=10)))
        grades = conn.execute('SELECT g.*, c.class_name FROM Grades g JOIN Classes c ON g.class_id = c.id WHERE g.student_id = ?', (target_id,)).fetchall()
        
        grade_data = [['SUBJECT / CLASS', 'MIDTERM', 'FINAL', 'HOMEWORK', 'OVERALL']]
        for g in grades:
            overall = (g['midterm']*0.3 + g['final']*0.5 + g['homework']*0.2)
            grade_data.append([g['class_name'], f"{g['midterm']}%", f"{g['final']}%", f"{g['homework']}%", f"{overall:.1f}%"])
        
        grade_table = Table(grade_data, colWidths=[3*inch, 1*inch, 1*inch, 1*inch, 1*inch])
        grade_table.setStyle(TableStyle([
            ('BACKGROUND', (0,0), (-1,0), colors.HexColor("#0f172a")),
            ('TEXTCOLOR', (0,0), (-1,0), colors.whitesmoke),
            ('ALIGN', (0,0), (-1,-1), 'CENTER'),
            ('FONTNAME', (0,0), (-1,0), 'Helvetica-Bold'),
            ('FONTSIZE', (0,0), (-1,0), 10),
            ('BOTTOMPADDING', (0,0), (-1,0), 12),
            ('BACKGROUND', (0,1), (-1,-1), colors.white),
            ('GRID', (0,0), (-1,-1), 0.5, colors.HexColor("#e2e8f0")),
            ('ROWBACKGROUNDS', (0,1), (-1,-1), [colors.white, colors.HexColor("#f8fafc")]),
        ]))
        elements.append(grade_table)
        elements.append(Spacer(1, 0.3*inch))

        # --- NEW: STRATEGIC GROWTH ROADMAP ---
        if pred and pred['recommendation']:
            roadmap_elements = []
            roadmap_elements.append(Paragraph("STRATEGIC GROWTH ROADMAP", ParagraphStyle('Section', fontSize=12, textColor=colors.HexColor("#38bdf8"), spaceAfter=5)))
            roadmap_elements.append(Spacer(1, 0.1*inch))
            
            rec_text = Paragraph(f"<b>Personalized Recommendation:</b> {pred['recommendation']}", ParagraphStyle('Rec', fontSize=10, leading=14))
            rec_table = Table([[rec_text]], colWidths=[7*inch])
            rec_table.setStyle(TableStyle([
                ('BACKGROUND', (0,0), (-1,-1), colors.HexColor("#f0f9ff")),
                ('BOX', (0,0), (-1,-1), 0.5, colors.HexColor("#e0f2fe")),
                ('TOPPADDING', (0,0), (-1,-1), 12),
                ('BOTTOMPADDING', (0,0), (-1,-1), 12),
                ('LEFTPADDING', (0,0), (-1,-1), 12),
                ('RIGHTPADDING', (0,0), (-1,-1), 12),
            ]))
            roadmap_elements.append(rec_table)
            
            # Action items simulation
            actions = "• Increase focus on midterm preparation.\n• Reduce absences to improve overall consistency.\n• Leverage family support for dedicated study blocks."
            roadmap_elements.append(Spacer(1, 0.15*inch))
            roadmap_elements.append(Paragraph(actions.replace('\n', '<br/>'), ParagraphStyle('Actions', fontSize=9, textColor=colors.HexColor("#64748b"), leftIndent=20, leading=14)))
            
            elements.append(KeepTogether(roadmap_elements))

    doc.build(elements)
    conn.close()
    return filename
