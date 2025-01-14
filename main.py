import streamlit as st
import pandas as pd
from datetime import datetime
import uuid
import os
import plotly.express as px
import plotly.graph_objects as go

# Add this at the very top of your script
st.set_page_config(page_title="Skills Matrix", layout="wide")

# Constants
RESPONSES_FILE = "skills_matrix_responses.csv"

def load_responses():
    """Load responses from CSV file"""
    try:
        if os.path.exists(RESPONSES_FILE):
            return pd.read_csv(RESPONSES_FILE)
        return pd.DataFrame()
    except Exception as e:
        st.error(f"Error loading responses: {e}")
        return pd.DataFrame()

def save_response(response_data):
    """Save response to CSV file"""
    try:
        # Load existing responses
        responses_df = load_responses()
        
        # Add new response
        new_response = pd.DataFrame([response_data])
        updated_responses = pd.concat([responses_df, new_response], ignore_index=True)
        
        # Save back to CSV
        updated_responses.to_csv(RESPONSES_FILE, index=False)
        return True
    except Exception as e:
        st.error(f"Error saving response: {e}")
        return False

def check_password():
    """Returns `True` if the user had the correct password."""
    if "password_correct" not in st.session_state:
        st.session_state.password_correct = False

    def password_entered():
        """Checks whether a password entered by the user is correct."""
        if st.session_state["password"] == st.secrets["admin_password"]:
            st.session_state["password_correct"] = True
            st.session_state.password = ''
        else:
            st.session_state["password_correct"] = False

    if st.session_state.get("password_correct", False):
        return True

    st.text_input(
        "Password", 
        type="password", 
        on_change=password_entered, 
        key="password"
    )
    if "password_correct" in st.session_state:
        st.error("😕 Password incorrect")
    return False

def show_admin_page():
    """Shows the admin page with download functionality and advanced analytics"""
    st.header("Admin Dashboard")
    
    # Load responses from file
    responses_df = load_responses()
    
    if not responses_df.empty:
        # Top section with key metrics and download
        col1, col2, col3 = st.columns([1,1,2])
        with col1:
            st.metric("Total Submissions", len(responses_df))
        with col2:
            st.metric("Unique Participants", len(responses_df['Submitter Email'].unique()))
        with col3:
            # Download and refresh buttons side by side
            subcol1, subcol2 = st.columns(2)
            with subcol1:
                st.download_button(
                    "📥 Download All Responses",
                    responses_df.to_csv(index=False),
                    "skills_matrix_responses.csv",
                    "text/csv",
                    key='download-csv'
                )
            with subcol2:
                if st.button("🔄 Refresh Data"):
                    st.experimental_rerun()
        
        # Tabs for different analysis views
        tab1, tab2, tab3 = st.tabs(["Raw Data", "Skills Analysis", "Form Submission Trends"])
        
        # Tab 1: Raw Data
        with tab1:
            st.subheader("Raw Response Data")
            st.dataframe(responses_df)
            
        # Tab 2: Skills Analysis
        with tab2:
            skill_cols = [col for col in responses_df.columns if col not in ['Response ID', 'Timestamp', 'Submitter Email']]
            
            # Summary statistics table
            st.subheader("Summary Statistics")
            col1, col2 = st.columns(2)
            
            def get_expertise_counts(row):
                primary = sum(1 for x in row if x >= 8)
                secondary = sum(1 for x in row if 3 <= x < 8)
                limited = sum(1 for x in row if 1 <= x < 3)
                return pd.Series({'Primary': primary, 'Secondary': secondary, 'Limited': limited})
            
            expertise_dist = responses_df[skill_cols].apply(get_expertise_counts, axis=1)
            
            # Calculate expertise distribution and stats
            # [Previous expertise distribution code remains the same]
            
            # Average points visualization
            st.subheader("Average Points by Skill")
            avg_points = responses_df[skill_cols].mean().sort_values(ascending=False)
            
            fig = px.bar(
                x=avg_points.index,
                y=avg_points.values,
                color=avg_points.values,
                color_continuous_scale=[[0, '#FFE5B4'],
                                      [0.3, '#90EE90'],
                                      [0.8, '#4169E1']],
                title='Average Points by Skill'
            )
            fig.update_layout(showlegend=False, xaxis_tickangle=-45)
            st.plotly_chart(fig, use_container_width=True)
            
            # [Rest of the admin visualization code remains the same]
        
        # Tab 3: Form Submission Trends code remains the same
        
    else:
        st.info("No responses collected yet.")

