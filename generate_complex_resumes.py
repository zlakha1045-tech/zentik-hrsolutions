from fpdf import FPDF
import os
import random

# Ensure folder exists
if not os.path.exists("complex_resumes"):
    os.makedirs("complex_resumes")

class ComplexPDF(FPDF):
    def header_section(self, name, title, contact):
        self.set_font('Arial', 'B', 24)
        self.cell(0, 10, name, 0, 1, 'L')
        self.set_font('Arial', 'I', 14)
        self.set_text_color(0, 102, 204) # Blue color like image
        self.cell(0, 10, title, 0, 1, 'L')
        
        self.set_font('Arial', '', 9)
        self.set_text_color(0, 0, 0)
        self.cell(0, 5, contact, 0, 1, 'L')
        self.ln(5)
        self.line(10, self.get_y(), 200, self.get_y()) # Horizontal line
        self.ln(5)

    def column_layout(self, left_content, right_content):
        y_start = self.get_y()
        
        # --- LEFT COLUMN (Width 65) ---
        self.set_left_margin(10)
        self.set_right_margin(135) # Leave space for right col
        self.set_y(y_start)
        
        for section, text in left_content.items():
            self.set_font('Arial', 'B', 11)
            self.cell(0, 8, section.upper(), 0, 1)
            self.line(10, self.get_y(), 70, self.get_y()) # Tiny section line
            self.ln(2)
            self.set_font('Arial', '', 9)
            self.multi_cell(0, 4, text)
            self.ln(4)
            
        max_y_left = self.get_y()
        
        # --- RIGHT COLUMN (Width 115) ---
        self.set_left_margin(80) # Move to right side
        self.set_right_margin(10)
        self.set_y(y_start)
        
        for section, text in right_content.items():
            self.set_font('Arial', 'B', 11)
            self.cell(0, 8, section.upper(), 0, 1)
            self.line(80, self.get_y(), 200, self.get_y())
            self.ln(2)
            self.set_font('Arial', '', 9)
            self.multi_cell(0, 4, text)
            self.ln(4)
            
        # Reset margins
        self.set_left_margin(10)
        self.set_y(max(max_y_left, self.get_y()))

def generate_resume(filename, data):
    pdf = ComplexPDF()
    pdf.add_page()
    pdf.header_section(data['name'], data['title'], data['contact'])
    pdf.column_layout(data['left_col'], data['right_col'])
    pdf.output(f"complex_resumes/{filename}")
    print(f"Generated: {filename}")

# --- THE DATASET (10 Candidates) ---

