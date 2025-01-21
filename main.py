import streamlit as st
import pandas as pd
from datetime import datetime
import uuid
import os

# Add this at the very top of your script
st.set_page_config(page_title="Skills Matrix", layout="wide")

# Constants
RESPONSES_FILE = "skills_matrix_responses.csv"

def load_responses():
    """Load responses from CSV file"""
    try:
        if os.path.exists(RESPONSES_FILE):
            df = pd.read_csv(RESPONSES_FILE)
            # Ensure all required columns exist
            required_columns = ['Response ID', 'Timestamp', 'Submitter Name', 'Submitter Email']
            for col in required_columns:
                if col not in df.columns:
                    df[col] = ''
            return df
        # If file doesn't exist, create empty DataFrame with required columns
        return pd.DataFrame(columns=['Response ID', 'Timestamp', 'Submitter Name', 'Submitter Email'])
    except Exception as e:
        st.error(f"Error loading responses: {e}")
        return pd.DataFrame()
        
def save_response(response_data):
    """Save response to CSV file"""
    try:
        # Load existing responses
        responses_df = load_responses()
        
        # Make sure all columns exist in the DataFrame
        required_columns = ['Response ID', 'Timestamp', 'Submitter Name', 'Submitter Email']
        for col in required_columns:
            if col not in responses_df.columns:
                responses_df[col] = ''
        
        # Add new response
        new_response = pd.DataFrame([response_data])
        
        # Ensure columns are in the correct order
        if not responses_df.empty:
            # Get all columns from both DataFrames
            all_columns = responses_df.columns.union(new_response.columns)
            # Reindex both DataFrames with all columns
            responses_df = responses_df.reindex(columns=all_columns)
            new_response = new_response.reindex(columns=all_columns)
        
        updated_responses = pd.concat([responses_df, new_response], ignore_index=True)
        
        # Save back to CSV
        updated_responses.to_csv(RESPONSES_FILE, index=False)
        return True
    except Exception as e:
        st.error(f"Error saving response: {e}")
        return False

