import streamlit as st
import pandas as pd
from datetime import datetime
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.application import MIMEApplication
import os

def send_email_with_csv(df):
    # Email settings
    sender_email = "your-email@gmail.com"  # Replace with your email
    sender_password = "your-app-password"   # Replace with your app password
    receiver_email = "aavadhan@umich.edu"
    
    # Create message
    msg = MIMEMultipart()
    msg['Subject'] = f'Skills Matrix Response - {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}'
    msg['From'] = sender_email
    msg['To'] = receiver_email
    
    # Convert DataFrame to CSV and attach
    csv_data = df.to_csv(index=False)
    attachment = MIMEApplication(csv_data.encode('utf-8'))
    attachment['Content-Disposition'] = 'attachment; filename="skills_matrix_response.csv"'
    msg.attach(attachment)
    
    # Send email
    try:
        with smtplib.SMTP_SSL('smtp.gmail.com', 465) as server:
            server.login(sender_email, sender_password)
            server.send_message(msg)
        return True
    except Exception as e:
        st.error(f"Failed to send email: {str(e)}")
        return False

def main():
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
    email = st.text_input("Enter your email:")
    
    # Display total points
    st.metric("Total Points Used", st.session_state.total_points, f"/{MAX_TOTAL_POINTS} available")
    
    if st.session_state.total_points > MAX_TOTAL_POINTS:
        st.error(f"⚠️ You have exceeded the maximum total points of {MAX_TOTAL_POINTS}")
    
    # Create form
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
        
        # Create columns for layout
        col1, col2 = st.columns([3, 1])
        
        # Track changes in total points
        new_total = 0
        
        # Create input fields for each skill
        for skill in st.session_state.skills.keys():
            with col1:
                st.markdown(f"**{skill}**")
            with col2:
                key = f"input_{skill}"
                value = st.number_input(
                    f"{skill} points",
                    min_value=0,
                    max_value=MAX_POINTS_PER_SKILL,
                    value=st.session_state.skills[skill],
                    key=key,
                    label_visibility="collapsed"
                )
                
                st.session_state.skills[skill] = value
                new_total += value
                
                # Display expertise level
                if value >= 8:
                    st.markdown("🔵 Primary")
                elif value >= 3:
                    st.markdown("🟢 Secondary")
                elif value >= 1:
                    st.markdown("🟡 Limited")
        
        st.session_state.total_points = new_total
        
        # Submit button
        submitted = st.form_submit_button("Submit Skills Matrix")
        
        if submitted:
            if not email:
                st.error("Please enter your email address")
            elif st.session_state.total_points > MAX_TOTAL_POINTS:
                st.error(f"Cannot submit: Total points ({st.session_state.total_points}) exceed maximum of {MAX_TOTAL_POINTS}")
            else:
                # Create DataFrame for submission
                response_data = {
                    'Timestamp': datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                    'Email': email,
                    **st.session_state.skills
                }
                df = pd.DataFrame([response_data])
                
                # Send email with CSV
                if send_email_with_csv(df):
                    st.success("Skills matrix submitted successfully! Response has been emailed.")
                    # Reset form
                    st.session_state.skills = {k: 0 for k in st.session_state.skills}
                    st.session_state.total_points = 0
                    st.experimental_rerun()

if __name__ == "__main__":
    main()
