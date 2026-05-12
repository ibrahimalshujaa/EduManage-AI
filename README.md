# EduManage AI 🎓
### *Next-Generation Academic Intelligence & Management System*

**EduManage AI** is a premium, AI-driven academic performance management platform designed to empower educational institutions with data-backed insights. By leveraging advanced Machine Learning algorithms, it predicts student success, identifies academic risks in real-time, and provides personalized recommendations to optimize learning outcomes.

![License](https://img.shields.io/badge/license-MIT-blue.svg?style=for-the-badge)
![Python](https://img.shields.io/badge/python-3.13-blue.svg?style=for-the-badge&logo=python)
![Flask](https://img.shields.io/badge/Web-Flask-green.svg?style=for-the-badge&logo=flask)
![Scikit-Learn](https://img.shields.io/badge/AI-Scikit--Learn-orange.svg?style=for-the-badge&logo=scikit-learn)
![SQLite](https://img.shields.io/badge/Database-SQLite-lightgrey.svg?style=for-the-badge&logo=sqlite)

---

## 🌟 Vision
To bridge the gap between traditional academic management and modern data science, providing teachers and administrators with the tools to intervene early and ensure every student reaches their full potential.

---

## ✨ Core Features

### 🏛️ Administrator Command Center
- **Institutional Overview**: Real-time monitoring of school-wide success probabilities and risk distributions.
- **User Management**: Unified interface to manage Students, Teachers, and Staff with role-based access control (RBAC).
- **Curriculum Control**: Easily create classes, assign subjects, and link teachers to specific academic groups.
- **Global Reporting**: Generate comprehensive institutional performance reports with a single click.

### 👨‍🏫 Teacher Intelligence Suite
- **AI Performance Simulator**: Test "what-if" scenarios—adjust study hours or attendance to see predicted impacts on student success.
- **Dynamic Grade Management**: Instant synchronization between grade entry and AI success forecasts.
- **Automated Alerts**: Visual risk badges (High, Medium, Low) for immediate identification of struggling students.
- **Resource Hub**: Upload lesson materials, share notes, and link external quizzes (Google Forms, Microsoft Forms) directly to subjects.

### 🎓 Student Success Portal
- **Academic Dashboard**: Visualized progress tracking with interactive charts (Chart.js).
- **AI Success Forecasts**: Real-time gauges showing the probability of passing based on current trajectories.
- **Smart Recommendations**: Personalized, AI-generated study advice tailored to individual performance trends.
- **Unified Gradebook**: Transparent access to all midterm, final, and homework grades across enrolled courses.

### 📊 Advanced Analytics & Reporting
- **Predictive Modeling**: Powered by Random Forest Regressor for high-accuracy academic forecasting.
- **Multilingual Support**: Fully localized in **English** and **Turkish**.
- **Professional PDF Export**: Generate printable academic transcripts and AI analysis reports for parents or administrative records.

---

## 🛠️ Technology Stack

| Layer | Technology |
| :--- | :--- |
| **Backend** | Python 3.13 / Flask (High-performance Web Server) |
| **Frontend** | Vanilla CSS3, Jinja2 Templates, HTML5 |
| **Intelligence** | Scikit-learn (Random Forest), NumPy, Pandas |
| **Visualization** | Chart.js (Web), Matplotlib (Analytics) |
| **Database** | SQLite (Reliable relational storage) |
| **PDF Engine** | ReportLab (Professional-grade PDF generation) |
| **Localization** | Custom i18n Translation Engine |

---

## 🚀 Installation & Getting Started

### Prerequisites
- Python 3.13+
- pip (Python package manager)

### 1. Clone & Prepare
```bash
git clone https://github.com/yourusername/EduManage-AI.git
cd EduManage-AI
```

### 2. Set Up Virtual Environment (Recommended)
```bash
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
```

### 3. Install Dependencies
```bash
pip install -r requirements.txt
# If requirements.txt is not present:
# pip install flask flask-sqlalchemy scikit-learn pandas numpy matplotlib reportlab PyQt6
```

### 4. Initialize Database & AI Model
```bash
python seed_db.py
python ai_model.py
```

### 5. Launch the Application
```bash
python app.py
```
*Access the portal at:* `http://127.0.0.1:8888`

---

## 🔐 Default Access Credentials

| Identity | Username (Email) | Password |
| :--- | :--- | :--- |
| **Administrator** | `admin@edumanage.com` | `admin123` |
| **Teacher** | `john@teacher.com` | `pass123` |
| **Student** | `alice@student.com` | `stud123` |

---

## 📂 Project Architecture

```text
EduManageAI/
├── app.py               # Flask Core Application (Web Entry)
├── ai_model.py          # Machine Learning Pipeline (Random Forest)
├── database.py          # SQLAlchemy/SQLite Database Logic
├── translations.py      # Multilingual Translation Engine
├── reports_generator.py # PDF Logic & Report Formatting
├── recommender.py       # AI-Driven Recommendation Logic
├── static/              # CSS, JS, Images, & Uploaded Materials
├── templates/           # Jinja2 HTML Layouts
├── data/                # Persistent Storage (DB & Trained Models)
├── ui/                  # Desktop Application Components
└── main.py              # PyQt6 Desktop Entry Point
```

---

## 🤝 Contributing
We welcome contributions from the community!
1. Fork the Project.
2. Create your Feature Branch (`git checkout -b feature/AmazingFeature`).
3. Commit your Changes (`git commit -m 'Add some AmazingFeature'`).
4. Push to the Branch (`git push origin feature/AmazingFeature`).
5. Open a Pull Request.

---

## 📝 License
Distributed under the **MIT License**. See `LICENSE` for more information.

---

*Developed for Advanced Academic Analytics & Institutional Excellence.*