def update_total_points():
    """Update the total points in session state"""
    total = 0
    for skill in st.session_state.skills.keys():
        input_key = f"input_{skill}"
        if input_key in st.session_state:
            total += st.session_state[input_key]
    st.session_state.total_points = total

def get_expertise_level(value):
    """Return expertise level emoji based on value"""
    if value >= 8:
        return "🔵 Primary"
    elif value >= 3:
        return "🟢 Secondary"
    elif value >= 1:
        return "🟡 Limited"
    return ""

def is_email_unique(email):
    """Check if email is unique in responses (except for test email)"""
    if email == "aavadhan@umich.edu":  # Allow multiple submissions for test email
        return True
    
    responses_df = load_responses()
    if not responses_df.empty:
        existing_emails = responses_df['Submitter Email'].tolist()
        return email not in existing_emails
    return True

def show_skills_form(submitter_email):
    """Display the skills matrix form"""
    MAX_TOTAL_POINTS = 90
    MAX_POINTS_PER_SKILL = 10
    
    # Visual progress indicator
    col1, col2 = st.columns([2, 1])
    with col1:
        progress = st.session_state.total_points / MAX_TOTAL_POINTS
        st.progress(progress)
    with col2:
        st.metric("Total Points Used", st.session_state.total_points, f"/{MAX_TOTAL_POINTS} available")
    
    if st.session_state.total_points > MAX_TOTAL_POINTS:
        st.error(f"⚠️ You have exceeded the maximum total points of {MAX_TOTAL_POINTS}. Please reduce your points before continuing.")
    
    st.markdown("---")
    
    # Create input fields for each skill
    skill_inputs = {}
    for skill in st.session_state.skills.keys():
        col1, col2, col3 = st.columns([3, 1, 1])
        
        with col1:
            st.markdown(f"**{skill}**")
        with col2:
            value = st.number_input(
                f"{skill} points",
                min_value=0,
                max_value=MAX_POINTS_PER_SKILL,
                value=st.session_state.skills[skill],
                key=f"input_{skill}",
                on_change=update_total_points
            )
            st.session_state.skills[skill] = value
            skill_inputs[skill] = value
        
        with col3:
            st.markdown(get_expertise_level(value))
    
    # Submit form
    with st.form("skills_matrix"):
        submitted = st.form_submit_button("Submit Skills Matrix")
        
        if submitted:
            if st.session_state.total_points > MAX_TOTAL_POINTS:
                st.error(f"Cannot submit: Total points ({st.session_state.total_points}) exceed maximum of {MAX_TOTAL_POINTS}. Please adjust your points allocation.")
                return  # Prevent form submission
            
            response_data = {
                'Response ID': str(uuid.uuid4())[:8],
                'Timestamp': datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                'Submitter Email': submitter_email,
                **st.session_state.skills
            }
            
            if save_response(response_data):
                st.success("Skills matrix submitted successfully!")
                st.balloons()
                
                # Reset form
                st.session_state.skills = {k: 0 for k in st.session_state.skills}
                st.session_state.total_points = 0
            else:
                st.error("There was an error saving your response. Please try again.")
