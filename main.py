import streamlit as st
import pandas as pd
from datetime import datetime
import uuid

# Add this at the very top of your script
st.set_page_config(page_title="Skills Matrix", layout="wide")

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

def save_response(response_data):
    """Save response to the session state dataframe"""
    if 'all_responses' not in st.session_state:
        st.session_state.all_responses = pd.DataFrame()
    
    new_response = pd.DataFrame([response_data])
    st.session_state.all_responses = pd.concat([st.session_state.all_responses, new_response], ignore_index=True)

def show_admin_page():
    """Shows the admin page with download functionality"""
    st.header("Admin Dashboard")
    
    if 'all_responses' in st.session_state and not st.session_state.all_responses.empty:
        st.success(f"Total responses collected: {len(st.session_state.all_responses)}")
        
        # Download button
        st.download_button(
            "📥 Download All Responses",
            st.session_state.all_responses.to_csv(index=False),
            "skills_matrix_responses.csv",
            "text/csv",
            key='download-csv'
        )
        
        # Show preview of responses
        st.subheader("Preview of Responses")
        st.dataframe(st.session_state.all_responses)
    else:
        st.info("No responses collected yet.")

def main():
    # Sidebar for navigation
    with st.sidebar:
        st.title("Navigation")
        page = st.radio("Go to", ["Submit Response", "Admin"])
    
    if page == "Admin":
        if check_password():
            show_admin_page()
            return
        return
    
    # Main form page
    st.title("Caravel Law Skills Matrix")
    
    # Initialize session state
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
    
    # Constants
    MAX_TOTAL_POINTS = 90
    MAX_POINTS_PER_SKILL = 10
    
    # Email input
    submitter_email = st.text_input("Enter your email:")
    
    # Visual progress indicator
    col1, col2 = st.columns([2, 1])
    with col1:
        progress = st.session_state.total_points / MAX_TOTAL_POINTS
        st.progress(progress)
    with col2:
        st.metric("Total Points Used", st.session_state.total_points, f"/{MAX_TOTAL_POINTS} available")
    
    if st.session_state.total_points > MAX_TOTAL_POINTS:
        st.error(f"⚠️ You have exceeded the maximum total points of {MAX_TOTAL_POINTS}")
    
    with st.form("skills_matrix"):
        st.markdown("### Instructions")
        st.markdown("""
        - You have **90 points** to allocate across all skills
        - Maximum **10 points** per skill
        - Primary expertise (8-10 points)
        - Secondary expertise (3-7 points)
        - Limited expertise (1-2 points)
        """)
        
        st.markdown("---")
        
        # Create input fields for each skill
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
                )
                st.session_state.skills[skill] = value
            
            with col3:
                if value >= 8:
                    st.markdown("🔵 Primary")
                elif value >= 3:
                    st.markdown("🟢 Secondary")
                elif value >= 1:
                    st.markdown("🟡 Limited")
        
        st.session_state.total_points = sum(st.session_state.skills.values())
        
        submitted = st.form_submit_button("Submit Skills Matrix")
        
        if submitted:
            if not submitter_email:
                st.error("Please enter your email address")
            elif st.session_state.total_points > MAX_TOTAL_POINTS:
                st.error(f"Cannot submit: Total points ({st.session_state.total_points}) exceed maximum of {MAX_TOTAL_POINTS}")
            else:
                response_data = {
                    'Response ID': str(uuid.uuid4())[:8],
                    'Timestamp': datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                    'Submitter Email': submitter_email,
                    **st.session_state.skills
                }
                
                save_response(response_data)
                st.success("Skills matrix submitted successfully!")
                
                # Reset form
                st.session_state.skills = {k: 0 for k in st.session_state.skills}
                st.session_state.total_points = 0

if __name__ == "__main__":
    main()
