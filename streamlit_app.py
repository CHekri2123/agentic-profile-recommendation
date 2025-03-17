import streamlit as st
from app.query_parser import parse_query_with_gemini
from app.database import get_user_profile
from app.recommendation_engine import generate_recommendations

# 🎨 Streamlit UI
st.set_page_config(page_title="AI Recommendation System", layout="wide")

st.title("AI-Powered Recommendation System")
st.markdown("Enter a natural language query to create your profile and get personalized recommendations.")

# Create two columns for the layout
col1, col2 = st.columns([1, 1])

with col1:
    st.subheader("Create or Update Your Profile")
    
    # 📥 User input
    user_input = st.text_area("Describe your interests, skills, and preferences:", 
                             "My name is John, I'm interested in AI and machine learning. I know Python and TensorFlow.")
    
    if st.button("Parse Query"):
        if user_input.strip():
            with st.spinner("Parsing query..."):
                response = parse_query_with_gemini(user_input)
            
            # 📌 Output
            st.write("🔹 **Parsed Profile:**")
            st.json(response)
            
            # 🔴 Error Handling
            if "error" in response:
                st.error(response["error"])
            else:
                user_id = response["user_id"]
                existing_user = get_user_profile(user_id)
                
                if existing_user:
                    st.success(f"✅ Profile updated! Your User ID: {user_id}")
                else:
                    st.success(f"✅ New profile created! Your User ID: {user_id}")
                
                # Store user_id in session state
                st.session_state.last_user_id = user_id
                st.session_state.show_recommendations = True
        else:
            st.warning("⚠️ Please enter a query before clicking Parse.")
    
    # Option to use existing profile
    st.subheader("Or Use Existing Profile")
    default_user_id = st.session_state.get("last_user_id", "")
    user_id_input = st.text_input("Enter User ID:", value=default_user_id)
    
    if st.button("Load Profile"):
        if user_id_input:
            user_profile = get_user_profile(user_id_input)
            if user_profile:
                st.success(f"✅ Profile loaded for: {user_profile.get('name', user_id_input)}")
                st.session_state.last_user_id = user_id_input
                st.session_state.show_recommendations = True
            else:
                st.error(f"User with ID {user_id_input} not found.")
        else:
            st.warning("⚠️ Please enter a User ID.")

with col2:
    st.subheader("Your Recommendations")
    
    if "show_recommendations" in st.session_state and st.session_state.show_recommendations:
        user_id = st.session_state.last_user_id
        user_profile = get_user_profile(user_id)
        
        if user_profile:
            # Display profile summary
            with st.expander("Profile Summary", expanded=False):
                st.write(f"**Name:** {user_profile.get('name', 'Not specified')}")
                st.write(f"**Interests:** {', '.join(user_profile.get('interests', []))}")
                
                preferences = user_profile.get('preferences', {})
                if preferences:
                    st.write("**Preferences:**")
                    for key, value in preferences.items():
                        if value is not None and value != "":
                            st.write(f"- {key.replace('_', ' ').title()}: {value}")
                
                demographics = user_profile.get('demographics', {})
                if demographics.get('skills'):
                    st.write(f"**Skills:** {', '.join(demographics.get('skills', []))}")
                if demographics.get('industries'):
                    st.write(f"**Industries:** {', '.join(demographics.get('industries', []))}")
            
            # Number of recommendations
            num_recommendations = st.slider("Number of recommendations", 3, 10, 5)
            
            # Get recommendations button
            if st.button("Get Recommendations"):
                with st.spinner("Generating personalized recommendations..."):
                    recommendations = generate_recommendations(user_id, limit=num_recommendations)
                
                if recommendations:
                    for i, rec in enumerate(recommendations, 1):
                        with st.expander(f"{i}. {rec.get('title')}", expanded=i==1):
                            st.write(f"**Why this is relevant:** {rec.get('explanation', 'No explanation available')}")
                            st.write(f"**Source:** {rec.get('source_name', rec.get('source', 'Unknown'))}")
                            st.write(f"**Relevance Score:** {rec.get('gemini_relevance_score', rec.get('relevance_score', 0))}/100")
                            st.write(f"**Snippet:** {rec.get('snippet', 'No snippet available')}")
                            st.link_button("View Full Content", rec.get('link'))
                else:
                    st.warning("No recommendations found. Try updating your profile with more specific interests.")
        else:
            st.info("Create or load a profile to see recommendations.")
    else:
        st.info("Create or load a profile to see recommendations.")

# Add a footer with instructions
st.divider()
st.caption("**How to use this app:**")
st.caption("1. Enter a description of your interests and preferences in the text area")
st.caption("2. Click 'Parse Query' to create your profile")
st.caption("3. Click 'Get Recommendations' to see personalized content")
st.caption("4. Save your User ID to retrieve your profile later")