def check_password():
    """Returns `True` if the user had the correct password."""

    def password_entered():
        """Checks whether a password entered by the user is correct."""
        if st.session_state["password"] == st.secrets["admin_password"]:
            st.session_state["password_correct"] = True
            st.session_state.password = ''  # Clear the password field
        else:
            st.session_state["password_correct"] = False

    # Return True if the password is validated
    if st.session_state.get("password_correct", False):
        return True

    # Show input for password
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
    import plotly.express as px
    import plotly.graph_objects as go
    st.header("Admin Dashboard")
    
    # Load responses from file
    responses_df = load_responses()
    
    if not responses_df.empty:
        # Define metadata columns to exclude from skills analysis
        metadata_cols = ['Response ID', 'Timestamp', 'Submitter Email', 'Submitter Name']
        
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
            # Reorder columns to show metadata first
            metadata_cols = ['Response ID', 'Timestamp', 'Submitter Email', 'Submitter Name']
            other_cols = [col for col in responses_df.columns if col not in metadata_cols]
            ordered_cols = metadata_cols + other_cols
            st.dataframe(responses_df[ordered_cols])
            
        # Tab 2: Skills Analysis
        with tab2:
            # Calculate skill columns (excluding metadata columns)
            skill_cols = [col for col in responses_df.columns if col not in metadata_cols]
            
            # Summary statistics table
            st.subheader("Summary Statistics")
            col1, col2 = st.columns(2)
            
            # Calculate expertise distribution
            def get_expertise_counts(row):
                try:
                    primary = sum(1 for x in row if isinstance(x, (int, float)) and x >= 8)
                    secondary = sum(1 for x in row if isinstance(x, (int, float)) and 3 <= x < 8)
                    limited = sum(1 for x in row if isinstance(x, (int, float)) and 1 <= x < 3)
                    return pd.Series({'Primary': primary, 'Secondary': secondary, 'Limited': limited})
                except Exception as e:
                    print(f"Error processing row: {row}")
                    return pd.Series({'Primary': 0, 'Secondary': 0, 'Limited': 0})
            
            expertise_dist = responses_df[skill_cols].apply(get_expertise_counts, axis=1)
            
            with col1:
                st.markdown("**Average Skills per Person:**")
                avg_stats = pd.DataFrame({
                    'Expertise Level': ['Primary', 'Secondary', 'Limited'],
                    'Average Skills': [
                        f"{expertise_dist['Primary'].mean():.1f}",
                        f"{expertise_dist['Secondary'].mean():.1f}",
                        f"{expertise_dist['Limited'].mean():.1f}"
                    ],
                    'Color': ['🔵', '🟢', '🟡']
                })
                st.table(avg_stats)
            
            with col2:
                st.markdown("**Top Skills by Expertise Level:**")
                # Get top skills for each level
                top_skills = {}
                for skill in skill_cols:
                    primary_count = len(responses_df[responses_df[skill] >= 8])
                    secondary_count = len(responses_df[(responses_df[skill] >= 3) & (responses_df[skill] < 8)])
                    limited_count = len(responses_df[(responses_df[skill] > 0) & (responses_df[skill] < 3)])
                    
                    if primary_count > 0:
                        if 'Primary' not in top_skills or top_skills['Primary'][1] < primary_count:
                            top_skills['Primary'] = (skill, primary_count)
                    if secondary_count > 0:
                        if 'Secondary' not in top_skills or top_skills['Secondary'][1] < secondary_count:
                            top_skills['Secondary'] = (skill, secondary_count)
                    if limited_count > 0:
                        if 'Limited' not in top_skills or top_skills['Limited'][1] < limited_count:
                            top_skills['Limited'] = (skill, limited_count)
                
                top_skills_df = pd.DataFrame({
                    'Expertise Level': ['Primary 🔵', 'Secondary 🟢', 'Limited 🟡'],
                    'Most Common Skill': [
                        f"{top_skills.get('Primary', ('None', 0))[0]} ({top_skills.get('Primary', ('None', 0))[1]})",
                        f"{top_skills.get('Secondary', ('None', 0))[0]} ({top_skills.get('Secondary', ('None', 0))[1]})",
                        f"{top_skills.get('Limited', ('None', 0))[0]} ({top_skills.get('Limited', ('None', 0))[1]})"
                    ]
                })
                st.table(top_skills_df)

            # Average points visualization
            st.subheader("Average Points by Skill")
            avg_points = responses_df[skill_cols].mean().sort_values(ascending=False)
            
            # Create a bar chart for average points with color coding
            fig = px.bar(
                x=avg_points.index,
                y=avg_points.values,
                color=avg_points.values,
                color_continuous_scale=[[0, '#FFE5B4'],  # Light yellow for limited
                                      [0.3, '#90EE90'],  # Green for secondary
                                      [0.8, '#4169E1']], # Blue for primary
                title='Average Points by Skill'
            )
            fig.update_layout(showlegend=False, xaxis_tickangle=-45)
            st.plotly_chart(fig, use_container_width=True)
            
            # Show top skills with color coding
            st.subheader("Most Common Primary Expertise Areas")
            primary_expertise = pd.DataFrame()
            for skill in skill_cols:
                primary_count = len(responses_df[responses_df[skill] >= 8])
                if primary_count > 0:
                    primary_expertise.at[skill, 'Count'] = primary_count
            
            if not primary_expertise.empty:
                primary_expertise = primary_expertise.sort_values('Count', ascending=False)
                fig2 = px.bar(
                    x=primary_expertise.index,
                    y=primary_expertise['Count'],
                    color=primary_expertise['Count'],
                    color_continuous_scale=[[0, '#4169E1'], [1, '#4169E1']],  # Blue for primary expertise
                    title='Number of Primary Expertise Areas'
                )
                fig2.update_layout(showlegend=False, xaxis_tickangle=-45)
                st.plotly_chart(fig2, use_container_width=True)
        
        # Tab 3: Form Submission Trends
        with tab3:
            st.subheader("Submission Trends")
            
            # Convert timestamp to datetime if it's not already
            responses_df['Timestamp'] = pd.to_datetime(responses_df['Timestamp'])
            
            # Daily submissions
            daily_submissions = responses_df.groupby(responses_df['Timestamp'].dt.date).size().reset_index()
            daily_submissions.columns = ['Date', 'Submissions']
            
            # Daily submissions with color
            fig4 = go.Figure()
            fig4.add_trace(go.Scatter(
                x=daily_submissions['Date'],
                y=daily_submissions['Submissions'],
                mode='lines+markers',
                name='Daily Submissions',
                line=dict(color='#4169E1')  # Blue
            ))
            fig4.update_layout(title='Daily Submissions')
            st.plotly_chart(fig4, use_container_width=True)
            
            # Cumulative submissions with color
            st.subheader("Cumulative Submissions")
            daily_submissions['Cumulative'] = daily_submissions['Submissions'].cumsum()
            fig5 = go.Figure()
            fig5.add_trace(go.Scatter(
                x=daily_submissions['Date'],
                y=daily_submissions['Cumulative'],
                mode='lines+markers',
                name='Cumulative Submissions',
                line=dict(color='#90EE90')  # Green
            ))
            fig5.update_layout(title='Cumulative Submissions Over Time')
            st.plotly_chart(fig5, use_container_width=True)
    else:
        st.info("No responses collected yet.")

