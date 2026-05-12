def generate_recommendations(study_hours, absences, gpa, previous_score):
    recs = []
    
    if absences > 10:
        recs.append({
            "title": "Improve Attendance",
            "description": "Your high absence rate is significantly impacting your predicted success. Aim for 95%+ attendance.",
            "type": "warning"
        })
    
    if study_hours < 10:
        recs.append({
            "title": "Increase Study Time",
            "description": "Students with your profile see a 15% grade boost by increasing study time to 12+ hours per week.",
            "type": "info"
        })
        
    if gpa < 60:
        recs.append({
            "title": "Peer Tutoring",
            "description": "We recommend joining the peer tutoring program for Mathematics and Science to bridge current gaps.",
            "type": "action"
        })
        
    if previous_score < 50:
        recs.append({
            "title": "Foundational Review",
            "description": "Focus on reviewing last semester's core concepts to build a stronger foundation for current topics.",
            "type": "info"
        })

    if not recs:
        recs.append({
            "title": "Maintain Excellence",
            "description": "You are performing well. Keep up your current study habits and consider mentoring others.",
            "type": "success"
        })
        
    return recs
