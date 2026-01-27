from fpdf import FPDF
import os

# Create a folder for them
if not os.path.exists("test_resumes"):
    os.makedirs("test_resumes")

class PDF(FPDF):
    def header(self):
        self.set_font('Arial', 'B', 16)
        self.cell(0, 10, 'Curriculum Vitae', 0, 1, 'C')
        self.ln(5)

def create_resume(filename, name, email, summary, skills, experience):
    pdf = PDF()
    pdf.add_page()
    
    # Name & Contact
    pdf.set_font("Arial", "B", 14)
    pdf.cell(0, 10, name, 0, 1)
    pdf.set_font("Arial", "", 10)
    pdf.cell(0, 5, f"Email: {email}", 0, 1)
    pdf.ln(5)
    
    # Summary
    pdf.set_font("Arial", "B", 12)
    pdf.cell(0, 10, "Professional Summary", 0, 1)
    pdf.set_font("Arial", "", 11)
    pdf.multi_cell(0, 5, summary)
    pdf.ln(5)
    
    # Skills
    pdf.set_font("Arial", "B", 12)
    pdf.cell(0, 10, "Key Skills", 0, 1)
    pdf.set_font("Arial", "", 11)
    pdf.multi_cell(0, 5, skills)
    pdf.ln(5)
    
    # Experience
    pdf.set_font("Arial", "B", 12)
    pdf.cell(0, 10, "Experience", 0, 1)
    pdf.set_font("Arial", "", 11)
    pdf.multi_cell(0, 5, experience)
    
    pdf.output(f"test_resumes/{filename}")
    print(f"Generated: {filename}")

# --- THE CANDIDATES ---

candidates = [
    {
        "filename": "1_Perfect_Match_Alice.pdf",
        "name": "Alice Peterson",
        "email": "alice.p@example.com",
        "summary": "Results-driven Digital Marketing Manager with 6 years of experience in B2B SaaS. Expert in lead generation, SEO, and content strategy. Proven track record of increasing ARR by 20% through targeted LinkedIn campaigns.",
        "skills": "SEO, SEM, Google Analytics, LinkedIn Ads, HubSpot, Copywriting, B2B Marketing, Python Basics.",
        "experience": "Marketing Manager @ CloudSoft (2020-Present): Managed $50k/mo ad budget. Led a team of 3. Implemented HubSpot automation.\n\nSEO Specialist @ WebTech (2017-2020): Increased organic traffic by 150%."
    },
    {
        "filename": "2_Perfect_Match_Bob.pdf",
        "name": "Bob Chen",
        "email": "bob.c@example.com",
        "summary": "Creative Growth Marketer specializing in tech startups. I build funnels that convert. Expert in copywriting and email automation sequences.",
        "skills": "Copywriting, Email Marketing, Google Ads, SEO, A/B Testing, Zapier, ClickFunnels.",
        "experience": "Growth Lead @ StartupX (2021-Present): Built the marketing engine from scratch. Scaled user base to 10k.\n\nContent Marketer @ TechDaily (2019-2021): Wrote viral blog posts and managed newsletter."
    },
    {
        "filename": "3_Strong_Match_Carol.pdf",
        "name": "Carol Davis",
        "email": "carol.d@example.com",
        "summary": "Data-driven marketer with a focus on analytics and performance marketing. I love using data to optimize ROI.",
        "skills": "Google Analytics 4, Tableau, SQL, Facebook Ads, Google Tag Manager, Excel.",
        "experience": "Performance Marketer @ BigData Corp (2019-Present): Optimized CPA by 30%. Managed cross-channel reporting."
    },
    {
        "filename": "4_Medium_Match_David_Retail.pdf",
        "name": "David Miller",
        "email": "david.m@example.com",
        "summary": "Marketing Manager with 10 years of experience in the Fashion and Retail industry. Expert in brand awareness and influencer marketing.",
        "skills": "Brand Strategy, Influencer Management, Social Media (Instagram/TikTok), Event Planning.",
        "experience": "Brand Manager @ FashionNova (2018-Present): Managed influencer campaigns with 1M+ reach.\n\nMarketing Coord @ RetailStore (2015-2018): Organized in-store events."
    },
    {
        "filename": "5_Medium_Match_Eve_Social.pdf",
        "name": "Eve Wilson",
        "email": "eve.w@example.com",
        "summary": "Social Media Ninja. I create viral content for TikTok and Instagram. Passionate about community building.",
        "skills": "TikTok, Instagram Reels, Community Management, Canva, Video Editing.",
        "experience": "Social Media Manager @ CoolBrand (2022-Present): Grew TikTok to 500k followers."
    },
    {
        "filename": "6_Junior_Frank.pdf",
        "name": "Frank Thomas",
        "email": "frank.t@example.com",
        "summary": "Recent Marketing Graduate eager to learn. Interned at a local agency.",
        "skills": "Basic SEO, Microsoft Office, Facebook Basics, Fast Learner.",
        "experience": "Marketing Intern @ Local Agency (2023): Assisted with social media scheduling."
    },
    {
        "filename": "7_Pivot_Grace_Sales.pdf",
        "name": "Grace Lee",
        "email": "grace.l@example.com",
        "summary": "Experienced Sales Representative looking to switch into Marketing. I know what customers want.",
        "skills": "Cold Calling, CRM (Salesforce), Negotiation, Public Speaking.",
        "experience": "Sales Rep @ TechSales (2018-Present): Top performer 3 years in a row. Closed $1M in deals."
    },
    {
        "filename": "8_Bad_Match_Harry_Chef.pdf",
        "name": "Harry Cook",
        "email": "harry.c@example.com",
        "summary": "Head Chef with 15 years of culinary experience. Looking for a career change.",
        "skills": "Menu Planning, Kitchen Management, Food Safety, Inventory Control.",
        "experience": "Head Chef @ The Grand Hotel (2010-Present): Managed kitchen staff of 20."
    },
    {
        "filename": "9_Technical_Ivan_Dev.pdf",
        "name": "Ivan Dev",
        "email": "ivan.d@example.com",
        "summary": "Python Developer interested in marketing automation tools.",
        "skills": "Python, Django, React, AWS, Docker.",
        "experience": "Backend Dev @ SoftwareHouse (2019-Present): Built APIs and database structures."
    },
    {
        "filename": "10_Keyword_Spam_Jack.pdf",
        "name": "Jack Spammer",
        "email": "jack.s@example.com",
        "summary": "Marketing Marketing SEO SEO SEO Sales Growth.",
        "skills": "SEO, Marketing, Growth, Sales, B2B, SaaS, Ads, Google.",
        "experience": "Self Employed (2020-Present): Did marketing stuff."
    }
]

# Generate them
for c in candidates:
    create_resume(c['filename'], c['name'], c['email'], c['summary'], c['skills'], c['experience'])

print("\nDone! Check the 'test_resumes' folder.")