def main():
    # Sidebar for navigation
    with st.sidebar:
        st.title("Navigation")
        page = st.radio("Go to", ["Caravel Skills Matrix", "Admin"])
    
    if page == "Admin":
        if not check_password():
            st.warning("Please enter the admin password to access this section.")
            return
        show_admin_page()
        return
    
    # Main form page
    st.title("Caravel Law Skills Matrix")
    
    # Introduction
    st.markdown("""
    Welcome to the Skills Matrix Survey! The purpose of this matrix is to help us gather insights into your strengths and areas 
    of expertise, ensuring we effectively leverage our team's collective knowledge. This information will play a critical role in:
    
    - Developing business development and marketing strategies
    - Identifying growth opportunities for the Firm
    - Uncovering untapped talents
    - Guiding our strategic initiatives
    
    Please note, some skills listed may be industry specific or with a specialization. If not applicable, you can leave blank or put 0.
    
    ### Points Allocation Overview
    You have **90 points** to allocate across **172 skills** listed in the matrix. These points represent your level of expertise 
    and experience in each area. The goal is to allocate your points in a way that best reflects your true areas of strength. 
    You'll need to make thoughtful choices about where your expertise lies, prioritizing key skills over areas of limited 
    experience to ensure we capture an honest reflection of your abilities.
    
    ### How to Complete the Matrix
    
    **1. Review the Skills**
    Carefully read through the skills listed in the matrix. Each skill represents a specific area of expertise relevant to our team's work.
    
    **2. Allocate Your Points**
    Distribute your 90 points across the skills based on your expertise. Remember, the objective is to highlight your primary 
    strengths while providing an honest reflection of your experience in other areas.
    
    **3. Consider Balance**
    While you are free to allocate up to 10 points for a single skill, keep in mind that spreading your points too thinly may 
    not fully represent your primary areas of expertise. Prioritize the skills where you are most confident and experienced.
    
    **4. Total Points**
    Ensure that the total number of points you allocate across all skills does not exceed **90 points**.
    
    ### Example Point Distribution
    - **Distribution and Supply Agreements:** 🔵 8 points (Primary area of expertise—highly experienced)
    - **Employment Agreements:** 🟢 4 points (Moderate experience)
    - **Technology Transfer Agreements:** 🟡 2 points (Limited experience)
    """)
    
    # Email input before showing the form
    submitter_email = st.text_input("Enter your email:")
    
    # Initialize session state after valid email
    if submitter_email:
        if not is_email_unique(submitter_email):
            st.error("This email has already submitted a response. Please use a different email address.")
            return
            
        if 'total_points' not in st.session_state:
            st.session_state.total_points = 0
        if 'skills' not in st.session_state:
            st.session_state.skills = {

    'Advertising and Labeling Regulations (Pharma/BioTech) (Skill 1)': 0,

    'Advertising and Marketing Regulations (Retail and Consumer) (Skill 2)': 0,

    'Advertising Technology (AdTech) (Skill 3)': 0,

    'Affiliate Marketing Agreements (Skill 4)': 0,

    'Amalgamations (Skill 5)': 0,

    'Artificial Intelligence Terms, Regulations & Compliance (Skill 6)': 0,

    'Associations (Skill 7)': 0,

    'Aquisitions (Skill 8)': 0,

    'Banking and Finance Transactions (Skill 9)': 0,

    'Banking Regulation and Compliance (Skill 10)': 0,

    'Bankrupcty and Insolvency (Debtor/Creditor) (Skill 11)': 0,

    'Biotech Agreements (Skill 12)': 0,

    'Blockchain Governance (Skill 13)': 0,

    'Board of Directors and Committees (Skill 14)': 0,

    'Canadian Anti-Spam Legislation (CASL) (Skill 15)': 0,

    'Children\'s Privacy (Skill 16)': 0,

    'Clinical Trials and Research (Skill 17)': 0,

    'Competition (Skill 18)': 0,

    'Commercial Real Estate Transactions (Skill 19)': 0,

    'Commercial Contracts (Skill 20)': 0,

    'Consumer Banking Regulations (Skill 21)': 0,

    'Consumer Protection (B2C) (Skill 22)': 0,

    'Construction (Skill 23)': 0,

    'Content Creation and Copyright (Skill 24)': 0,

    'Content Removal and Takedown (Skill 25)': 0,

    'Continuous Disclosure (Skill 26)': 0,

    'Collections (Skill 27)': 0,

    'Copyright and Fair Dealing (Skill 28)': 0,

    'Corporate Bylaws, Records and Governance (Skill 29)': 0,

    'Corporate Reorganization (Skill 30)': 0,

    'Corruption and Anti-Bribery (Skill 31)': 0,

    'Cross-Border Privacy Compliance (Skill 32)': 0,

    'Cross-Border Transactions (Skill 33)': 0,

    'Cryptocurrency Exchange (Digital Assets & Blockchain) (Skill 34)': 0,

    'Customs Regulations (Skill 35)': 0,

    'Cybersecurity and Data Protection (Regulatory Compliance) (Skill 36)': 0,

    'Cybersecurity/Data Breach Incident Response (Skill 37)': 0,

    'Data Collection, Sales and Compliance (Data Brokers) (Skill 38)': 0,

    'Debt & Equity Financing (Skill 39)': 0,

    'Deferred Compensation Plans (Skill 40)': 0,

    'Demand Response Agreements (Skill 41)': 0,

    'Derivatives and Commodities (Skill 42)': 0,

    'Digital Advertising Regulation (Skill 43)': 0,

    'Digital Media and Online Content (Skill 44)': 0,

    'Digital Payment Regulations (Skill 45)': 0,

    'Distribution and Supply Agreements (Skill 46)': 0,

    'Drug, Alcohol, Gaming Regulatory (Skill 47)': 0,

    'Due Diligence and Valuation (Skill 48)': 0,

    'eCommerce (Skill 49)': 0,

    'Employee Benefits Plans (Skill 50)': 0,

    'Employee side Employment Issues (Skill 51)': 0,

    'Employee Stock Purchase Plans (Skill 52)': 0,

    'Employee Training Programs (Skill 53)': 0,

    'Employer Side Employment Issues (Skill 54)': 0,

    'Employment Agreements (Skill 55)': 0,

    'Employment; Notice, Severance and Termination (Skill 56)': 0,

    'Employment; Workplace Discrimination and Human Rights (Skill 57)': 0,

    'Employment-based Immigration (Skill 58)': 0,

    'Energy Contracts and Agreements (Skill 59)': 0,

    'Energy - Solar (Skill 60)': 0,

    'Energy - Wind (Skill 61)': 0,

    'Energy - Hydro (Skill 62)': 0,

    'Energy - Nuclear (Skill 63)': 0,

    'Entertainment and Sponsorship Agreements (Skill 64)': 0,

    'Environmental Sustainability Compliance (Skill 65)': 0,

    'Equity Compensation or Incentive Plans (Skill 66)': 0,

    'Escrow Agreements (Skill 67)': 0,

    'Executive Compensation (Skill 68)': 0,

    'Export Control Regulations (Skill 69)': 0,

    'Dissolutions (Skill 70)': 0,

    'Drones (Skill 71)': 0,

    'Federal and Provincial Government Contracting (Prime and Subs) (Skill 72)': 0,

    'Financial Services Regulatory Requirements (Skill 73)': 0,

    'Financial Transactions and Structuring (Skill 74)': 0,

    'Fintech (Skill 75)': 0,

    'Fintrac (Skill 76)': 0,

    'Forced Labour and Slavery (Skill 77)': 0,

    'Formation and Entity Creation/Operating Agreements (Skill 78)': 0,

    'Founder Agreements (Skill 79)': 0,

    'Franchise Law - Franchisor (Skill 80)': 0,

    'Franchise Law - Franchisee (Skill 81)': 0,

    'Global/Cross-Border Employment Issues (Skill 82)': 0,

    'Health Canada Compliance, Regulations and Enforcement (Skill 83)': 0,

    'Healthcare Compliance and Regulations (Skill 84)': 0,

    'Higher Education Regulations (Skill 85)': 0,

    'Immigration - Business (Skill 86)': 0,

    'Immigration - Personal/Family (Skill 87)': 0,

    'Incorporations (Federal) (Skill 88)': 0,

    'Incorporations (Professional) (Skill 89)': 0,

    'Incorporations (Provincial) (Skill 90)': 0,

    'Independent Contractor Agreements (Skill 91)': 0,

    'Independent Schools (Skill 92)': 0,

    'Indigenous Rights and Relations (Skill 93)': 0,

    'Influencer Agreements (Skill 94)': 0,

    'Insurance Coverage Review (Skill 95)': 0,

    'Intellectual Property in M&A (Skill 96)': 0,

    'Intellectual Property Infringement (Skill 97)': 0,

    'Intellectual Property Licensing (Skill 98)': 0,

    'Intellectual Property Protection (Skill 99)': 0,

    'International Data Transfers (Skill 100)': 0,

    'International Trade and Import Export (Skill 101)': 0,

    'International/Foreign Government Contracts (Skill 102)': 0,

    'Initial Public Offering (IPO) (Skill 103)': 0,

    'Investment and Funding (Skill 104)': 0,

    'Investment Law and Regulations (Skill 105)': 0,

    'Investor Relations and Reporting (Skill 106)': 0,

    'Joint Ventures and Strategic Alliances (Skill 107)': 0,

    'Labour and Union (Skill 108)': 0,

    'Land Use and Zoning (Skill 109)': 0,

    'Leasing (Equipment) (Skill 110)': 0,

    'Leasing (Commercial Property) (Skill 111)': 0,

    'Lending (secured or unsecured) (Skill 112)': 0,

    'Life Sciences Licensing and Tech Transfer Agreements (Skill 113)': 0,

    'Litigation (Civil) (Skill 114)': 0,

    'Litigation (Employment) (Skill 115)': 0,

    'Litigation (Small Claims) (Skill 116)': 0,

    'Litigation Management (Skill 117)': 0,

    'Lobbying and PACs (Skill 118)': 0,

    'Loyalty Card Programs (Skill 119)': 0,

    'M&A (Skill 120)': 0,

    'Master Services Agreements (Skill 121)': 0,

    'Media Production Contracts (Skill 122)': 0,

    'Mediation (Skill 123)': 0,

    'Medical Device Licensing and Distribution (Skill 124)': 0,

    'Medical Device Regulations (Skill 125)': 0,

    'Mining (Skill 126)': 0,

    'Money Laundering and AML Regulations (Skill 127)': 0,

    'Municipality (Skill 128)': 0,

    'Natural Resource Management (Skill 129)': 0,

    'Non-Competition and Solicitation Agreements (Skill 130)': 0,

    'Non-Disclosure Agreements (Skill 131)': 0,

    'Non-Profit Law (Skill 132)': 0,

    'Occupational Health and Safety (Skill 133)': 0,

    'Oil and Gas Regulation (Skill 134)': 0,

    'Open Source Agreements (Skill 135)': 0,

    'Private Public Partnerships (P3) (Skill 136)': 0,

    'Patent Portfolio Management (Skill 137)': 0,

    'Prospectus (Skill 138)': 0,

    'Patent Prosecution (Skill 139)': 0,

    'Payment Systems and Digital Payments (Skill 140)': 0,

    'Pension Fund Management (Skill 141)': 0,

    'Pharmaceutical Licensing (Skill 142)': 0,

    'Policy Creation (Skill 143)': 0,

    'Power Purchase Agreements (Skill 144)': 0,

    'Privacy Compliance (Skill 145)': 0,

    'Private Company Corporate Governance (Skill 146)': 0,

    'Private Equity and Venture Capital (Skill 147)': 0,

    'Procurement (private) & RFPs (Skill 148)': 0,

    'Procurement (public) & RFPs (Skill 149)': 0,

    'Product Labeling and Packaging (Skill 150)': 0,

    'Product Warranties/Agreement Warranties (Skill 151)': 0,

    'Professional Services Agreements and related SOWs (Skill 152)': 0,

    'Public Company Corporate Governance (Skill 153)': 0,

    'Purchase and Sale Agreements (Skill 154)': 0,

    'Reorganizations (Skill 155)': 0,

    'Sanctions Law & Compliance (Skill 156)': 0,

    'Securities and Capital Markets (Skill 157)': 0,

    'Shareholder and Partnership Agreements (Skill 158)': 0,

    'Sports Law Agreements (Skill 159)': 0,

    'State/Local SLED Government Contracting (Skill 160)': 0,

    'Structured Finance and Securitization (Skill 161)': 0,

    'Sweepstakes and Contests (Skill 162)': 0,

    'Technology Licensing—Hardware (Skill 163)': 0,

    'Technology Licensing—Software/SaaS (Skill 164)': 0,

    'Terms of Service and User Agreements (Skill 165)': 0,

    'Trademark and Brand Protection/Prosecution (Skill 166)': 0,

    'Trademark Law/Portfolio Management (Skill 167)': 0,

    'Waste Management and Recycling (Skill 168)': 0

}
            show_skills_form(submitter_email)

if __name__ == "__main__":
    main()
