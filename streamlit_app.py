import streamlit as st
from app.query_parser import parse_query_with_gemini
from app.database import get_user_profile
from app.recommendation_engine import generate_job_recommendations

# 🎨 Streamlit UI Configuration
st.set_page_config(page_title="AI Job Recommendation System", layout="wide")

st.title("💼 AI-Powered Job Recommendation System")
st.markdown("Enter a natural language query to create your job-seeker profile and get personalized job recommendations.")

# Create two columns for the layout
col1, col2 = st.columns([1, 1])

# 🔹 Section 1: Profile Creation & Loading
with col1:
    st.subheader("📝 Create or Update Your Job-Seeker Profile")

    # 📥 User input
    user_input = st.text_area("Describe your experience, skills, and job preferences:", 
                              "My name is John, I have 3 years of experience in AI and machine learning. I know Python, TensorFlow, and want a remote AI Engineer job.")

    if st.button("Parse Job Query", type="primary"):
        if user_input.strip():
            with st.spinner("🔍 Parsing job preferences..."):
                response = parse_query_with_gemini(user_input)

            # 📌 Handle response errors
            if not response or "error" in response:
                st.error("❌ Error parsing query. Please try again.")
            else:
                user_id = response.get("user_id")
                if not user_id:
                    st.error("❌ No user ID generated. Try refining your query.")
                else:
                    user_profile = get_user_profile(user_id)
                    st.session_state.last_user_id = user_id
                    st.session_state.show_recommendations = True

                    if user_profile:
                        st.success(f"✅ Job-seeker profile updated! Your User ID: {user_id}")
                    else:
                        st.success(f"✅ New job-seeker profile created! Your User ID: {user_id}")

                    st.json(response)  # Show parsed profile as JSON
        else:
            st.warning("⚠️ Please enter a query before clicking Parse.")

    # 🔹 Option to Load Existing Job-Seeker Profile
    st.subheader("🔍 Load Your Profile")
    default_user_id = st.session_state.get("last_user_id", "")
    user_id_input = st.text_input("Enter Your User ID:", value=default_user_id)

    if st.button("Load Profile"):
        if user_id_input.strip():
            user_profile = get_user_profile(user_id_input)
            if user_profile:
                st.success(f"✅ Profile loaded for: {user_profile.get('name', user_id_input)}")
                st.session_state.last_user_id = user_id_input
                st.session_state.show_recommendations = True
            else:
                st.error(f"❌ User with ID {user_id_input} not found.")
        else:
            st.warning("⚠️ Please enter a User ID.")

# 🔹 Section 2: Job Recommendations
with col2:
    st.subheader("🚀 Personalized Job Recommendations")

    if st.session_state.get("show_recommendations", False):
        user_id = st.session_state.get("last_user_id")
        user_profile = get_user_profile(user_id)

        if user_profile:
            # 📌 Job-Seeker Profile Summary (Collapsible)
            with st.expander("📋 Job-Seeker Profile Summary", expanded=False):
                st.write(f"**👤 Name:** {user_profile.get('name', 'Not specified')}")
                st.write(f"**💼 Preferred Roles:** {', '.join(user_profile.get('preferences', {}).get('role', [])) or 'None specified'}")
                st.write(f"**📍 Location Preference:** {user_profile.get('preferences', {}).get('location', 'Not specified')}")
                
                preferences = user_profile.get('preferences', {})
                demographics = user_profile.get('demographics', {})

                if demographics.get('experience'):
                    st.write(f"**📆 Experience:** {demographics.get('experience')} years")

                if demographics.get('skills'):
                    st.write(f"**🛠️ Skills:** {', '.join(demographics.get('skills', []))}")
                if demographics.get('industries'):
                    st.write(f"**🏢 Industries:** {', '.join(demographics.get('industries', []))}")

                # Remote/Hybrid preference
                if preferences.get("remote"):
                    st.write("**🌍 Work Preference:** Remote")
                elif preferences.get("hybrid"):
                    st.write("**🏢 Work Preference:** Hybrid")
                else:
                    st.write("**🏢 Work Preference:** On-site or not specified")

            # 🔹 Select Number of Job Recommendations
            num_recommendations = st.slider("📌 Number of Job Recommendations", 3, 10, 5)

            # 🟢 Get Job Recommendations Button
            if st.button("Find Jobs", type="primary"):
                with st.spinner("🔍 Searching for jobs..."):
                    recommendations = generate_job_recommendations(user_id, limit=num_recommendations)

                if recommendations:
                    for i, rec in enumerate(recommendations, 1):
                        with st.expander(f"💼 {i}. {rec.get('title', 'Untitled Job')}", expanded=i == 1):
                            st.write(f"**🏢 Company:** {rec.get('company', 'Unknown')}")
                            st.write(f"**📍 Location:** {rec.get('location', 'Not specified')}")
                            st.write(f"**📝 Job Type:** {rec.get('job_type', 'Not specified')}")
                            st.write(f"**💰 Salary Range:** {rec.get('salary', 'Not specified')}")
                            st.write(f"**📜 Description:** {rec.get('snippet', 'No description available')}")
                            st.write(f"**🔗 Job Posting:**")
                            st.link_button("🔎 View Job", rec.get('link'))
                else:
                    st.warning("❌ No job recommendations found. Try updating your profile with more details.")
        else:
            st.info("ℹ️ Create or load a job-seeker profile to see job recommendations.")
    else:
        st.info("ℹ️ Create or load a profile to see job recommendations.")

# 📌 Footer Instructions
st.divider()
st.caption("**📖 How to use this app:**")
st.caption("1️⃣ Enter your job preferences and skills in the text box above.")
st.caption("2️⃣ Click 'Parse Job Query' to create your job-seeker profile.")
st.caption("3️⃣ Click 'Find Jobs' to see personalized job openings.")
st.caption("4️⃣ Save your User ID to retrieve your profile later.")
