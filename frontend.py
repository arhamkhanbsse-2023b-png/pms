import streamlit as st
import requests
import time

# --- CONFIG ---
st.set_page_config(page_title="Park-O-Matic Pro", layout="wide")

API_URL = "http://127.0.0.1:5000"

# --- STATE ---
if 'user_id' not in st.session_state: st.session_state.user_id = None
if 'username' not in st.session_state: st.session_state.username = None
if 'page' not in st.session_state: st.session_state.page = 'home'

# --- CSS STYLES ---
st.markdown("""
<style>
    /* VARIABLES */
    :root { --gold: #FFD700; --dark: #000; --card: #1a1a1a; }
    
    /* GLOBAL */
    .stApp { background-color: var(--dark); color: white; }
    h1, h2, h3 { color: white !important; }
    
    /* NAVBAR-ISH */
    .nav-btn { width: 100%; border: 1px solid var(--gold); background: transparent; color: var(--gold); }
    .nav-btn:hover { background: var(--gold); color: black; }

    /* STREAMLIT BUTTON OVERRIDES */
    div.stButton > button {
        background-color: var(--card);
        color: var(--gold);
        border: 1px solid var(--gold);
        width: 100%;
        transition: all 0.3s ease;
    }
    div.stButton > button:hover {
        background-color: var(--gold);
        color: black;
        border-color: var(--gold);
        transform: scale(1.02);
    }
    div.stButton > button:active {
        background-color: white;
        color: black;
    }
    div[data-testid="stForm"] { border: 1px solid var(--gold); padding: 2rem; border-radius: 10px; }
    
    /* HERO */
    .hero { 
        padding: 5rem 2rem; 
        background: linear-gradient(rgba(0,0,0,0.7), rgba(0,0,0,0.9)), url('https://images.unsplash.com/photo-1470224114660-3f6686c562eb?q=80&w=2070&auto=format&fit=crop'); 
        background-size: cover; 
        border-radius: 10px;
        text-align: center;
        margin-bottom: 2rem;
    }
    .hero h1 { font-size: 3rem; margin-bottom: 0.5rem; }
    .gold-text { color: var(--gold); }
    
    /* SLOTS */
    .slot-card {
        background-color: var(--card);
        padding: 1.5rem;
        border-radius: 10px;
        border: 1px solid #333;
        text-align: center;
        transition: 0.3s;
        height: 250px;
        display: flex;
        flex-direction: column;
        justify-content: space-between;
    }
    .slot-card:hover { border-color: var(--gold); transform: translateY(-5px); }
    .slot-card.AVAILABLE { border-bottom: 3px solid #0f0; }
    .slot-card.OCCUPIED { border-bottom: 3px solid #f00; background: #220000; }
    .slot-card.RESERVED { border-bottom: 3px solid orange; }
    .slot-card.UNAVAILABLE { border-bottom: 3px solid grey; opacity: 0.6; }
    
    .status-badge { 
        display: inline-block; padding: 2px 8px; border-radius: 4px; font-size: 0.8rem; font-weight: bold; margin-top: 5px;
    }
    .AVAILABLE .status-badge { background: rgba(0,255,0,0.2); color: #0f0; }
    .OCCUPIED .status-badge { background: rgba(255,0,0,0.2); color: #f00; }
    
    .icon { font-size: 3rem; color: #555; }
    .OCCUPIED .icon { color: var(--gold); }

    /* LOYALTY */
    .loyalty-box { border: 1px solid var(--gold); padding: 1rem; border-radius: 8px; text-align: center; margin-bottom: 1rem; }
    .wash-reward { color: var(--gold); animation: pulse 1s infinite; font-weight: bold; }
    @keyframes pulse { 0% { opacity: 0.5; } 100% { opacity: 1; } }

</style>
""", unsafe_allow_html=True)

# --- NAVIGATION ---
def nav():
    col1, col2, col3, col4, col5 = st.columns([2, 1, 1, 1, 1])
    with col1: st.write("### 🅿️ PARK-O-MATIC")
    with col2: 
        if st.button("Home"): st.session_state.page = 'home'
    with col3: 
        if st.button("About"): st.session_state.page = 'about'
    with col4: 
        if st.session_state.user_id:
             if st.button("Dashboard"): st.session_state.page = 'dashboard'
        else:
             if st.button("Sign In"): st.session_state.page = 'auth'
    with col5:
        if st.session_state.user_id:
            if st.button("Logout"): 
                st.session_state.user_id = None
                st.session_state.page = 'home'
                st.rerun()

nav()
st.divider()

# --- PAGES ---

if st.session_state.page == 'home':
    st.markdown("""
        <div class="hero">
            <h1>Welcome to <span class="gold-text">EASY PARK</span></h1>
            <p>Premium Parking Management. Rewarding & Secure.</p>
        </div>
    """, unsafe_allow_html=True)
    
    c1, c2, c3 = st.columns(3)
    c1.info("🛡️ **Fully Insured** by SecureSafe Ltd.")
    c2.warning("🎁 **Loyalty Rewards**: Free Car Wash every 6th Park!")
    c3.success("📍 **Prime Locations**: Hayatabad, Saddar, Cantt.")
    
    if st.button("BOOK NOW", use_container_width=True, type="primary"):
        st.session_state.page = 'auth' if not st.session_state.user_id else 'dashboard'
        st.rerun()

