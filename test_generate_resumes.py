import os
import random
from fpdf import FPDF
import warnings

# Suppress the deprecation warnings to clean up the terminal output
warnings.filterwarnings("ignore")

# --- SETUP OUTPUT FOLDER ---
output_dir = os.path.join(os.getcwd(), "test_resumes")
if not os.path.exists(output_dir):
    os.makedirs(output_dir)
    print(f"✅ Created folder: {output_dir}")

# ===========================
# 1. CANDIDATE DATA GENERATION
# ===========================
def get_perfect_match(i):
    return {
        "file_name": f"Candidate_Perfect_{i}",
        "name": f"ALEX JOHNSON {i}",
        "title": "TECHNICAL SALES MANAGER",
        "contact": f"alex.perfect.{i}@email.com\n+1 202 555 01{i:02d}\nChicago, IL",
        "education": "B.S. Mech Engineering\nUniv. of Illinois\n2012 - 2016",
        "skills": "Technical Sales Strategy\nCRM (Salesforce Expert)\nTeam Leadership\nB2B Negotiation",
        "summary": "Results-oriented Technical Sales Manager with 8+ years of experience driving revenue in the industrial sector.",
        "jobs": [
            {"role": "Senior Sales Manager", "company": "Global Tech", "date": "2020 - Present", 
             "desc": "- Led a 12-person sales team to achieve $35M annual revenue.\n- Implemented Salesforce across the division."},
            {"role": "Sales Engineer", "company": "Industrial Solutions", "date": "2016 - 2020", 
             "desc": "- Top performer nationwide in 2018.\n- Developed technical proposals."}
        ]
    }

def get_good_match(i):
    return {
        "file_name": f"Candidate_Good_{i}",
        "name": f"SAMANTHA LEE {i}",
        "title": "SALES REPRESENTATIVE",
        "contact": f"sam.good.{i}@email.com\n+1 202 555 02{i:02d}\nNew York, NY",
        "education": "B.A. Business Admin\nState College\n2015 - 2019",
        "skills": "B2B Sales\nLead Generation\nAccount Management\nHubSpot CRM",
        "summary": "Motivated Sales Professional with 5 years of experience in B2B software sales. Looking to transition into management.",
        "jobs": [
            {"role": "Senior Account Executive", "company": "Software Solutions", "date": "2019 - Present", 
             "desc": "- Managed a portfolio of 50+ mid-market accounts.\n- Exceeded personal sales quota for 3 consecutive years."}
        ]
    }

def get_bad_match(i):
    roles = [("CHEF", "Culinary"), ("DRIVER", "Logistics"), ("TEACHER", "Education")]
    role_name, industry = random.choice(roles)
    return {
        "file_name": f"Candidate_Mismatch_{i}",
        "name": f"CHRIS DAVIS {i}",
        "title": role_name,
        "contact": f"chris.mismatch.{i}@email.com\n+1 202 555 03{i:02d}\nLos Angeles, CA",
        "education": f"High School Diploma\nCity High\n2014",
        "skills": "Time Management\nTeamwork\nHardworking\nPunctuality",
        "summary": f"Dedicated and hardworking {role_name.lower()} with experience in fast-paced environments.",
        "jobs": [
            {"role": f"Lead {role_name.title()}", "company": "Local Services LLC", "date": "2015 - Present", 
             "desc": "- Responsible for daily operations.\n- Managed schedules and inventory."}
        ]
    }

candidates = []
for i in range(1, 6): candidates.append(get_perfect_match(i))
for i in range(1, 11): candidates.append(get_good_match(i))
for i in range(1, 11): candidates.append(get_bad_match(i))

# ===========================
# 2. PDF GENERATOR CLASS
# ===========================
class ComplexResumePDF(FPDF):
    def header(self):
        self.set_fill_color(32, 136, 194)
        self.rect(0, 0, 65, 297, 'F')

    def create_resume_content(self, data):
        self.add_page()
        
        # --- LEFT COLUMN ---
        self.set_text_color(255, 255, 255)
        self.set_left_margin(10)
        self.set_right_margin(150)
        
        self.set_y(65)
        self.set_font('Helvetica', 'B', 13)
        self.cell(0, 10, 'CONTACT', 0, 1, 'L')
        self.set_font('Helvetica', '', 9)
        self.multi_cell(50, 5, data['contact'])
        self.ln(8)

        self.set_font('Helvetica', 'B', 13)
        self.cell(0, 10, 'SKILLS', 0, 1, 'L')
        self.set_font('Helvetica', '', 9)
        # Using dash (-) instead of bullet point to fix error
        bulleted_skills = "\n".join([f"- {skill}" for skill in data['skills'].split('\n')])
        self.multi_cell(50, 5, bulleted_skills)

        # --- RIGHT COLUMN ---
        self.set_text_color(0, 0, 0)
        self.set_left_margin(75) 
        self.set_right_margin(10)
        self.set_y(25)

        self.set_font('Helvetica', 'B', 24)
        self.cell(0, 10, data['name'], 0, 1, 'L')
        self.set_text_color(100, 100, 100)
        self.set_font('Helvetica', 'B', 14)
        self.cell(0, 8, data['title'], 0, 1, 'L')
        self.set_text_color(0, 0, 0)

        self.ln(12)
        self.set_font('Helvetica', 'B', 14)
        self.set_text_color(32, 136, 194)
        self.cell(0, 8, 'SUMMARY', 0, 1, 'L')
        self.set_text_color(0, 0, 0)
        self.set_font('Helvetica', '', 10)
        self.multi_cell(0, 5, data['summary'])

        self.ln(10)
        self.set_font('Helvetica', 'B', 14)
        self.set_text_color(32, 136, 194)
        self.cell(0, 8, 'EXPERIENCE', 0, 1, 'L')
        self.set_text_color(0, 0, 0)

        for job in data['jobs']:
            self.set_font('Helvetica', 'B', 11)
            self.cell(90, 6, job['role'], 0, 0)
            self.set_font('Helvetica', 'I', 10)
            self.set_text_color(100, 100, 100)
            self.cell(0, 6, job['date'], 0, 1, 'R')
            
            self.set_text_color(0, 0, 0)
            self.set_font('Helvetica', 'B', 10)
            self.cell(0, 6, job['company'], 0, 1)
            
            self.set_font('Helvetica', '', 10)
            self.multi_cell(0, 5, job['desc'])
            self.ln(5)

# ===========================
# 3. EXECUTION
# ===========================
print(f"🚀 Starting generation...")
for i, data in enumerate(candidates):
    try:
        pdf = ComplexResumePDF()
        pdf.set_auto_page_break(auto=True, margin=15)
        pdf.create_resume_content(data)
        pdf.output(os.path.join(output_dir, f"{data['file_name']}.pdf"))
        print(f"[{i+1}/{len(candidates)}] ✅ Created: {data['file_name']}")
    except Exception as e:
        print(f"❌ Error: {e}")

print("\n🎉 DONE! Check 'test_resumes' folder.")