def update_total_points():
    """Update the total points in session state and show modal when hitting 90 points"""
    total = 0
    for skill in st.session_state.skills.keys():
        input_key = f"input_{skill}"
        if input_key in st.session_state:
            try:
                value = float(st.session_state[input_key])
                if value.is_integer():
                    total += int(value)
                else:
                    total += value
            except (ValueError, TypeError):
                continue
    
    new_total = round(total, 1)  # Round to 1 decimal place for consistency
    
    # Check if we just hit 90 points and haven't shown the modal yet
    if new_total >= 90 and st.session_state.total_points < 90:
        st.session_state.show_90_points_modal = True
    
    st.session_state.total_points = new_total
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

def show_skills_form(submitter_email, submitter_name):
    """Display the skills matrix form"""
    # Constants
    MAX_TOTAL_POINTS = 90
    MAX_POINTS_PER_SKILL = 10
    
    # Check if form was already submitted
    if 'form_submitted' not in st.session_state:
        st.session_state.form_submitted = False
    
    # If form was already submitted, show thank you message and exit
    if st.session_state.form_submitted:
        st.success(f"Thank you {submitter_name}! Your skills matrix has been submitted successfully!")
        st.balloons()
        
        # Add a close button
        if st.button("Close Survey"):
            # Reset all session state variables
            for key in list(st.session_state.keys()):
                del st.session_state[key]
            # Force redirect to a blank state
            st.markdown("Survey closed. Thank you for your participation!")
            st.stop()
        return

    # Show the 90 points modal if needed
    if st.session_state.get('show_90_points_modal', False):
        # Add CSS for modal overlay and positioning
        # Create container for modal and button
        col1, col2, col3 = st.columns([1,3,1])
        with col2:
            st.markdown("""
                <style>
                    .modal-overlay {
                        position: fixed;
                        top: 0;
                        left: 0;
                        right: 0;
                        bottom: 0;
                        background: rgba(0, 0, 0, 0.5);
                        z-index: 1000;
                        display: flex;
                        align-items: center;
                        justify-content: center;
                    }
                    .modal-content {
                        background: white;
                        padding: 2rem;
                        border-radius: 5px;
                        box-shadow: 0 2px 10px rgba(0, 0, 0, 0.1);
                        width: 90%;
                        max-width: 500px;
                        text-align: center;
                        z-index: 1001;
                    }
                    .modal-title {
                        color: #FF4B4B;
                        font-size: 1.5rem;
                        margin-bottom: 1rem;
                    }
                    .modal-text {
                        font-size: 1rem;
                        margin-bottom: 1.5rem;
                        text-align: left;
                    }
                </style>
                <div class="modal-overlay">
                    <div class="modal-content">
                        <div class="modal-title">🎉 Maximum Points Reached!</div>
                        <div class="modal-text">
                            You have now allocated all available points. To add points to other skills, 
                            you'll need to reduce points from your current allocations.<br><br>
                            Review your selections and adjust as needed to best reflect your expertise across different skills.
                        </div>
                    </div>
                </div>
            """, unsafe_allow_html=True)
            
            # Add the button using Streamlit's native component
            if st.button("OK, I'll adjust my values", key="modal_button", type="primary"):
                st.session_state.show_90_points_modal = False
                st.rerun()

    st.markdown("<u>**You can type a number directly or use the up/down arrows to enter your points**</u>", unsafe_allow_html=True)
    
    if st.session_state.total_points >= MAX_TOTAL_POINTS:
        st.warning("You have used all 90 points. To add points to other skills, first reduce points elsewhere.")
    
    st.markdown("---")
    
    # Create input fields for each skill
    skill_inputs = {}
    for skill in st.session_state.skills.keys():
        col1, col2, col3 = st.columns([3, 1, 1])
        
        with col1:
            st.markdown(f"**{skill}**")
        
        # Calculate maximum points available for this skill
        current_skill_points = st.session_state.get(f"input_{skill}", 0)
        remaining_points = MAX_TOTAL_POINTS - (st.session_state.total_points - current_skill_points)
        points_available = min(MAX_POINTS_PER_SKILL, remaining_points)
        
        with col2:
            try:
                value = st.number_input(
                    f"{skill} points",
                    min_value=0,
                    max_value=points_available,
                    value=current_skill_points,
                    key=f"input_{skill}",
                    on_change=update_total_points,
                    help="You've used all 90 points. To add points here, first reduce points in other skills." if st.session_state.total_points >= MAX_TOTAL_POINTS and current_skill_points == 0 else None
                )
                st.session_state.skills[skill] = value
                skill_inputs[skill] = value
            except:
                if st.session_state.total_points >= MAX_TOTAL_POINTS:
                    st.error("You've used all 90 points. To add points here, first reduce points in other skills.")
        
        with col3:
            st.markdown(get_expertise_level(value))
    
    # Submit form
    with st.form("skills_matrix"):
        submitted = st.form_submit_button("Submit Skills Matrix")
        
        if submitted:
            # Validate total points before submission
            if abs(st.session_state.total_points - MAX_TOTAL_POINTS) > 0.1:
                st.error(f"Total points must be exactly {MAX_TOTAL_POINTS}. Current total: {st.session_state.total_points}")
                return
                
            response_data = {
                'Response ID': str(uuid.uuid4())[:8],
                'Submitter Name': submitter_name,
                'Timestamp': datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                'Submitter Email': submitter_email,
                **st.session_state.skills
            }
            
            if save_response(response_data):
                # Set form_submitted to True instead of refreshing
                st.session_state.form_submitted = True
                st.experimental_rerun()  # This will be the last refresh to show success message
            else:
                st.error("There was an error saving your response. Please try again.")