elif st.session_state.page == 'about':
    st.title("About & Insurance Policy")
    st.markdown("""
    ### Partners with SecureSafe Insurance Ltd.
    Policy Number: **PK-99-SECURE**
    
    We guarantee the safety of your vehicle. Any theft or fire damage incurred while parked in valid Park-O-Matic slots is covered up to **100% of market value**.
    
    **Our Mission**: To automate urban mobility with style.
    """)
    
    st.write("### Contact Us")
    st.text_input("Name")
    st.text_area("Message")
    st.slider("Rate Us", 1, 5, 5)
    st.button("Send Feedback")

elif st.session_state.page == 'auth':
    tab1, tab2 = st.tabs(["Login", "Sign Up"])
    
    with tab1:
        u = st.text_input("Username", key="l_u")
        p = st.text_input("Password", type="password", key="l_p")
        if st.button("Login"):
            try:
                r = requests.post(f"{API_URL}/login", json={'username': u, 'password': p})
                if r.json()['success']:
                    data = r.json()
                    st.session_state.user_id = data['user_id']
                    st.session_state.username = data['username']
                    st.session_state.page = 'dashboard'
                    st.rerun()
                else:
                    st.error("Invalid Credentials")
            except Exception as e:
                st.error(f"Backend Error: {e}")

    with tab2:
        su = st.text_input("Choose Username", key="s_u")
        sp = st.text_input("Choose Password", type="password", key="s_p")
        if st.button("Create Account"):
            try:
                r = requests.post(f"{API_URL}/signup", json={'username': su, 'password': sp})
                if r.json().get('success'):
                    st.success("Account created! Please Login.")
                else:
                    st.error("Username taken.")
            except Exception as e:
                st.error(f"Backend Error: {e}")

elif st.session_state.page == 'dashboard':
    st.title(f"Dashboard - {st.session_state.username}")
    
    # Sidebar features
    with st.sidebar:
        st.header("Loyalty Tracker")
        try:
            # Refresh user count
            user_info = requests.get(f"{API_URL}/get_user_info", params={'user_id': st.session_state.user_id}).json()
            count = user_info['parking_count']
        except Exception as e:
            st.error(f"Loyalty Error: {e}")
            count = 0
            
        st.progress(min(count/5, 1.0))
        st.write(f"**{count} / 5 Parks**")
        if count >= 5:
            st.markdown('<div class="wash-reward">✨ FREE CAR WASH AVAILABLE!</div>', unsafe_allow_html=True)
            if st.button("Redeem Reward"):
                st.toast("Show this code at exit: WASH-FREE-777")
        
        st.divider()
        st.header("Park Vehicle")
        plate = st.text_input("Plate Number")
        model = st.text_input("Car Model")
        
        # Area Filter
        area = st.selectbox("Filter Area", ["All", "Hayatabad", "University Road", "Saddar", "Cantt"])
    
    # Main Grid
    try:
        slots = requests.get(f"{API_URL}/status", params={'area': area}).json()
        
        # For selection in sidebar
        avail_slots = [s['slot_id'] for s in slots if s['status'] == 'AVAILABLE']
        with st.sidebar:
            selected_slot = st.selectbox("Select Slot", avail_slots if avail_slots else ["None"])
            if st.button("Park Now", type="primary"):
                if plate and selected_slot != "None":
                    requests.post(f"{API_URL}/park", json={
                        'plate': plate, 'model': model, 'slot': selected_slot, 'user_id': st.session_state.user_id
                    })
                    st.success("Parked!")
                    time.sleep(1)
                    st.rerun()
    
        # Render Grid
        cols = st.columns(4)
        for i, slot in enumerate(slots):
            with cols[i % 4]:
                # Card HTML
                status = slot['status']
                plate_display = slot['plate'] if slot.get('plate') else "---"
                car = f"<div>{plate_display}</div>" if status == 'OCCUPIED' else ""
                
                st.markdown(f"""
                <div class="slot-card {status}">
                    <div><b>{slot['slot_id']}</b><br><small>{slot['area']}</small></div>
                    <div class="icon">🚗</div>
                    <div><span class="status-badge">{status}</span>{car}</div>
                </div>
                """, unsafe_allow_html=True)
                
                # Popover Menu
                with st.popover("⋮"):
                    st.write(f"**Manage {slot['slot_id']}**")
                    if st.button("Mark Available", key=f"a_{slot['slot_id']}", use_container_width=True):
                        requests.post(f"{API_URL}/update_status", json={'slot_id': slot['slot_id'], 'status': 'AVAILABLE'})
                        st.rerun()
                    if st.button("Mark Reserved", key=f"r_{slot['slot_id']}", use_container_width=True):
                        requests.post(f"{API_URL}/update_status", json={'slot_id': slot['slot_id'], 'status': 'RESERVED'})
                        st.rerun()
                    if st.button("Mark Unavailable", key=f"u_{slot['slot_id']}", use_container_width=True):
                         requests.post(f"{API_URL}/update_status", json={'slot_id': slot['slot_id'], 'status': 'UNAVAILABLE'})
                         st.rerun()
                    if st.button("Mark Occupied", key=f"o_{slot['slot_id']}", use_container_width=True):
                         requests.post(f"{API_URL}/update_status", json={'slot_id': slot['slot_id'], 'status': 'OCCUPIED'})
                         st.rerun()

    except Exception as e:
        st.error(f"Error connecting to backend: {e}")
        
    # Auto-refresh logic (crudely)
    time.sleep(2)
    st.rerun()