candidates = [
    # 1. PERFECT FIT: Material Handling Expert
    {
        "file": "1_Star_Candidate_John.pdf",
        "name": "John Steal",
        "title": "Senior Technical Sales Manager",
        "contact": "Nairobi, Kenya | +254 700 123 456 | john.steal@materials.co.ke",
        "left": {
            "Summary": "Accomplished Sales Manager with 7 years in Material Handling. Expert in forklifts, warehousing solutions, and tender management. Proven track record of closing $2M+ deals.",
            "Education": "B.Sc. Mechanical Engineering\nUniversity of Nairobi (2015)\n\nDiploma in Sales & Marketing\nKIM (2017)",
            "Skills": "Forklifts, Cranes, Tender Preparation, SAP, Salesforce, Negotiation, Swahili, English",
            "Certifications": "Certified Sales Professional (CSP)"
        },
        "right": {
            "Experience": "Regional Sales Manager @ HeavyLift Ltd (2018-Present)\n- Managed key accounts for logistics firms.\n- Increased forklift sales by 40% YoY.\n- Prepared successful tender bids for government contracts.\n\nSales Engineer @ EquiTech (2015-2018)\n- Technical demos for warehousing clients.",
            "Strengths": "Strategic Planning, Client Relations, Technical Knowledge",
            "References": "Available upon request."
        }
    },
    # 2. PERFECT FIT: Logistics Sales
    {
        "file": "2_Star_Candidate_Sarah.pdf",
        "name": "Sarah Omondi",
        "title": "Business Development Manager - Logistics",
        "contact": "Mombasa, Kenya | sarah.o@logistics.com",
        "left": {
            "Summary": "Results-oriented manager specializing in supply chain equipment. 6 years experience selling heavy machinery and warehousing tech.",
            "Education": "B.Com Marketing\nKenyatta University (2016)",
            "Skills": "B2B Sales, CRM, Supply Chain, Tender Management, MS Office",
        },
        "right": {
            "Experience": "Sales Lead @ PortSide Solutions (2019-Present)\n- Lead a team of 5 sales reps.\n- Specialized in selling automated material handling systems.\n\nSales Exec @ WarehousePro (2016-2019)\n- Top performer 2017, 2018.",
            "Strengths": "Team Leadership, Closing Deals",
            "References": "Mr. Kamau, CEO PortSide"
        }
    },
    # 3. WEAK FIT: Software Sales (Wrong Industry)
    {
        "file": "3_Weak_Fit_Mike_SaaS.pdf",
        "name": "Mike Techie",
        "title": "SaaS Sales Director",
        "contact": "Remote | mike.t@cloud.com",
        "left": {
            "Summary": "Tech sales expert. I sell cloud software to startups. Great at negotiation but zero experience with hardware or machinery.",
            "Education": "B.Sc. Computer Science\nJKUAT (2018)",
            "Skills": "Python, AWS, Jira, Salesforce, Cold Calling",
        },
        "right": {
            "Experience": "Sales Director @ CloudSoft (2020-Present)\n- Sold $1M in software licenses.\n- Managed remote teams.\n\nDevOps Engineer (2018-2020)\n- Switched to sales.",
            "Strengths": "Software knowledge, Agile methodology",
            "References": "Reference available."
        }
    },
    # 4. IRRELEVANT: The "Liz Shelby" Clone (Student)
    {
        "file": "4_Irrelevant_Liz_Shelby.pdf",
        "name": "Liz Shelby",
        "title": "Computer Science Student",
        "contact": "Little Rock, AR | liz@github.com",
        "left": {
            "Summary": "Resourceful Software Intern with 2 years of experience in IT. Looking for an internship.",
            "Education": "Bachelor of Computer Science\nNortheastern University (2022)\nGPA: 4.0",
            "Skills": "Java, Python, HTML, CSS, Windows, AWS",
            "Volunteer": "Educator at EduTech"
        },
        "right": {
            "Experience": "Software Intern @ Salesforce (2021)\n- Contributed to web development.\n- Resolved 20 Jira tickets.\n\nIT Intern @ Microsoft (2020)\n- Tier 1 technical support.",
            "Strengths": "Curiosity, Critical Thinking",
            "References": "Sara Fenton, HR at Salesforce"
        }
    },
    # 5. WEAK FIT: Engineer (No Sales)
    {
        "file": "5_Tech_No_Sales_Brian.pdf",
        "name": "Brian Engineer",
        "title": "Mechanical Engineer",
        "contact": "Nakuru, Kenya | brian.eng@fixit.com",
        "left": {
            "Summary": "Highly skilled Mechanical Engineer with deep knowledge of hydraulics and forklifts. I can fix anything, but I have never sold a product in my life.",
            "Education": "B.Sc. Mechanical Engineering (2019)",
            "Skills": "AutoCAD, SolidWorks, Hydraulics, Maintenance",
        },
        "right": {
            "Experience": "Maintenance Lead @ FactoryCorp (2019-Present)\n- Responsible for repairing forklifts and conveyor belts.\n- Managed spare parts inventory.",
            "Strengths": "Problem Solving, Technical Maintenance",
            "References": "Factory Manager"
        }
    },
    # 6. PERFECT FIT: Competitor Hire
    {
        "file": "6_Star_Candidate_David.pdf",
        "name": "David Kimani",
        "title": "Key Account Manager",
        "contact": "Nairobi | david.k@competitor.com",
        "left": {
            "Summary": "Currently working for your biggest competitor selling Toyota Forklifts. I have the client list you want.",
            "Education": "Diploma in Engineering",
            "Skills": "Strategic Selling, Material Handling, Account Management",
        },
        "right": {
            "Experience": "Sales Manager @ TopForklifts (2015-Present)\n- Manage 50 active accounts.\n- Expert in equipment leasing contracts.",
            "Strengths": "Industry Network, Product Knowledge",
            "References": "Confidential"
        }
    },
    # 7. IRRELEVANT: Chef
    {
        "file": "7_Irrelevant_Gordon.pdf",
        "name": "Gordon Ramsey",
        "title": "Executive Chef",
        "contact": "London | gordon@kitchen.com",
        "left": {
            "Summary": "World class chef. I shout at people until the food is good.",
            "Education": "Culinary Arts Degree",
            "Skills": "Cooking, Knives, Yelling, Menu Planning",
        },
        "right": {
            "Experience": "Head Chef @ Hell's Kitchen (2000-Present)\n- Managed kitchen staff.\n- Created 3 Michelin star menus.",
            "Strengths": "Perfectionism, Taste",
            "References": "The Queen"
        }
    },
    # 8. MEDIUM FIT: Retail Manager
    {
        "file": "8_Medium_Retail_Jane.pdf",
        "name": "Jane Wanjiku",
        "title": "Store Manager",
        "contact": "Nairobi | jane.w@retail.com",
        "left": {
            "Summary": "Retail manager with 10 years experience running supermarkets. Good at managing people and inventory, looking to move into B2B.",
            "Education": "B.A. Business Admin",
            "Skills": "Inventory, Staff Scheduling, Customer Service",
        },
        "right": {
            "Experience": "Branch Manager @ Naivas (2015-Present)\n- Oversaw store operations.\n- Handled customer complaints.",
            "Strengths": "Operations, People Skills",
            "References": "Available"
        }
    },
    # 9. MEDIUM FIT: Junior Sales
    {
        "file": "9_Junior_Sales_Tom.pdf",
        "name": "Tom Junior",
        "title": "Sales Assistant",
        "contact": "Nairobi | tom.j@sales.com",
        "left": {
            "Summary": "Recent grad with 1 year experience selling solar panels. Eager to learn material handling.",
            "Education": "Diploma in Sales",
            "Skills": "Cold Calling, Email Marketing",
        },
        "right": {
            "Experience": "Sales Rep @ SolarPoa (2023)\n- Door to door sales of solar lights.",
            "Strengths": "Energy, Persuasion",
            "References": "Tutor"
        }
    },
    # 10. TECH FIT: Civil Engineer
    {
        "file": "10_Civil_Eng_Peter.pdf",
        "name": "Peter Build",
        "title": "Civil Engineer",
        "contact": "Kisumu | peter@build.com",
        "left": {
            "Summary": "Civil Engineer specializing in road construction. Know a lot about heavy machinery (bulldozers), but not forklifts specifically.",
            "Education": "B.Sc Civil Engineering",
            "Skills": "Project Management, Site Supervision",
        },
        "right": {
            "Experience": "Site Engineer @ RoadWorks (2020-Present)\n- Supervised road grading.",
            "Strengths": "Construction knowledge",
            "References": "Available"
        }
    }
]

# Run Generator
for c in candidates:
    data = {
        "name": c["name"],
        "title": c["title"],
        "contact": c["contact"],
        "left_col": c["left"],
        "right_col": c["right"]
    }
    generate_resume(c["file"], data)