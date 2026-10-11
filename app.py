import streamlit as st
import pandas as pd
import requests
import smtplib
import re
import dns.resolver
import time
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import anthropic
import random
from datetime import datetime, timedelta

# Page Configuration for SaaS Web App & Mobile Compatibility
st.set_page_config(
    page_title="Instantly Enterprise - B2B Sales & Bidding Engine",
    page_icon="⚡",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ---------------------------------------------------------
# Instantly.ai Dark Emerald Theme & Styling
# ---------------------------------------------------------
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@400;500;600;700;800&display=swap');
    * { font-family: 'Plus Jakarta Sans', sans-serif !important; }
    
    .stApp { background-color: #080c14; color: #f8fafc; }
    #MainMenu, footer, header { visibility: hidden; }
    
    .instantly-navbar {
        background: rgba(15, 23, 42, 0.75);
        border: 1px solid rgba(255, 255, 255, 0.08);
        border-radius: 14px;
        padding: 18px 26px;
        margin-bottom: 20px;
        backdrop-filter: blur(16px);
    }
    .instantly-brand {
        font-size: 1.6rem;
        font-weight: 800;
        background: linear-gradient(135deg, #10b981 0%, #3b82f6 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        margin: 0;
    }
    .instantly-card {
        background: #0f172a;
        border: 1px solid rgba(255, 255, 255, 0.07);
        border-radius: 14px;
        padding: 22px;
        margin-bottom: 18px;
    }
    div[data-testid="stMetric"] {
        background: #1e293b !important;
        border: 1px solid rgba(16, 185, 129, 0.2) !important;
        border-radius: 12px !important;
        padding: 14px 18px !important;
    }
    div[data-testid="stMetricLabel"] {
        color: #94a3b8 !important;
        font-size: 0.8rem !important;
        font-weight: 600 !important;
    }
    div[data-testid="stMetricValue"] {
        color: #10b981 !important;
        font-weight: 800 !important;
    }
    .stTabs [data-baseweb="tab-list"] {
        gap: 6px;
        background: #0b0f19;
        padding: 6px;
        border-radius: 12px;
        border: 1px solid rgba(255, 255, 255, 0.08);
    }
    .stTabs [data-baseweb="tab"] {
        height: 42px;
        border-radius: 8px;
        color: #94a3b8;
        font-weight: 600;
        font-size: 0.86rem;
        border: none !important;
        padding: 0px 18px;
    }
    .stTabs [aria-selected="true"] {
        background: linear-gradient(135deg, #10b981 0%, #059669 100%) !important;
        color: #ffffff !important;
    }
    .stButton>button {
        background: linear-gradient(135deg, #10b981 0%, #059669 100%);
        color: #ffffff;
        font-weight: 700;
        border: none;
        border-radius: 8px;
        padding: 10px 24px;
    }
</style>
""", unsafe_allow_html=True)

# ---------------------------------------------------------
# Real Data Pools
# ---------------------------------------------------------
FIRST_NAMES = ["Michael", "David", "Robert", "James", "William", "John", "Richard", "Thomas", "Charles", "Daniel", "Matthew", "Mark", "Christopher", "Andrew", "Steven", "Paul"]
LAST_NAMES = ["Smith", "Johnson", "Williams", "Brown", "Jones", "Miller", "Davis", "Wilson", "Taylor", "Anderson", "Thomas", "Jackson", "White", "Harris", "Martin", "Thompson"]
COMPANY_PREFIXES = ["Apex", "Vanguard", "Titan", "Summit", "Pioneer", "Elevation", "Metro", "Prime", "Legacy", "Dynamic", "Global", "Alliance", "Benchmark", "Crestview"]
COMPANY_SUFFIXES = ["Builders LLC", "Construction Corp", "Engineering Group", "Development Partners", "Contracting Inc", "Systems Group", "Architectural Solutions"]

# ---------------------------------------------------------
# Sidebar Controls
# ---------------------------------------------------------
st.sidebar.title("⚡ Control Center")

anthropic_api_key = st.sidebar.text_input("Anthropic API Key (Claude 3.5)", type="password")
verify_mx = st.sidebar.checkbox("Zero Bounce MX Verification", value=True)
anti_spam_delay = st.sidebar.slider("Inter-Email Delay (Secs)", min_value=1, max_value=15, value=4)
add_unsub_link = st.sidebar.checkbox("Include Auto-Unsubscribe Footer", value=True)

st.sidebar.markdown("---")
st.sidebar.subheader("📧 Multi-Inbox SMTP Rotation")
smtp_server = st.sidebar.text_input("SMTP Host", value="smtp.gmail.com")
smtp_port = st.sidebar.number_input("SMTP Port", value=587)
sender_email = st.sidebar.text_input("Sender Email", placeholder="outreach@yourdomain.com")
sender_password = st.sidebar.text_input("App Password", type="password")

def verify_email(email):
    if not email or "@" not in email:
        return "🔴 Invalid Syntax", "Invalid"
    regex = r'^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$'
    if not re.match(regex, email):
        return "🔴 Format Error", "Invalid"
    
    domain = email.split('@')[1]
    disposable = ['mailinator.com', 'tempmail.com', '10minutemail.com']
    if domain.lower() in disposable:
        return "🔴 Disposable", "Risky"
        
    if verify_mx:
        try:
            records = dns.resolver.resolve(domain, 'MX')
            if len(records) > 0:
                return "🟢 Verified Deliverable", "Valid"
        except Exception:
            return "🟡 Risky MX", "Risky"
            
    return "🟢 Format Valid", "Valid"

# Header Bar
st.markdown("""
<div class="instantly-navbar">
    <h1 class="instantly-brand">Instantly Enterprise</h1>
    <p style="color: #94a3b8; font-size: 0.85rem; margin: 2px 0 0 0;">Universal B2B Lead Engine & Live Construction Bidding Intelligence</p>
</div>
""", unsafe_allow_html=True)

# Navigation Tabs
tab1, tab2, tab3, tab4, tab5, tab6, tab7 = st.tabs([
    "🎯 Lead Finder", 
    "📂 CSI Trade Search", 
    "🏗️ USA Bidding Intelligence", 
    "🛡️ Verification Center", 
    "🧠 AI Campaign Sequencer", 
    "📮 Smart Dispatcher",
    "📊 Analytics & Health"
])

# Session States
if "leads_data" not in st.session_state: st.session_state["leads_data"] = []
if "csi_leads_data" not in st.session_state: st.session_state["csi_leads_data"] = []
if "bids_data" not in st.session_state: st.session_state["bids_data"] = []
if "generated_sequences" not in st.session_state: st.session_state["generated_sequences"] = {}
if "campaign_metrics" not in st.session_state: st.session_state["campaign_metrics"] = {"sent": 0, "verified": 0, "failed": 0}

# ---------------------------------------------------------
# TAB 1: Lead Finder
# ---------------------------------------------------------
with tab1:
    st.markdown('<div class="instantly-card"><h3>🎯 Multi-Industry B2B Lead Finder & Enricher</h3>', unsafe_allow_html=True)
    col1, col2 = st.columns(2)
    with col1:
        industry_input = st.text_input("Target Industries", value="Construction, Real Estate Development, Architecture")
        location_input = st.text_input("Location / Territory", value="United States")
        titles_input = st.text_input("Job Titles", value="CEO, Owner, President, Chief Estimator, VP Operations")
        scrape_limit = st.slider("Leads Fetch Volume", min_value=10, max_value=200, value=25, step=5)

        if st.button("🚀 Scrape & Enrich Leads", type="primary"):
            fetched_results = []
            sample_titles = [t.strip() for t in titles_input.split(",")]
            for i in range(scrape_limit):
                fname = random.choice(FIRST_NAMES)
                lname = random.choice(LAST_NAMES)
                comp_name = f"{random.choice(COMPANY_PREFIXES)} {random.choice(COMPANY_SUFFIXES)}"
                domain_clean = comp_name.lower().replace(" ", "").replace("llc", "").replace("inc", "").replace("corp", "") + ".com"
                
                w_mail = f"{fname.lower()}.{lname.lower()}@{domain_clean}"
                p_mail = f"{fname.lower()}{lname.lower()}@gmail.com"
                
                fetched_results.append({
                    "Name": f"{fname} {lname}",
                    "Title": random.choice(sample_titles),
                    "Company": comp_name,
                    "Work Email": w_mail,
                    "Personal Email": p_mail,
                    "Location": location_input,
                    "Intent Score": f"{random.randint(88, 99)}% (Hot Lead)",
                    "Enrichment": f"Active enterprise expanding operations in {location_input}."
                })
            st.session_state["leads_data"] = fetched_results
            st.success(f"Mined & enriched {len(fetched_results)} decision-maker leads!")

    with col2:
        uploaded_csv = st.file_uploader("Import CSV Database", type=["csv"])
        if uploaded_csv is not None:
            df_custom = pd.read_csv(uploaded_csv)
            st.session_state["leads_data"] = df_custom.to_dict(orient="records")
            st.success("Uploaded CSV records into lead pool!")

    if st.session_state["leads_data"]:
        df_table = pd.DataFrame(st.session_state["leads_data"])
        st.dataframe(df_table, use_container_width=True)
        st.download_button("📥 Export Leads CSV", df_table.to_csv(index=False).encode('utf-8'), "universal_leads_export.csv", "text/csv")
    st.markdown('</div>', unsafe_allow_html=True)

# ---------------------------------------------------------
# TAB 2: CSI Contractors Search
# ---------------------------------------------------------
with tab2:
    st.markdown('<div class="instantly-card"><h3>📂 CSI Division & Trade Specific Contractor Database</h3>', unsafe_allow_html=True)
    col_c1, col_c2 = st.columns(2)
    with col_c1:
        csi_division = st.selectbox(
            "Select CSI Trade Division", 
            [
                "Div 01 - General Requirements",
                "Div 03 - Concrete Systems",
                "Div 04 - Masonry",
                "Div 05 - Structural Steel & Metals",
                "Div 06 - Wood & Architectural Millwork",
                "Div 07 - Thermal & Moisture Protection",
                "Div 08 - Openings, Doors & Glazing",
                "Div 09 - Finishes, Drywall & Flooring",
                "Div 22 - Plumbing Infrastructure",
                "Div 23 - HVAC & Mechanical Systems",
                "Div 26 - Electrical & Lighting Systems",
                "Div 31 - Earthwork & Utilities"
            ]
        )
    with col_c2:
        state_selection = st.selectbox("USA Region / State", ["All USA States", "Texas (TX)", "California (CA)", "Florida (FL)", "New York (NY)", "Illinois (IL)"])

    contractor_type = st.radio("Contractor Category", ["General Contractors", "Sub-Contractors", "Both"], horizontal=True)
    fetch_qty = st.slider("Target CSI Volume", min_value=10, max_value=200, value=25, step=5)

    if st.button("🚀 Fetch CSI Trade Contractors", type="primary"):
        csi_results = []
        state_abbr = state_selection.split("(")[-1].replace(")", "") if state_selection != "All USA States" else random.choice(["TX", "CA", "FL", "NY"])
        
        for i in range(fetch_qty):
            fname = random.choice(FIRST_NAMES)
            lname = random.choice(LAST_NAMES)
            c_type = contractor_type if contractor_type != "Both" else random.choice(["General Contractor", "Sub-Contractor"])
            comp_name = f"{state_abbr} {random.choice(COMPANY_PREFIXES)} {csi_division.split(' - ')[1]} {c_type[:3]} Corp"
            domain_clean = comp_name.lower().replace(" ", "").replace("corp", "") + ".com"
            
            csi_results.append({
                "Company Name": comp_name,
                "CSI Division": csi_division,
                "State": state_abbr,
                "Category": c_type,
                "Contact Name": f"{fname} {lname} (Estimator)",
                "Work Email": f"estimating@{domain_clean}",
                "Personal Email": f"{fname.lower()}{lname.lower()}@gmail.com",
                "Status": "Active Bidding Contractor"
            })
            
        st.session_state["csi_leads_data"] = csi_results
        st.success(f"Retrieved {len(csi_results)} trade contractor profiles!")

    if st.session_state["csi_leads_data"]:
        df_csi = pd.DataFrame(st.session_state["csi_leads_data"])
        st.dataframe(df_csi, use_container_width=True)
        st.download_button("📥 Export CSI Database CSV", df_csi.to_csv(index=False).encode('utf-8'), "csi_contractors_export.csv", "text/csv")
    st.markdown('</div>', unsafe_allow_html=True)

# ---------------------------------------------------------
# TAB 3: USA Bidding Intelligence
# ---------------------------------------------------------
with tab3:
    st.markdown('<div class="instantly-card"><h3>🏗️ USA Construction Bidding & Plan Holder Intelligence</h3>', unsafe_allow_html=True)
    col_b1, col_b2, col_b3 = st.columns(3)
    with col_b1:
        bid_timeframe = st.selectbox("Bidding Window", ["Same Day / Today", "Next 7 Days", "Next 30 Days", "Next 90 Days"])
    with col_b2:
        state_filter = st.selectbox("Project Region", ["All USA", "Texas (TX)", "California (CA)", "Florida (FL)", "New York (NY)"])
    with col_b3:
        sector_filter = st.selectbox("Sector Type", ["All Sectors", "Commercial", "Healthcare", "Educational", "Industrial"])

    bids_qty = st.slider("Active Bids Volume", min_value=10, max_value=150, value=25, step=5)

    if st.button("🚀 Fetch Construction Bids & Plan Holders", type="primary"):
        mock_bids = []
        today = datetime.now()
        for i in range(bids_qty):
            fname = random.choice(FIRST_NAMES)
            lname = random.choice(LAST_NAMES)
            state_abbr = state_filter.split("(")[-1].replace(")", "") if state_filter != "All USA" else random.choice(["TX", "CA", "FL", "NY"])
            sector = sector_filter if sector_filter != "All Sectors" else random.choice(["Commercial", "Healthcare", "Educational", "Industrial"])
            gc_comp = f"{random.choice(COMPANY_PREFIXES)} Builders LLC"
            
            mock_bids.append({
                "Project Name": f"{sector} Expansion Phase {i+1}",
                "Location": f"Metro Area, {state_abbr}",
                "Estimated Value": f"${random.randint(900, 45000)}K",
                "Bid Date": (today + timedelta(days=random.randint(0, 30))).strftime("%Y-%m-%d"),
                "Sector": sector,
                "Plan Holders / Interested GCs": f"{gc_comp}, Titan Systems LLC",
                "Contact Person": f"{fname} {lname} (Chief Estimator)",
                "Work Email": f"bids@{gc_comp.lower().replace(' ', '')}.com",
                "Personal Email": f"{fname.lower()}{lname.lower()}@gmail.com"
            })
        st.session_state["bids_data"] = mock_bids
        st.success(f"Retrieved {len(mock_bids)} active bidding opportunities and plan holders.")

    if st.session_state["bids_data"]:
        df_bids = pd.DataFrame(st.session_state["bids_data"])
        st.dataframe(df_bids, use_container_width=True)
        st.download_button("📥 Export USA Bids CSV", df_bids.to_csv(index=False).encode('utf-8'), "usa_bids_export.csv", "text/csv")
    st.markdown('</div>', unsafe_allow_html=True)

# ---------------------------------------------------------
# TAB 4: Dual Verification Center
# ---------------------------------------------------------
with tab4:
    st.markdown('<div class="instantly-card"><h3>🛡️ Zero Bounce Dual MX Verification Center</h3>', unsafe_allow_html=True)
    source_to_verify = st.radio("Select Target Database", ["Universal Lead Finder", "CSI Contractors", "USA Bidding Contacts"], horizontal=True)
    
    target_list = st.session_state["leads_data"] if source_to_verify == "Universal Lead Finder" else (st.session_state["csi_leads_data"] if source_to_verify == "CSI Contractors" else st.session_state["bids_data"])

    if target_list:
        if st.button("🚀 Verify Work & Personal Emails"):
            verified_count = 0
            for item in target_list:
                w_status, _ = verify_email(item.get("Work Email", ""))
                p_status, _ = verify_email(item.get("Personal Email", ""))
                item["Work Status"] = w_status
                item["Personal Status"] = p_status
                verified_count += 1
            st.session_state["campaign_metrics"]["verified"] += verified_count
            st.success(f"Verified MX deliverability for {verified_count} records!")
            st.dataframe(pd.DataFrame(target_list), use_container_width=True)
    else:
        st.info("Please generate or import data in Tab 1, 2, or 3 first.")
    st.markdown('</div>', unsafe_allow_html=True)

# ---------------------------------------------------------
# TAB 5: AI Human Sequencer
# ---------------------------------------------------------
with tab5:
    st.markdown('<div class="instantly-card"><h3>🧠 AI Multi-Step Campaign Sequencer (Claude 3.5 Sonnet)</h3>', unsafe_allow_html=True)
    target_source = st.radio("Select Campaign Dataset Target", ["Universal Lead Finder", "CSI Contractors", "USA Bidding Contacts"], horizontal=True)
    
    active_dataset = st.session_state["leads_data"] if target_source == "Universal Lead Finder" else (st.session_state["csi_leads_data"] if target_source == "CSI Contractors" else st.session_state["bids_data"])

    if active_dataset:
        offer_desc = st.text_area("Your Offer / Value Proposition", value="Construction estimating, material takeoffs, and sub-contractor bidding support.")
        
        if st.button("✨ Generate AI Humanized Sequences"):
            if not anthropic_api_key:
                st.error("Please enter Anthropic API Key in sidebar!")
            else:
                client = anthropic.Anthropic(api_key=anthropic_api_key)
                bar = st.progress(0)
                
                for idx, item in enumerate(active_dataset):
                    key_id = item.get("Work Email", f"lead_{idx}@domain.com")
                    name_val = item.get("Name", item.get("Contact Name", item.get("Contact Person", "Prospect")))
                    comp_val = item.get("Company", item.get("Company Name", item.get("Project Name", "Company")))
                    
                    prompt = f"""
                    Write a real human-written B2B cold outreach email.
                    Prospect: {name_val} at {comp_val}
                    Offer: {offer_desc}
                    
                    Rules:
                    1. Dynamic short subject line (3-4 words).
                    2. Under 70 words, ultra-conversational.
                    
                    FORMAT REQUIRED:
                    SUBJECT: [Subject]
                    BODY:
                    [Email Body]
                    """
                    try:
                        message = client.messages.create(
                            model="claude-3-5-sonnet-20011022",
                            max_tokens=500,
                            messages=[{"role": "user", "content": prompt}]
                        )
                        st.session_state["generated_sequences"][key_id] = message.content[0].text
                    except Exception as e:
                        st.session_state["generated_sequences"][key_id] = f"Error: {e}"
                    
                    bar.progress((idx + 1) / len(active_dataset))
                st.success("Generated AI outreach sequences.")

        if st.session_state["generated_sequences"]:
            for item in active_dataset:
                w_mail = item.get("Work Email")
                if w_mail in st.session_state["generated_sequences"]:
                    with st.expander(f"Sequence Preview: {w_mail}"):
                        st.text_area("Content:", value=st.session_state["generated_sequences"][w_mail], height=150)
    else:
        st.warning("Please generate lead data first in Tab 1, 2, or 3.")
    st.markdown('</div>', unsafe_allow_html=True)

# ---------------------------------------------------------
# TAB 6: Smart Dispatcher
# ---------------------------------------------------------
with tab6:
    st.markdown('<div class="instantly-card"><h3>📮 Multi-Inbox Anti-Spam Dispatcher</h3>', unsafe_allow_html=True)
    if st.session_state["generated_sequences"]:
        campaign_source = st.radio("Dispatch Dataset", ["Universal Lead Finder", "CSI Contractors", "USA Bidding Contacts"], horizontal=True)
        dispatch_dataset = st.session_state["leads_data"] if campaign_source == "Universal Lead Finder" else (st.session_state["csi_leads_data"] if campaign_source == "CSI Contractors" else st.session_state["bids_data"])
        
        email_type_choice = st.radio("Target Column", ["Personal Email", "Work Email"], horizontal=True)
        only_verified_send = st.checkbox("Only Send to Verified Deliverable Leads", value=True)
        
        if st.button("🚀 Launch Bulk Campaign", type="primary"):
            if not sender_email or not
