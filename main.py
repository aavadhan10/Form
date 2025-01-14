import streamlit as st
import pandas as pd
from datetime import datetime
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.application import MIMEApplication
import uuid
import json
import os

def save_response_locally(df):
    """Save response to a local CSV for aggregation"""
    filename = "all_responses.csv"
    if os.path.exists(filename):
        existing_df = pd.read_csv(filename)
        updated_df = pd.concat([existing_df, df], ignore_index=True)
    else:
        updated_df = df
    updated_df.to_csv(filename, index=False)

def send_email_with_csv(df, submitter_email):
    sender_email = "aavadhan@umich.edu"
    receiver_email = "aavadhan@umich.edu"
    
    msg = MIMEMultipart()
    msg['Subject'] = f'Skills Matrix Response #{df.iloc[0]["Response ID"]} - {submitter_email}'
    msg['From'] = sender_email
    msg['To'] = receiver_email
    
    # Enhanced email body with submission stats
    body = f"""
    New Skills Matrix Submission
    
    Response ID: {df.iloc[0]["Response ID"]}
    From: {submitter_email}
    Time: {df.iloc[0]["Timestamp"]}
    Total Points Used: {sum(df.iloc[0][3:])}  # Skipping ID, timestamp, and email columns
    
    Expertise Breakdown:
    Primary (8-10 points): {sum(1 for x in df.iloc[0][3:] if x >= 8)} skills
    Secondary (3-7 points): {sum(1 for x in df.iloc[0][3:] if 3 <= x < 8)} skills
    Limited (1-2 points): {sum(1 for x in df.iloc[0][3:] if 1 <= x < 3)} skills
    """
    msg.attach(MIMEText(body, 'plain'))
    
    # Attach individual response CSV
    csv_data = df.to_csv(index=False)
    attachment = MIMEApplication(csv_data.encode('utf-8'))
    attachment['Content-Disposition'] = f'attachment; filename="skills_matrix_response_{df.iloc[0]["Response ID"]}.csv"'
    msg.attach(attachment)
    
    # If this is a multiple of 10 submissions, attach the aggregate file too
    if os.path.exists("all_responses.csv"):
        all_df = pd.read_csv("all_responses.csv")
        if len(all_df) % 10 == 0:  # Every 10 submissions
            aggregate_csv = all_df.to_csv(index=False)
            agg_attachment = MIMEApplication(aggregate_csv.encode('utf-8'))
            agg_attachment['Content-Disposition'] = 'attachment; filename="all_skills_matrix_responses.csv"'
            msg.attach(agg_attachment)
            
            # Add summary stats to email body
            body += f"""
            
            Aggregate Statistics:
            Total Submissions: {len(all_df)}
            Most Common Primary Skills: {', '.join(all_df.iloc[:, 3:].apply(lambda x: sum(x >= 8)).nlargest(3).index)}
            Average Points Used: {all_df.iloc[:, 3:].sum(axis=1).mean():.1f}
            """
            msg.attach(MIMEText(body, 'plain'))
    
    try:
        with smtplib.SMTP_SSL('smtp.gmail.com', 465) as server:
            server.login(sender_email, st.secrets["email"]["password"])
            server.send_message(msg)
        return True
    except Exception as e:
        st.error(f"Failed to send email: {str(e)}")
        return False

def main():
    st.title("Caravel Law Skills Matrix")
    
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
            # Add all skills here
        }
    
    MAX_TOTAL_POINTS = 90
    MAX_POINTS_PER_SKILL = 10
    
    submitter_email = st.text_input("Enter your email:")
    
    # Visual progress indicator
    progress = st.session_state.total_points / MAX_TOTAL_POINTS
    st.progress(progress)
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
        
        # Improved layout with tabs for skill categories
        tabs = st.tabs(["General Skills", "Industry Specific", "Technical Skills"])
        
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
                # Generate unique response ID
                response_id = str(uuid.uuid4())[:8]
                
                response_data = {
                    'Response ID': response_id,
                    'Timestamp': datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                    'Submitter Email': submitter_email,
                    **st.session_state.skills
                }
                df = pd.DataFrame([response_data])
                
                # Save locally and send email
                save_response_locally(df)
                if send_email_with_csv(df, submitter_email):
                    st.success("✅ Skills matrix submitted successfully!")
                    # Reset form
                    st.session_state.skills = {k: 0 for k in st.session_state.skills}
                    st.session_state.total_points = 0
                    st.balloons()  # Add a fun touch!
                    st.experimental_rerun()

if __name__ == "__main__":
    main()
