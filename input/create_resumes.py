"""
Run this script once to generate the two sample resume PDFs in the input/ folder.
    python create_resumes.py
Requires: pip install reportlab
"""
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
from reportlab.lib.units import cm
from reportlab.lib.enums import TA_CENTER
import os

OUTPUT_DIR = os.path.dirname(os.path.abspath(__file__))


def build_resume(filename: str, lines: list[tuple[str, str]]):
    """lines = list of (style_name, text)"""
    path = os.path.join(OUTPUT_DIR, filename)
    doc = SimpleDocTemplate(path, pagesize=A4,
                            leftMargin=2*cm, rightMargin=2*cm,
                            topMargin=2*cm, bottomMargin=2*cm)
    styles = getSampleStyleSheet()
    styles.add(ParagraphStyle(name="CenterBold",
                               parent=styles["Heading1"],
                               alignment=TA_CENTER,
                               fontSize=16))
    styles.add(ParagraphStyle(name="SectionHead",
                               parent=styles["Heading2"],
                               fontSize=12,
                               spaceAfter=4))
    styles.add(ParagraphStyle(name="Body",
                               parent=styles["Normal"],
                               fontSize=10,
                               spaceAfter=2))

    story = []
    for style_name, text in lines:
        story.append(Paragraph(text, styles[style_name]))
        if style_name == "CenterBold":
            story.append(Spacer(1, 0.3*cm))
    doc.build(story)
    print(f"Created: {path}")


# ── Rahul Kumar resume ────────────────────────────────────────────────────
build_resume("Rahul_Resume.pdf", [
    ("CenterBold",   "Rahul Kumar"),
    ("Body",         "Email: rahul@gmail.com"),
    ("Body",         "Phone: 9012345678"),
    ("Body",         "LinkedIn: https://linkedin.com/in/rahulkumar"),
    ("Body",         "GitHub: https://github.com/rahulkumar-dev"),
    ("SectionHead",  "Professional Summary"),
    ("Body",         "Software Engineer with 2 years of experience in Java backend development "
                     "using Spring Boot and REST APIs."),
    ("SectionHead",  "Skills"),
    ("Body",         "JAVA, Spring Boot, REST APIs, SQL, Git, Docker"),
    ("SectionHead",  "Experience"),
    ("Body",         "Software Engineer, TCS (June 2023 - Present)"),
    ("Body",         "Developed scalable microservices using Java, Spring Boot, Kafka and Redis."),
    ("SectionHead",  "Education"),
    ("Body",         "B.Tech in Computer Science, JNTUH, 2023"),
    ("SectionHead",  "Projects"),
    ("Body",         "Employee Management System"),
    ("Body",         "Online Banking Application"),
])

# ── Deepika Rajmanoharan resume ───────────────────────────────────────────
build_resume("Deepika_Resume.pdf", [
    ("CenterBold",   "Deepika Rajmanoharan"),
    ("Body",         "Email: deepikarajmanoharan@gmail.com"),
    ("Body",         "LinkedIn: https://www.linkedin.com/in/deepikarajmanoharan/"),
    ("Body",         "GitHub: https://github.com/Deepika4825"),
    ("SectionHead",  "Professional Summary"),
    ("Body",         "Software Engineer with 3 years of experience in Python, "
                     "Machine Learning and Data Analysis."),
    ("SectionHead",  "Skills"),
    ("Body",         "Python, Machine Learning, Data Analysis, SQL, Pandas, NumPy, Power BI"),
    ("SectionHead",  "Experience"),
    ("Body",         "Software Engineer, Infosys (July 2021 - Present)"),
    ("Body",         "Built data pipelines and ML models for client analytics platforms."),
    ("SectionHead",  "Education"),
    ("Body",         "B.Tech in Information Technology, Anna University, 2021"),
    ("SectionHead",  "Projects"),
    ("Body",         "Customer Churn Prediction Model"),
    ("Body",         "Sales Forecasting Dashboard"),
])

print("Done.")
