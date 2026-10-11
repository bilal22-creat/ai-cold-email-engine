import streamlit as st
import anthropic

# Page Configuration
st.set_page_config(
    page_title="B2B AI Cold Email Engine",
    page_icon="⚡",
    layout="wide"
)

# Custom CSS for Premium UI
st.markdown("""
<style>
    .main-header {
        font-size: 2.2rem;
        font-weight: 700;
        color: #1E293B;
        margin-bottom: 0.5rem;
    }
    .sub-header {
        font-size: 1rem;
        color: #64748B;
        margin-bottom: 2rem;
    }
    .credit-badge {
        background-color: #E0E7FF;
        color: #4338CA;
        padding: 0.3rem 0.8rem;
        border-radius: 20px;
        font-weight: 600;
        font-size: 0.85rem;
    }
</style>
""", unsafe_allow_html=True)

# Initialize Session State
if 'credits' not in st.session_state:
    st.session_state.credits = 3

# Sidebar
with st.sidebar:
    st.title("⚙️ Engine Configuration")
    api_key = st.text_input("Enter Anthropic API Key:", type="password", help="Requires a valid Claude 3.5 Sonnet API key.")
    st.markdown("---")
    st.markdown(f"**Remaining Credits:** <span class='credit-badge'>{st.session_state.credits} Free Credits</span>", unsafe_allow_html=True)
    st.markdown("---")
    st.caption("B2B Cold Outreach Engine v1.0")

# Main Interface
st.markdown("<div class='main-header'>AI Cold Email & Personalization Engine</div>", unsafe_allow_html=True)
st.markdown("<div class='sub-header'>Generate highly-tailored B2B cold emails & LinkedIn connection notes powered by Claude 3.5 Sonnet.</div>", unsafe_allow_html=True)

col1, col2 = st.columns([1, 1], gap="large")

with col1:
    st.subheader("📥 Input Offer & Lead Details")
    outreach_type = st.radio("Select Outreach Channel:", ["Cold Email", "LinkedIn InMail / Message"])
    user_offer = st.text_area("Your Product/Service Offer:", placeholder="e.g., Construction estimation and quantity takeoff services for US general contractors.", height=100)
    prospect_info = st.text_area("Prospect Information (Paste Bio/Company Info):", placeholder="e.g., John Doe, CEO of Apex Construction. Looking to streamline bidding and estimation bottlenecks.", height=120)
    tone = st.selectbox("Tone / Style:", ["Professional & Direct", "Casual & Value-Focused", "Short & Punchy (Under 100 words)"])

with col2:
    st.subheader("🚀 Output Engine")
    
    if st.button("Generate Cold Email", type="primary", use_container_width=True):
        if not api_key:
            st.error("Please enter a valid Anthropic API Key in the sidebar.")
        elif st.session_state.credits <= 0:
            st.warning("You have exhausted your free credits! Please upgrade for unlimited generations.")
        elif not user_offer or not prospect_info:
            st.error("Please fill in both your offer and prospect details.")
        else:
            with st.spinner("Crafting personalized email..."):
                try:
                    client = anthropic.Anthropic(api_key=api_key)
                    
                    prompt = f"""You are an expert B2B copywriter. Craft a highly compelling, personalized {outreach_type} based on the following:
- My Offer: {user_offer}
- Prospect Context: {prospect_info}
- Tone: {tone}

Instructions:
1. Hook the prospect using their context.
2. Clearly state the value offer without sounding overly salesy.
3. Include a soft Call to Action (CTA).
4. Do not use generic filler words or cliché intros.
"""
                    response = client.messages.create(
                        model="claude-3-5-sonnet-20241022",
                        max_tokens=600,
                        messages=[{"role": "user", "content": prompt}]
                    )
                    
                    generated_text = response.content[0].text
                    st.session_state.credits -= 1
                    
                    st.success("Generated Successfully!")
                    st.text_area("Result:", value=generated_text, height=260)
                    st.code(generated_text, language="markdown")
                    
                except Exception as e:
                    st.error(f"Error generating copy: {str(e)}")
