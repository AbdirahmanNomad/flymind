import streamlit as st
import requests
import json
import re
from datetime import datetime, timedelta

def parse_price(price_str):
    """Parse price string with various whitespace and currency formats"""
    if not price_str:
        return 0
    # Remove currency symbols and normalize whitespace
    clean_price = re.sub(r'[^\d,.\s]', '', price_str)
    # Remove all whitespace (including non-breaking spaces)
    clean_price = re.sub(r'\s+', '', clean_price)
    # Remove commas and convert to float
    return float(clean_price.replace(',', '')) if clean_price else 0

# Configure page
st.set_page_config(
    page_title="FlyMind - AI-Powered Flight Analytics",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for better branding
st.markdown("""
<style>
    .main-header {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        padding: 2rem;
        border-radius: 15px;
        color: white;
        text-align: center;
        margin-bottom: 2rem;
        box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
    }
    .main-title {
        font-size: 3rem;
        font-weight: bold;
        margin-bottom: 0.5rem;
        text-shadow: 2px 2px 4px rgba(0,0,0,0.3);
    }
    .subtitle {
        font-size: 1.2rem;
        opacity: 0.9;
        margin-bottom: 1rem;
    }
    .feature-card {
        background: white;
        padding: 1.5rem;
        border-radius: 10px;
        box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
        border-left: 4px solid #667eea;
        margin-bottom: 1rem;
    }
    .status-indicator {
        display: inline-block;
        padding: 0.25rem 0.75rem;
        border-radius: 20px;
        font-size: 0.8rem;
        font-weight: bold;
        text-transform: uppercase;
    }
    .status-healthy {
        background: #d4edda;
        color: #155724;
        border: 1px solid #c3e6cb;
    }
    .status-error {
        background: #f8d7da;
        color: #721c24;
        border: 1px solid #f5c6cb;
    }
    .metric-card {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        padding: 1rem;
        border-radius: 10px;
        text-align: center;
        box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
    }
    .metric-value {
        font-size: 2rem;
        font-weight: bold;
        margin-bottom: 0.25rem;
    }
    .metric-label {
        font-size: 0.9rem;
        opacity: 0.9;
    }
    .sidebar-header {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        padding: 1rem;
        border-radius: 10px;
        margin-bottom: 1rem;
        text-align: center;
    }
    .sidebar-title {
        font-size: 1.5rem;
        font-weight: bold;
        margin-bottom: 0.5rem;
    }
    .sidebar-subtitle {
        font-size: 0.9rem;
        opacity: 0.8;
    }
</style>
""", unsafe_allow_html=True)

# Main Header
st.markdown("""
<div class="main-header">
    <div class="main-title">🧠 FlyMind</div>
    <div class="subtitle">AI-Powered Flight Analytics & Automation Suite</div>
    <div style="font-size: 0.9rem; opacity: 0.8;">
        🚀 Intelligent Flight Search • 🤖 AI Automation • ⚡ Real-Time Analytics
    </div>
</div>
""", unsafe_allow_html=True)

# Add title and caption for better SEO and branding
st.title("FlyMind – AI-Powered Flight Analytics")
st.caption("Smart flight search, monitoring, and automation.")

# Feature highlights
col1, col2, col3, col4 = st.columns(4)
with col1:
    st.markdown("""
    <div class="feature-card">
        <h4>🌍 Global Coverage</h4>
        <p>Search flights worldwide with city name support</p>
    </div>
    """, unsafe_allow_html=True)

with col2:
    st.markdown("""
    <div class="feature-card">
        <h4>⚡ Real-time Data</h4>
        <p>Live Google Flights data with instant results</p>
    </div>
    """, unsafe_allow_html=True)

with col3:
    st.markdown("""
    <div class="feature-card">
        <h4>🤖 AI Integration</h4>
        <p>Perfect for n8n workflows and automation</p>
    </div>
    """, unsafe_allow_html=True)

with col4:
    st.markdown("""
    <div class="feature-card">
        <h4>💰 Price Alerts</h4>
        <p>Monitor fares and get notified of deals</p>
    </div>
    """, unsafe_allow_html=True)

# Sidebar with branding
st.sidebar.markdown("""
<div class="sidebar-header">
    <div class="sidebar-title">⚙️ Configuration</div>
    <div class="sidebar-subtitle">API Connection Settings</div>
</div>
""", unsafe_allow_html=True)

# API Configuration
API_BASE_URL = st.sidebar.text_input("API Base URL", "http://localhost:8001", help="URL of your Google Flights API server")

# API Health Status
st.sidebar.markdown("### 🔍 API Status")
health_placeholder = st.sidebar.empty()

if st.sidebar.button("🔄 Check API Health"):
    try:
        response = requests.get(f"{API_BASE_URL}/health", timeout=5)
        if response.status_code == 200:
            health_placeholder.markdown("""
            <div style="display: inline-block; padding: 0.25rem 0.75rem; border-radius: 20px; font-size: 0.8rem; font-weight: bold; background: #d4edda; color: #155724; border: 1px solid #c3e6cb;">
                ✅ HEALTHY
            </div>
            """, unsafe_allow_html=True)
        else:
            health_placeholder.markdown("""
            <div style="display: inline-block; padding: 0.25rem 0.75rem; border-radius: 20px; font-size: 0.8rem; font-weight: bold; background: #f8d7da; color: #721c24; border: 1px solid #f5c6cb;">
                ❌ UNHEALTHY
            </div>
            """, unsafe_allow_html=True)
    except Exception as e:
        health_placeholder.markdown("""
        <div style="display: inline-block; padding: 0.25rem 0.75rem; border-radius: 20px; font-size: 0.8rem; font-weight: bold; background: #f8d7da; color: #721c24; border: 1px solid #f5c6cb;">
            ❌ OFFLINE
        </div>
        """, unsafe_allow_html=True)

st.sidebar.markdown("---")
st.sidebar.markdown("### 📊 Quick Stats")
st.sidebar.markdown("**API Version:** 2.0.0")
st.sidebar.markdown("**Status:** 🟢 Operational")
st.sidebar.markdown("**Environment:** Development")

# Test Health Check
st.header("🏥 Health Check")
if st.button("Test Health Check"):
    try:
        response = requests.get(f"{API_BASE_URL}/health")
        if response.status_code == 200:
            st.success("✅ API is healthy!")
            st.json(response.json())
        else:
            st.error(f"❌ Health check failed: {response.status_code}")
    except Exception as e:
        st.error(f"❌ Connection failed: {str(e)}")

# Flight Search
st.header("✈️ Advanced Flight Search")
st.markdown("Search flights with detailed options and full city names")

# Trip Type Selection
trip_type = st.radio("Trip Type", ["One Way", "Round Trip", "Multi City"], horizontal=True)

col1, col2, col3 = st.columns(3)

with col1:
    origin = st.text_input("From (City or Airport)", "New York", placeholder="e.g., London, Paris, JFK")
    destination = st.text_input("To (City or Airport)", "Los Angeles", placeholder="e.g., London, Paris, LAX")

with col2:
    depart_date = st.date_input("Departure Date", datetime.now() + timedelta(days=7))
    if trip_type == "Round Trip":
        return_date = st.date_input("Return Date", datetime.now() + timedelta(days=14))
    else:
        return_date = None

with col3:
    adults = st.number_input("Passengers", 1, 10, 1)
    seat_class = st.selectbox("Class", ["economy", "premium_economy", "business", "first"], index=0)

# Advanced Options
with st.expander("🔧 Advanced Options"):
    col_adv1, col_adv2, col_adv3 = st.columns(3)
    with col_adv1:
        max_stops = st.selectbox("Max Stops", ["any", "nonstop", "1", "2"], index=0)
        sort_by = st.selectbox("Sort By", ["price", "duration", "stops", "best"], index=0, help="Sort flights by: price (cheapest first), duration (fastest first), stops (fewest first), or best (recommended)")
    with col_adv2:
        airlines = st.multiselect("Preferred Airlines", ["Any", "American", "Delta", "United", "Lufthansa", "British Airways"], default=["Any"])
        fetch_mode = st.selectbox("Search Mode", ["local", "remote"], index=0)
    with col_adv3:
        currency = st.selectbox("Currency", ["USD", "EUR", "GBP", "SEK"], index=0)

if st.button("🔍 Search Flights"):
    # Convert max_stops from string to int or None
    max_stops_int = None
    if max_stops == "nonstop":
        max_stops_int = 0
    elif max_stops.isdigit():
        max_stops_int = int(max_stops)

    payload = {
        "origin": origin,
        "destination": destination,
        "depart_date": depart_date.strftime("%Y-%m-%d"),
        "adults": adults,
        "fetch_mode": fetch_mode,
        "max_stops": max_stops_int
    }

    try:
        response = requests.post(f"{API_BASE_URL}/search", json=payload)
        if response.status_code == 200:
            data = response.json()
            st.success(f"✅ Found {data.get('total_flights', 0)} flights!")

            # Display results
            if data.get('flights'):
                st.subheader("✈️ Detailed Flight Results")

                # Summary stats
                total_flights = len(data['flights'])

                def parse_price(price_str):
                    """Parse price string with various whitespace and currency formats"""
                    if not price_str:
                        return 0
                    # Remove currency symbols and normalize whitespace
                    clean_price = re.sub(r'[^\d,.\s]', '', price_str)
                    # Remove all whitespace (including non-breaking spaces)
                    clean_price = re.sub(r'\s+', '', clean_price)
                    # Remove commas and convert to float
                    return float(clean_price.replace(',', '')) if clean_price else 0

                # Filter out flights with invalid prices (0 or empty)
                valid_flights = [f for f in data['flights'] if f.get('price') and parse_price(f['price']) > 0]

                # Sort flights based on user selection
                def parse_duration(duration_str):
                    """Parse duration string like '2 hr 30 min' to minutes"""
                    if not duration_str:
                        return 0
                    hours = 0
                    minutes = 0
                    # Extract hours
                    hour_match = re.search(r'(\d+)\s*hr', duration_str.lower())
                    if hour_match:
                        hours = int(hour_match.group(1))
                    # Extract minutes
                    min_match = re.search(r'(\d+)\s*min', duration_str.lower())
                    if min_match:
                        minutes = int(min_match.group(1))
                    return hours * 60 + minutes

                if sort_by == "price":
                    valid_flights.sort(key=lambda x: parse_price(x['price']))
                elif sort_by == "duration":
                    valid_flights.sort(key=lambda x: parse_duration(x.get('duration', '')))
                elif sort_by == "stops":
                    valid_flights.sort(key=lambda x: x.get('stops', 0))
                elif sort_by == "best":
                    # Best: balance of price and duration (lower is better)
                    valid_flights.sort(key=lambda x: parse_price(x['price']) + parse_duration(x.get('duration', '')) * 0.1)

                prices = [parse_price(f['price']) for f in valid_flights]
                avg_price = sum(prices) / len(prices) if prices else 0
                min_price = min(prices) if prices else 0

                col_stats1, col_stats2, col_stats3 = st.columns(3)
                with col_stats1:
                    st.metric("Total Flights", total_flights)
                with col_stats2:
                    st.metric("Average Price", f"SEK {avg_price:.0f}")
                with col_stats3:
                    st.metric("Lowest Price", f"SEK {min_price:.0f}")

                # Show sorted flights with detailed info
                for i, flight in enumerate(valid_flights[:20]):  # Show first 20
                    price_num = parse_price(flight['price'])

                    # Color coding for prices
                    if price_num <= min_price * 1.1:
                        price_color = "🟢"  # Cheap
                    elif price_num <= avg_price * 1.2:
                        price_color = "🟡"  # Average
                    else:
                        price_color = "🔴"  # Expensive

                    with st.expander(f"{price_color} {flight['name']} - {flight['price']} ({flight['duration']})"):
                        # Flight details in columns
                        col_detail1, col_detail2 = st.columns(2)

                        with col_detail1:
                            st.markdown("**🛫 Departure**")
                            st.write(f"**Time:** {flight['departure']}")
                            st.write(f"**From:** {origin}")

                            st.markdown("**🛬 Arrival**")
                            st.write(f"**Time:** {flight['arrival']}")
                            st.write(f"**To:** {destination}")

                        with col_detail2:
                            st.markdown("**📊 Flight Details**")
                            st.write(f"**Duration:** {flight['duration']}")
                            st.write(f"**Stops:** {flight['stops']}")
                            st.write(f"**Class:** {seat_class.title()}")
                            if flight.get('delay'):
                                st.write(f"**⚠️ Delay:** {flight['delay']}")

                            # Show layover information if available
                            if flight.get('layovers') and len(flight['layovers']) > 0:
                                st.markdown("**🛑 Layovers**")
                                for i, layover in enumerate(flight['layovers'], 1):
                                    st.write(f"**Stop {i}:** {layover}")
                            elif flight['stops'] > 0:
                                # Simple stop count display
                                st.markdown("**🛑 Layovers**")
                                if flight['stops'] == 1:
                                    st.write("**1 stop**")
                                elif flight['stops'] == 2:
                                    st.write("**2 stops**")
                                else:
                                    st.write(f"**{flight['stops']} stops**")

                            st.markdown("**💰 Pricing**")
                            st.write(f"**Price:** {flight['price']}")
                            st.write(f"**Per Person:** {flight['price']}")

                            # Show additional flight information if available
                            if flight.get('additional_info') and len(flight['additional_info']) > 0:
                                st.markdown("**ℹ️ Additional Details**")
                                for info in flight['additional_info'][:3]:  # Show first 3 items
                                    st.write(f"• {info}")

                        # Additional info
                        if i < 5:  # Show booking link for first 5 results
                            st.markdown("---")
                            st.markdown(f"**🔗 Search URL:** [View on Google Flights]({data.get('search_url', '#')})")
        else:
            st.error(f"❌ Search failed: {response.status_code}")
            st.text(response.text)
    except Exception as e:
        st.error(f"❌ Connection failed: {str(e)}")

# Price Alerts
st.header("💰 Price Alerts")

# Trip type selection for alerts
alert_trip_type = st.radio("Trip Type", ["One Way", "Round Trip"], horizontal=True, key="alert_trip_type")

alert_col1, alert_col2, alert_col3 = st.columns(3)

with alert_col1:
    alert_origin = st.text_input("From (City or Airport)", "New York", key="alert_origin", placeholder="e.g., London, Paris, JFK")
    alert_destination = st.text_input("To (City or Airport)", "London", key="alert_destination", placeholder="e.g., London, Paris, LHR")
    alert_currency = st.selectbox("Currency", ["SEK", "USD", "EUR", "GBP"], index=0, key="alert_currency")

with alert_col2:
    alert_depart_date = st.date_input("Departure Date", datetime.now() + timedelta(days=30), key="alert_depart_date")
    if alert_trip_type == "Round Trip":
        alert_return_date = st.date_input("Return Date", datetime.now() + timedelta(days=37), key="alert_return_date")
    else:
        alert_return_date = None
    target_price = st.number_input(f"Target Price ({alert_currency})", 100, 50000, 3000, key="target_price")

with alert_col3:
    email = st.text_input("Email for Notifications", "user@example.com", key="alert_email")
    notification_channels = st.multiselect("Notification Channels", ["email", "webhook"], default=["email"], key="notification_channels")

if st.button("🔔 Create Price Alert"):
    # Convert trip type to API format
    trip_type_api = "one-way" if alert_trip_type == "One Way" else "round-trip"

    payload = {
        "trip_type": trip_type_api,
        "origin": alert_origin,
        "destination": alert_destination,
        "depart_date": alert_depart_date.strftime("%Y-%m-%d"),
        "return_date": alert_return_date.strftime("%Y-%m-%d") if alert_return_date else None,
        "target_price": float(target_price),
        "currency": alert_currency,
        "email": email,
        "notification_channels": notification_channels
    }

    try:
        response = requests.post(f"{API_BASE_URL}/alerts", json=payload)
        if response.status_code == 200:
            data = response.json()
            trip_display = "One-way" if trip_type_api == "one-way" else "Round-trip"
            st.success(f"✅ {trip_display} alert created! ID: {data.get('alert_id', 'Unknown')}")
            st.json(data)
        else:
            st.error(f"❌ Alert creation failed: {response.status_code}")
            st.text(response.text)
    except Exception as e:
        st.error(f"❌ Connection failed: {str(e)}")

# View Alerts
if st.button("📋 View All Alerts"):
    try:
        response = requests.get(f"{API_BASE_URL}/alerts")
        if response.status_code == 200:
            data = response.json()
            alerts = data.get('alerts', [])
            st.success(f"📊 Found {len(alerts)} active alerts")

            for alert in alerts:
                trip_type_display = "One-way" if alert.get('trip_type') == "one-way" else "Round-trip"
                currency = alert.get('currency', 'SEK')
                return_date_info = f" → {alert['return_date']}" if alert.get('return_date') else ""

                with st.expander(f"🔔 {trip_type_display} Alert {alert['alert_id'][:12]}..."):
                    col_alert1, col_alert2 = st.columns(2)

                    with col_alert1:
                        st.markdown("**✈️ Trip Details**")
                        st.write(f"**Route:** {alert['origin']} → {alert['destination']}")
                        st.write(f"**Type:** {trip_type_display}")
                        st.write(f"**Dates:** {alert['depart_date']}{return_date_info}")

                        st.markdown("**💰 Price Target**")
                        st.write(f"**Amount:** {alert['target_price']} {currency}")
                        st.write(f"**Status:** {alert['status'].title()}")

                    with col_alert2:
                        st.markdown("**📧 Notifications**")
                        st.write(f"**Email:** {alert['email']}")
                        st.write(f"**Channels:** {', '.join(alert.get('notification_channels', ['email']))}")

                        st.markdown("**📅 Metadata**")
                        st.write(f"**Created:** {alert['created_at'][:10]}")
                        st.write(f"**ID:** {alert['alert_id']}")

                        # Delete button for this alert
                        if st.button(f"🗑️ Delete Alert", key=f"delete_{alert['alert_id']}"):
                            try:
                                delete_response = requests.delete(f"{API_BASE_URL}/alerts/{alert['alert_id']}")
                                if delete_response.status_code == 200:
                                    st.success("✅ Alert deleted successfully!")
                                    st.rerun()
                                else:
                                    st.error("❌ Failed to delete alert")
                            except Exception as e:
                                st.error(f"❌ Delete failed: {str(e)}")
        else:
            st.error(f"❌ Failed to fetch alerts: {response.status_code}")
    except Exception as e:
        st.error(f"❌ Connection failed: {str(e)}")

# AI-Powered Search
st.header("🤖 AI-Powered Flight Search")
st.markdown("✨ **NEW!** Ask questions in natural language and let AI find your flights!")

# AI Provider Selection
ai_provider = st.selectbox(
    "🧠 Choose AI Provider",
    ["openai", "gemini", "deepseek"],
    index=0,
    help="Select your preferred AI provider for natural language processing"
)

ai_query = st.text_input(
    "💬 Ask me about flights:",
    placeholder="e.g., 'Find cheap flights from Paris to Tokyo next weekend'",
    help="Try: 'Show me round-trip flights to London in December' or 'Find business class flights from NYC to LA'"
)

# Dynamic API key input based on provider
api_key_labels = {
    "openai": "🔑 OpenAI API Key (optional)",
    "gemini": "🔑 Gemini API Key (optional)",
    "deepseek": "🔑 DeepSeek API Key (optional)"
}

api_key_placeholders = {
    "openai": "sk-...",
    "gemini": "AIza...",
    "deepseek": "sk-..."
}

api_key_help = {
    "openai": "Set OPENAI_API_KEY environment variable or enter here",
    "gemini": "Set GEMINI_API_KEY environment variable or enter here",
    "deepseek": "Set DEEPSEEK_API_KEY environment variable or enter here"
}

ai_api_key = st.text_input(
    api_key_labels[ai_provider],
    type="password",
    help=api_key_help[ai_provider],
    placeholder=api_key_placeholders[ai_provider]
)

if st.button("🚀 AI Search Flights", type="primary"):
    if not ai_query.strip():
        st.error("❌ Please enter a flight search query")
    else:
        with st.spinner("🤖 AI is analyzing your request..."):
            try:
                payload = {
                    "query": ai_query.strip(),
                    "provider": ai_provider,
                    "api_key": ai_api_key if ai_api_key else None
                }

                response = requests.post(f"{API_BASE_URL}/ai/search", json=payload, timeout=30)

                if response.status_code == 200:
                    data = response.json()

                    st.success(f"✅ AI found {data.get('total_flights', 0)} flights!")

                    # Show parsed query
                    with st.expander("🧠 AI Parsed Your Request"):
                        parsed = data.get('parsed_query', {})
                        col1, col2 = st.columns(2)
                        with col1:
                            st.write(f"**From:** {parsed.get('origin', 'Unknown')}")
                            st.write(f"**To:** {parsed.get('destination', 'Unknown')}")
                            st.write(f"**Trip:** {parsed.get('trip_type', 'Unknown').title()}")
                        with col2:
                            st.write(f"**Departure:** {parsed.get('depart_date', 'Unknown')}")
                            st.write(f"**Return:** {parsed.get('return_date', 'N/A')}")
                            st.write(f"**Class:** {parsed.get('seat_class', 'economy').title()}")

                    # Display results
                    if data.get('flights'):
                        st.subheader("✈️ AI-Recommended Flights")

                        # Summary stats
                        total_flights = data['total_flights']
                        flights_shown = len(data['flights'])

                        col_stats1, col_stats2 = st.columns(2)
                        with col_stats1:
                            st.metric("Total Flights Found", total_flights)
                        with col_stats2:
                            st.metric("Top Results Shown", flights_shown)

                        # Show flights
                        for i, flight in enumerate(data['flights'], 1):
                            price_num = parse_price(flight['price'])

                            with st.expander(f"#{i} 🏆 {flight['name']} - {flight['price']} ({flight['duration']})"):
                                col_detail1, col_detail2 = st.columns(2)

                                with col_detail1:
                                    st.markdown("**🛫 Departure**")
                                    st.write(f"**Time:** {flight['departure']}")
                                    st.write(f"**From:** AI-parsed origin")

                                with col_detail2:
                                    st.markdown("**📊 Flight Details**")
                                    st.write(f"**Duration:** {flight['duration']}")
                                    st.write(f"**Stops:** {flight['stops']}")
                                    if flight.get('delay'):
                                        st.write(f"**⚠️ Delay:** {flight['delay']}")

                                # Direct booking link
                                if data.get('search_url'):
                                    st.markdown("---")
                                    st.markdown(f"**🔗 Book on Google Flights:** [View & Book]({data['search_url']})")

                        # AI insights
                        if total_flights > flights_shown:
                            st.info(f"💡 AI found {total_flights - flights_shown} more flight options. Showing top {flights_shown} results.")

                    else:
                        st.warning("🤔 No flights found for your AI-parsed request. Try rephrasing your query.")

                elif response.status_code == 503:
                    st.error("❌ AI functionality not available. Please install OpenAI: `pip install openai`")
                elif response.status_code == 400:
                    st.error(f"❌ AI Error: {response.json().get('detail', 'Invalid request')}")
                else:
                    st.error(f"❌ AI Search failed: {response.status_code}")

            except requests.exceptions.Timeout:
                st.error("⏰ AI search timed out. Please try again.")
            except Exception as e:
                st.error(f"❌ AI search failed: {str(e)}")

st.markdown("---")

# API Documentation Link
st.header("📚 API Documentation")
st.markdown(f"📖 **Interactive API Docs:** {API_BASE_URL}/docs")
st.markdown(f"🔗 **OpenAPI JSON:** {API_BASE_URL}/openapi.json")
st.markdown(f"🤖 **AI Search Endpoint:** `{API_BASE_URL}/ai/search`")

# Footer
st.markdown("---")
st.markdown("**🧠 FlyMind** - AI-Powered Flight Analytics & Automation Suite")
st.markdown("**👨‍💻 Developed by:** Abdirahman")
st.markdown("**🚀 Powered by:** FastAPI, Streamlit & Playwright")
st.markdown("**📊 Status:** API running on port 8001 | Ready for deployment to Coolify! 🚀")
st.markdown("**📅 Version:** 2.0.0 | Built with ❤️ for automation excellence")