def main():
    # Initialize total_points in session state if it doesn't exist
    if 'total_points' not in st.session_state:
        st.session_state.total_points = 0
    # Sidebar for navigation and points tracking
    with st.sidebar:
        st.title("Navigation")
        page = st.radio("Go to", ["Caravel Skills Matrix", "Admin"])
        
        # Always show points tracker in sidebar
        st.markdown("---")
        st.markdown("### Points Tracker")
        progress = min(st.session_state.total_points / 90, 1.0)
        st.progress(progress)
        st.metric("Total Points Used", st.session_state.total_points, f"/90 available")
        
        # Add color-coded expertise level legend
        st.markdown("---")
        st.markdown("### Expertise Levels")
        st.markdown("🔵 Primary (8-10 points)")
        st.markdown("🟢 Secondary (3-7 points)")
        st.markdown("🟡 Limited (1-2 points)")
    
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
    You have **90 points** to allocate across **168 skills** listed in the matrix. These points represent your level of expertise 
    and experience in each area. The goal is to allocate your points in a way that best reflects your true areas of strength. 
    You'll need to make thoughtful choices about where your expertise lies, prioritizing key skills over areas of limited 
    experience to ensure we capture an honest reflection of your abilities.
   
    ### Points Guidelines
    Maximum Points Per Skill: You can allocate a maximum of 10 points to any single skill.
    Primary Areas of Expertise: You should allocate higher points (e.g., 8-10) to the skills where you have deep expertise or significant experience.
    Secondary Areas of Expertise: For skills where you have some experience or intermediate-level knowledge, allocate moderate points (e.g., 3-7).
    Limited Experience: For skills where you have limited experience or basic understanding, allocate fewer points (e.g., 1-2), or none at all.
    
    ### How to Complete the Matrix
    
    **1. Review the Skills**:
    Carefully read through the skills listed in the matrix. Each skill represents a specific area of expertise relevant to our team's work.
    
    **2. Allocate Your Points**:
    Distribute your 90 points across the skills based on your expertise. Remember, the objective is to highlight your primary 
    strengths while providing an honest reflection of your experience in other areas. 
    
    **You can enter in a number between 1 and 10 or you could use the arrows to increase or decrease the number.**
    
    **3. Consider Balance**:
    While you are free to allocate up to 10 points for a single skill, keep in mind that spreading your points too thinly may 
    not fully represent your primary areas of expertise. Prioritize the skills where you are most confident and experienced.
    
    **4. Total Points**:
    Ensure that the total number of points you allocate across all skills does not exceed **90 points**.

    **5. Reaching 90 Points**:
    The system will not allow you to enter more values after you've reached 90 points. Once 90 points have been reached, adjust other entry values accordingly, utilizing the point tracker on the left to keep track of updated points.
    
    ### Example Point Distribution
    - **Distribution and Supply Agreements:** 🔵 8 points (Primary area of expertise—highly experienced)
    - **Employment Agreements:** 🟢 4 points (Moderate experience)
    - **Technology Transfer Agreements:** 🟡 2 points (Limited experience)
    """)
    
    # Email input before showing the form
    submitter_name = st.text_input("Enter your full name:")
    submitter_email = st.text_input("Enter your email:")
    
     # Initialize session state after valid inputs
    if submitter_email and submitter_name:  # Check for both name and email
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
                'Aquisitions (Skill 8)': 0,
                'Artificial Intelligence Terms, Regulations & Compliance (Skill 6)': 0,
                'Associations (Skill 7)': 0,   
                'Banking and Finance Transactions (Skill 9)': 0,
                'Banking Regulation and Compliance (Skill 10)': 0,
                'Bankrupcty and Insolvency (Debtor/Creditor) (Skill 11)': 0,
                'Biotech Agreements (Skill 12)': 0,
                'Blockchain Governance (Skill 13)': 0,
                'Board of Directors and Committees (Skill 14)': 0,
                'Canadian Anti-Spam Legislation (CASL) (Skill 15)': 0,
                'Children\'s Privacy (Skill 16)': 0,
                'Clinical Trials and Research (Skill 17)': 0,
                'Collections (Skill 27)': 0,
                'Commercial Contracts (Skill 20)': 0,
                'Commercial Real Estate Transactions (Skill 19)': 0,
                'Competition (Skill 18)': 0,
                'Construction (Skill 23)': 0,
                'Consumer Banking Regulations (Skill 21)': 0,
                'Consumer Protection (B2C) (Skill 22)': 0,
                'Content Creation and Copyright (Skill 24)': 0,
                'Content Removal and Takedown (Skill 25)': 0,
                'Continuous Disclosure (Skill 26)': 0,  
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
                'Dissolutions (Skill 70)': 0,
                'Distribution and Supply Agreements (Skill 46)': 0,
                'Drones (Skill 71)': 0,
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
                'Energy - Hydro (Skill 62)': 0,
                'Energy - Nuclear (Skill 63)': 0,
                'Energy - Solar (Skill 60)': 0,
                'Energy - Wind (Skill 61)': 0,
                'Entertainment and Sponsorship Agreements (Skill 64)': 0,
                'Environmental Sustainability Compliance (Skill 65)': 0,
                'Equity Compensation or Incentive Plans (Skill 66)': 0,
                'Escrow Agreements (Skill 67)': 0,
                'Executive Compensation (Skill 68)': 0,
                'Export Control Regulations (Skill 69)': 0,
                'Federal and Provincial Government Contracting (Prime and Subs) (Skill 72)': 0,
                'Financial Services Regulatory Requirements (Skill 73)': 0,
                'Financial Transactions and Structuring (Skill 74)': 0,
                'Fintech (Skill 75)': 0,
                'Fintrac (Skill 76)': 0,
                'Forced Labour and Slavery (Skill 77)': 0,
                'Formation and Entity Creation/Operating Agreements (Skill 78)': 0,
                'Founder Agreements (Skill 79)': 0,
                'Franchise Law - Franchisee (Skill 81)': 0,
                'Franchise Law - Franchisor (Skill 80)': 0,
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
                'Initial Public Offering (IPO) (Skill 103)': 0,
                'Insurance Coverage Review (Skill 95)': 0,
                'Intellectual Property in M&A (Skill 96)': 0,
                'Intellectual Property Infringement (Skill 97)': 0,
                'Intellectual Property Licensing (Skill 98)': 0,
                'Intellectual Property Protection (Skill 99)': 0,
                'International Data Transfers (Skill 100)': 0,
                'International Trade and Import Export (Skill 101)': 0,
                'International/Foreign Government Contracts (Skill 102)': 0,
                'Investment and Funding (Skill 104)': 0,
                'Investment Law and Regulations (Skill 105)': 0,
                'Investor Relations and Reporting (Skill 106)': 0,
                'Joint Ventures and Strategic Alliances (Skill 107)': 0,
                'Labour and Union (Skill 108)': 0,
                'Land Use and Zoning (Skill 109)': 0,
                'Leasing (Commercial Property) (Skill 111)': 0,
                'Leasing (Equipment) (Skill 110)': 0,
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
                'Patent Portfolio Management (Skill 137)': 0,
                'Patent Prosecution (Skill 139)': 0,
                'Payment Systems and Digital Payments (Skill 140)': 0,
                'Pension Fund Management (Skill 141)': 0,
                'Pharmaceutical Licensing (Skill 142)': 0,
                'Policy Creation (Skill 143)': 0,
                'Power Purchase Agreements (Skill 144)': 0,
                'Privacy Compliance (Skill 145)': 0,
                'Private Company Corporate Governance (Skill 146)': 0,
                'Private Equity and Venture Capital (Skill 147)': 0,
                'Private Public Partnerships (P3) (Skill 136)': 0,
                'Procurement (private) & RFPs (Skill 148)': 0,
                'Procurement (public) & RFPs (Skill 149)': 0,
                'Product Labeling and Packaging (Skill 150)': 0,
                'Product Warranties/Agreement Warranties (Skill 151)': 0,
                'Professional Services Agreements and related SOWs (Skill 152)': 0,
                'Prospectus (Skill 138)': 0,
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
        
        show_skills_form(submitter_email,submitter_name)

if __name__ == "__main__":
    main()
