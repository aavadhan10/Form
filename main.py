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
            # Calculate skill columns and expertise distribution first
            skill_cols = [col for col in responses_df.columns if col not in ['Response ID', 'Timestamp', 'Submitter Email']]
            
            def get_expertise_counts(row):
                primary = sum(1 for x in row if x >= 8)
                secondary = sum(1 for x in row if 3 <= x < 8)
                limited = sum(1 for x in row if 1 <= x < 3)
                return pd.Series({'Primary': primary, 'Secondary': secondary, 'Limited': limited})
            
            expertise_dist = responses_df[skill_cols].apply(get_expertise_counts, axis=1)
            
            # Summary statistics table
            st.subheader("Summary Statistics")
            col1, col2 = st.columns(2)
            
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
            # Calculate average points for each skill (excluding metadata columns)
            skill_cols = [col for col in responses_df.columns if col not in ['Response ID', 'Timestamp', 'Submitter Email']]
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
        
        # Tab 2: Expertise Distribution
        with tab2:
            st.subheader("Distribution of Expertise Levels")
            
            def get_expertise_counts(row):
                primary = sum(1 for x in row if x >= 8)
                secondary = sum(1 for x in row if 3 <= x < 8)
                limited = sum(1 for x in row if 1 <= x < 3)
                return pd.Series({'Primary': primary, 'Secondary': secondary, 'Limited': limited})
            
            expertise_dist = responses_df[skill_cols].apply(get_expertise_counts, axis=1)
            
            # Average number of skills per expertise level
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("Avg Primary Skills", f"{expertise_dist['Primary'].mean():.1f}")
            with col2:
                st.metric("Avg Secondary Skills", f"{expertise_dist['Secondary'].mean():.1f}")
            with col3:
                st.metric("Avg Limited Skills", f"{expertise_dist['Limited'].mean():.1f}")
            
            # Distribution chart with colors
            st.subheader("Distribution of Expertise Levels Across Team")
            expertise_totals = expertise_dist.sum()
            fig3 = go.Figure(data=[
                go.Bar(
                    x=['Primary', 'Secondary', 'Limited'],
                    y=expertise_totals,
                    marker_color=['#4169E1', '#90EE90', '#FFE5B4']  # Blue, Green, Yellow
                )
            ])
            fig3.update_layout(title='Distribution of Expertise Levels')
            st.plotly_chart(fig3, use_container_width=True)

            # Detailed breakdown of skills by expertise level
            st.subheader("Detailed Expertise Breakdown")
            
            # Create DataFrame with skill counts by expertise level
            def categorize_expertise(points):
                if points >= 8:
                    return 'Primary'
                elif points >= 3:
                    return 'Secondary'
                elif points > 0:
                    return 'Limited'
                return 'None'
            
            expertise_breakdown = pd.DataFrame()
            for skill in skill_cols:
                skill_series = responses_df[skill].apply(categorize_expertise).value_counts()
                expertise_breakdown[skill] = skill_series
            
            expertise_breakdown = expertise_breakdown.fillna(0)
            
            # Create a stacked bar chart for each skill
            fig_breakdown = go.Figure()
            
            # Add bars for each expertise level
            for level, color in [('Primary', '#4169E1'), ('Secondary', '#90EE90'), ('Limited', '#FFE5B4')]:
                if level in expertise_breakdown.index:
                    fig_breakdown.add_trace(go.Bar(
                        name=level,
                        x=expertise_breakdown.columns,
                        y=expertise_breakdown.loc[level],
                        marker_color=color
                    ))
            
            fig_breakdown.update_layout(
                barmode='stack',
                title='Expertise Level Distribution by Skill',
                xaxis_tickangle=-45,
                height=600  # Make the chart taller
            )
            st.plotly_chart(fig_breakdown, use_container_width=True)

            
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
    """Update the total points in session state"""
    # Calculate sum from the actual input values, not the session state
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
    # Constants
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
        st.error(f"⚠️ You have exceeded the maximum total points of {MAX_TOTAL_POINTS}")
    
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
                st.error(f"Cannot submit: Total points ({st.session_state.total_points}) exceed maximum of {MAX_TOTAL_POINTS}")
            else:
                response_data = {
                    'Response ID': str(uuid.uuid4())[:8],
                    'Timestamp': datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                    'Submitter Email': submitter_email,
                    **st.session_state.skills
                }
                
                if save_response(response_data):
                    st.success("Skills matrix submitted successfully!")
                    
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
        if check_password():
            show_admin_page()
            return
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
                'Advertising and Labeling Regulations (Pharma/BioTech)': 0,
                'Advertising and Marketing Regulations (Retail and Consumer)': 0,
                'Advertising and Marketing Regulations (Skill 3)': 0,
                'Advertising and Marketing Regulations (Skill 4)': 0,
                'Advertising and Marketing Regulations (Skill 5)': 0,
                'Advertising and Marketing Regulations (Skill 6)': 0,
            }
        
        show_skills_form(submitter_email)

if __name__ == "__main__":
    main()
