# EduManage AI 🎓

**EduManage AI** is a premium, AI-powered academic performance management platform designed for modern educational institutions. It leverages Machine Learning to predict student success, identify academic risks, and provide data-driven recommendations in real-time.

![License](https://img.shields.io/badge/license-MIT-blue.svg)
![Python](https://img.shields.io/badge/python-3.13-blue.svg)
![Flask](https://img.shields.io/badge/Web-Flask-green.svg)
![Scikit-Learn](https://img.shields.io/badge/AI-Scikit--Learn-orange.svg)

---

## ✨ Key Features

### 🏢 Web Portal (Admin, Teacher, Student)
- **Role-Based Access**: Specialized interfaces for Administrators, Teachers, and Students.
- **Dynamic Dashboards**: Real-time stats, AI risk badges, and performance charts.
- **Real-time AI Sync**: Predictive models automatically update whenever a teacher modifies student grades (Midterm, Final, Homework).

### 👨‍🏫 Teacher Intelligence
- **AI Improvement Simulator**: Simulate how changes in student habits (study hours, attendance) affect their success probability.
- **Academic Reporting**: Generate detailed individual performance reports with AI success forecasts and grade breakdowns.
- **Grade Management**: Direct synchronization between academic entry and AI prediction outcomes.

### 🎓 Student Analytics
- **Personalized AI Insights**: Smart recommendations based on individual performance trends.
- **Success Forecasts**: Visual gauges showing the probability of academic success based on current trajectory.
- **My Grades**: Comprehensive view of academic progress across all enrolled classes.

### 📄 Intelligent Reporting
- **PDF Export**: Generate professional, printable performance reports featuring AI analysis, demographic data, and detailed grade histories.

---

## 🛠️ Technology Stack

- **Backend**: Python 3.13 / Flask (Web Server)
- **UI Framework**: PyQt6 (Desktop) / Vanilla CSS & Jinja2 (Web)
- **Database**: SQLite (Relational data storage)
- **Machine Learning**: Scikit-learn (Random Forest Regressor)
- **Visualization**: Chart.js (Web) / Matplotlib (Desktop)
- **Reporting**: ReportLab (Professional PDF Generation)

---

## 🚀 Installation & Setup

1. **Clone the Repository**
   ```bash
   git clone https://github.com/yourusername/EduManage-AI.git
   cd EduManage-AI
   ```

2. **Install Dependencies**
   ```bash
   pip install flask flask-sqlalchemy scikit-learn pandas numpy matplotlib reportlab PyQt6
   ```

3. **Run the Web Portal (Recommended)**
   ```bash
   python app.py
   ```
   *Access at: http://127.0.0.1:8888*

4. **Run the Desktop Version**
   ```bash
   python main.py
   ```

---

## 🔐 Access Credentials

| Role | Username (Email) | Password |
| :--- | :--- | :--- |
| **Administrator** | `admin@edumanage.com` | `admin123` |
| **Teacher** | `john@teacher.com` | `pass123` |
| **Student** | `alice@student.com` | `stud123` |

---

## 📂 Project Structure

```text
EduManageAI/
├── app.py               # Flask Web Entry Point
├── main.py              # Desktop Entry Point (PyQt6)
├── database.py          # SQLite Schema & DB Logic
├── ai_model.py          # AI Prediction Engine
├── reports_generator.py # PDF Generation Logic
├── recommender.py       # AI Recommendation Engine
├── templates/           # HTML Templates (Jinja2)
├── static/              # CSS, JS, and Uploaded Media
├── ui/                  # Desktop UI Components
└── data/                # Database & Model Storage
```

---

## 📝 License

This project is licensed under the MIT License.

---

*Developed for Advanced Academic Analytics.*
