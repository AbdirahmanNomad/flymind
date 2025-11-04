import streamlit as st
import requests
import json
import re
import os
import pandas as pd
import time
from datetime import datetime, timedelta
from io import BytesIO
from typing import List, Dict, Any

# Session state initialization
if 'search_history' not in st.session_state:
    st.session_state.search_history = []
if 'favorite_routes' not in st.session_state:
    st.session_state.favorite_routes = []
if 'search_results' not in st.session_state:
    st.session_state.search_results = {}

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

def parse_duration(duration_str):
    """Parse duration string like '2 hr 30 min' to minutes"""
    if not duration_str:
        return 0
    hours = 0
    minutes = 0
    hour_match = re.search(r'(\d+)\s*hr', duration_str.lower())
    if hour_match:
        hours = int(hour_match.group(1))
    min_match = re.search(r'(\d+)\s*min', duration_str.lower())
    if min_match:
        minutes = int(min_match.group(1))
    return hours * 60 + minutes

def display_results_with_export(data: dict, is_multi_city: bool = False, sort_by: str = "price"):
    """Display flight results with export and comparison features"""
    if not data.get('flights'):
        st.warning("No flights found")
        return
    
    # Export and share buttons
    st.subheader("📊 Results & Export")
    col_exp1, col_exp2, col_exp3, col_exp4 = st.columns(4)
    
    with col_exp1:
        flights_df = pd.DataFrame(data['flights'])
        csv = flights_df.to_csv(index=False)
        st.download_button(
            label="📥 Download CSV",
            data=csv,
            file_name=f"flights_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
            mime="text/csv"
        )
    
    with col_exp2:
        json_str = json.dumps(data, indent=2, default=str)
        st.download_button(
            label="📥 Download JSON",
            data=json_str,
            file_name=f"flights_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json",
            mime="application/json"
        )
    
    with col_exp3:
        # Share link (in production, this would generate a shareable link)
        search_id = data.get('search_id', 'latest')
        st.markdown(f"🔗 [Share Results]({API_BASE_URL}/search/{search_id})")
    
    with col_exp4:
        print_view_key = f"print_view_{search_id}"
        show_print_view = st.checkbox("📄 Show Print View", key=print_view_key, help="Display print-friendly JSON view")
        if show_print_view:
            st.markdown("### 📄 Print-Friendly View")
            st.json(data)
            st.markdown("---")
    
    # Comparison checkbox - Always show if there are multiple searches
    st.markdown("---")
    if len(st.session_state.search_results) > 1:
        enable_comparison = st.checkbox("📊 Enable Flight Comparison", help="Compare this search with others", key=f"comp_{search_id}", value=False)
    else:
        enable_comparison = False
        st.info("💡 Run multiple searches to enable flight comparison")
    
    if enable_comparison and len(st.session_state.search_results) > 1:
        st.subheader("📊 Compare with Other Searches")
        comparison_ids = st.multiselect(
            "Select searches to compare",
            list(st.session_state.search_results.keys()),
            default=list(st.session_state.search_results.keys())[:2] if len(st.session_state.search_results) >= 2 else [],
            key=f"comp_select_{search_id}"
        )
        
        if len(comparison_ids) >= 2:
            comparison_data = []
            for sid in comparison_ids:
                result = st.session_state.search_results[sid]
                flights = result.get('flights', [])
                if flights:
                    valid_flights = [f for f in flights if f.get('price') and parse_price(f['price']) > 0]
                    if valid_flights:
                        prices = [parse_price(f['price']) for f in valid_flights]
                        comparison_data.append({
                            'Search': sid[:12],
                            'Total Flights': len(valid_flights),
                            'Lowest Price': min(prices),
                            'Average Price': sum(prices) / len(prices),
                            'Best Duration': min([parse_duration(f.get('duration', '')) for f in valid_flights])
                        })
            
            if comparison_data:
                st.dataframe(pd.DataFrame(comparison_data), use_container_width=True)
                
                # Price trend chart
                chart_data = pd.DataFrame({
                    'Search': [d['Search'] for d in comparison_data],
                    'Lowest Price': [d['Lowest Price'] for d in comparison_data],
                    'Average Price': [d['Average Price'] for d in comparison_data]
                })
                st.bar_chart(chart_data.set_index('Search'))
                
                # Best time to book recommendation
                best_price = min([d['Lowest Price'] for d in comparison_data])
                best_search = [d for d in comparison_data if d['Lowest Price'] == best_price][0]
                st.success(f"💡 Best price found in {best_search['Search']}: SEK {best_price:.0f}")
                st.info("📅 Tip: Book 2-3 months in advance for best prices. Tuesday and Wednesday flights are often cheaper.")
    
    # Display results
    st.subheader("✈️ Flight Results")
    flights = data['flights']
    valid_flights = [f for f in flights if f.get('price') and parse_price(f['price']) > 0]
    
    # Sort flights
    if sort_by == "price":
        valid_flights.sort(key=lambda x: parse_price(x['price']))
    elif sort_by == "duration":
        valid_flights.sort(key=lambda x: parse_duration(x.get('duration', '')))
    elif sort_by == "stops":
        valid_flights.sort(key=lambda x: x.get('stops', 0))
    elif sort_by == "best":
        # Best: balance of price and duration (lower is better)
        valid_flights.sort(key=lambda x: parse_price(x['price']) + parse_duration(x.get('duration', '')) * 0.1)
    
    # Summary metrics
    prices = [parse_price(f['price']) for f in valid_flights]
    avg_price = sum(prices) / len(prices) if prices else 0
    min_price = min(prices) if prices else 0
    
    col_stats1, col_stats2, col_stats3 = st.columns(3)
    with col_stats1:
        st.metric("Total Flights", len(valid_flights))
    with col_stats2:
        st.metric("Average Price", f"SEK {avg_price:.0f}")
    with col_stats3:
        st.metric("Lowest Price", f"SEK {min_price:.0f}")
    
    # Display flight cards
    for i, flight in enumerate(valid_flights[:20]):
        price_num = parse_price(flight['price'])
        price_color = "🟢" if price_num <= min_price * 1.1 else "🟡" if price_num <= avg_price * 1.2 else "🔴"
        
        with st.expander(f"{price_color} {flight['name']} - {flight['price']} ({flight['duration']})"):
            col_detail1, col_detail2 = st.columns(2)
            with col_detail1:
                st.markdown(f"**🛫 Departure:** {flight['departure']}")
                st.markdown(f"**🛬 Arrival:** {flight['arrival']}")
            with col_detail2:
                st.markdown(f"**Duration:** {flight['duration']}")
                st.markdown(f"**Stops:** {flight['stops']}")
                st.markdown(f"**Price:** {flight['price']}")
            
            if is_multi_city and flight.get('segment_route'):
                st.info(f"Segment: {flight['segment_route']}")

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

# API Configuration - Auto-detect environment
if 'STREAMLIT_SERVER_HEADLESS' in os.environ:
    # Running on Streamlit Cloud - use deployed API
    default_api_url = "https://your-deployed-api-url.flymind.com"  # Replace with your actual deployed API URL
else:
    # Running locally
    default_api_url = "http://localhost:8001"

API_BASE_URL = st.sidebar.text_input("API Base URL", default_api_url, help="URL of your Google Flights API server")

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

# Multi-city search UI
if trip_type == "Multi City":
    st.subheader("🌍 Multi-City Route")
    num_segments = st.number_input("Number of Stops", 2, 5, 2, help="Add 2-5 flight segments")
    
    segments = []
    for i in range(num_segments):
        st.markdown(f"### Segment {i+1}")
        col_seg1, col_seg2, col_seg3 = st.columns([2, 2, 1])
        with col_seg1:
            origin_seg = st.text_input(f"From", key=f"seg_{i}_origin", placeholder="City or Airport")
        with col_seg2:
            destination_seg = st.text_input(f"To", key=f"seg_{i}_dest", placeholder="City or Airport")
        with col_seg3:
            depart_date_seg = st.date_input(f"Date", datetime.now() + timedelta(days=7*(i+1)), key=f"seg_{i}_date")
        
        if origin_seg and destination_seg:
            segments.append({
                'origin': origin_seg,
                'destination': destination_seg,
                'depart_date': depart_date_seg.strftime("%Y-%m-%d")
            })
    
    col_pass1, col_pass2 = st.columns(2)
    with col_pass1:
        adults = st.number_input("Passengers", 1, 10, 1, key="multi_adults")
    with col_pass2:
        seat_class = st.selectbox("Class", ["economy", "premium_economy", "business", "first"], index=0, key="multi_class")
    
    with st.expander("🔧 Advanced Options"):
        max_stops = st.selectbox("Max Stops", ["any", "nonstop", "1", "2"], index=0, key="multi_stops")
        fetch_mode = st.selectbox("Search Mode", ["local", "remote"], index=0, key="multi_mode")
    
    if st.button("🔍 Search Multi-City Flights", type="primary", key="multi_search"):
        if len(segments) < 2:
            st.error("Please add at least 2 segments for multi-city search")
        else:
            # Build multi-city payload
            payload = {
                "trip_type": "multi-city",
                "segments": segments,
                "adults": adults,
                "seat_class": seat_class,
                "fetch_mode": fetch_mode,
                "max_stops": 0 if max_stops == "nonstop" else (int(max_stops) if max_stops.isdigit() else None)
            }
            
            # Progress indicator with real-time updates
            progress_bar = st.progress(0)
            status_text = st.empty()
            time_estimate = st.empty()
            
            try:
                status_text.text("🔄 Searching flights... This may take a while for multi-city routes.")
                start_time = time.time()
                
                # Simulate progress updates
                for i in range(10):
                    time.sleep(0.3)
                    progress = (i + 1) * 10
                    progress_bar.progress(progress / 100)
                    elapsed = time.time() - start_time
                    estimated_total = elapsed / (progress / 100) if progress > 0 else 0
                    remaining = max(0, estimated_total - elapsed)
                    status_text.text(f"🔄 Searching flights... {progress}% complete")
                    time_estimate.text(f"⏱️ Estimated time remaining: {remaining:.0f}s")
                
                response = requests.post(f"{API_BASE_URL}/search", json=payload, timeout=120)
                
                elapsed_time = time.time() - start_time
                progress_bar.progress(100)
                time_estimate.empty()
                
                if response.status_code == 200:
                    data = response.json()
                    status_text.success(f"✅ Found {data.get('total_flights', 0)} flights in {elapsed_time:.1f}s")
                    
                    # Save to history
                    search_entry = {
                        'id': f"search_{int(time.time())}",
                        'timestamp': datetime.now().isoformat(),
                        'params': payload,
                        'results': data,
                        'favorite': False
                    }
                    st.session_state.search_history.insert(0, search_entry)
                    if len(st.session_state.search_history) > 50:
                        st.session_state.search_history = st.session_state.search_history[:50]
                    
                    st.session_state.search_results[search_entry['id']] = data
                    
                    # Display results
                    display_results_with_export(data, is_multi_city=True, sort_by="price")
                else:
                    status_text.error(f"❌ Search failed: {response.status_code}")
                    st.text(response.text)
            except Exception as e:
                status_text.error(f"❌ Error: {str(e)}")

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

if st.button("🔍 Search Flights", key="search_btn"):
    # Convert max_stops from string to int or None
    max_stops_int = None
    if max_stops == "nonstop":
        max_stops_int = 0
    elif max_stops.isdigit():
        max_stops_int = int(max_stops)
    
    trip_type_api = "one-way" if trip_type == "One Way" else "round-trip"
    payload = {
        "trip_type": trip_type_api,
        "origin": origin,
        "destination": destination,
        "depart_date": depart_date.strftime("%Y-%m-%d"),
        "return_date": return_date.strftime("%Y-%m-%d") if return_date else None,
        "adults": adults,
        "fetch_mode": fetch_mode,
        "max_stops": max_stops_int
    }
    
    # Progress indicator with real-time updates
    progress_bar = st.progress(0)
    status_text = st.empty()
    time_estimate = st.empty()
    
    try:
        status_text.text("🔄 Searching flights...")
        start_time = time.time()
        
        # Simulate progress (in production, this would come from streaming API)
        for i in range(5):
            time.sleep(0.5)
            progress = (i + 1) * 20
            progress_bar.progress(progress / 100)
            elapsed = time.time() - start_time
            estimated_total = elapsed / (progress / 100) if progress > 0 else 0
            remaining = max(0, estimated_total - elapsed)
            status_text.text(f"🔄 Searching flights... {progress}% complete")
            time_estimate.text(f"⏱️ Estimated time remaining: {remaining:.0f}s")
        
        response = requests.post(f"{API_BASE_URL}/search", json=payload, timeout=60)
        
        elapsed_time = time.time() - start_time
        progress_bar.progress(100)
        time_estimate.empty()
        if response.status_code == 200:
            data = response.json()
            status_text.success(f"✅ Found {data.get('total_flights', 0)} flights in {elapsed_time:.1f}s")
            
            # Save to history
            search_entry = {
                'id': f"search_{int(time.time())}",
                'timestamp': datetime.now().isoformat(),
                'params': payload,
                'results': data,
                'favorite': False
            }
            st.session_state.search_history.insert(0, search_entry)
            if len(st.session_state.search_history) > 50:
                st.session_state.search_history = st.session_state.search_history[:50]
            
            st.session_state.search_results[search_entry['id']] = data
            
            # Display results with export options
            display_results_with_export(data, sort_by=sort_by)
        else:
            status_text.error(f"❌ Search failed: {response.status_code}")
            st.text(response.text)
    except Exception as e:
        status_text.error(f"❌ Connection failed: {str(e)}")

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

# Search History Section
st.header("📚 Search History")
if st.session_state.search_history:
    # Filter options
    col_filt1, col_filt2 = st.columns(2)
    with col_filt1:
        show_favorites_only = st.checkbox("Show favorites only", key="fav_filter")
    with col_filt2:
        sort_history = st.selectbox("Sort by", ["Newest first", "Oldest first"], key="sort_history")
    
    # Filter history
    history_to_show = st.session_state.search_history
    if show_favorites_only:
        history_to_show = [h for h in history_to_show if h.get('favorite')]
    
    if sort_history == "Oldest first":
        history_to_show = list(reversed(history_to_show))
    
    # Display history
    for entry in history_to_show[:10]:  # Show last 10
        with st.expander(f"🔍 {entry['params'].get('origin', 'N/A')} → {entry['params'].get('destination', 'N/A')} ({entry['timestamp'][:10]})"):
            col_hist1, col_hist2 = st.columns([3, 1])
            with col_hist1:
                st.json(entry['params'])
                if entry.get('results'):
                    st.metric("Flights Found", entry['results'].get('total_flights', 0))
            with col_hist2:
                # Favorite button
                if not entry.get('favorite'):
                    if st.button("⭐ Add to Favorites", key=f"fav_{entry['id']}"):
                        entry['favorite'] = True
                        st.session_state.favorite_routes.append(entry)
                        st.rerun()
                else:
                    st.success("⭐ Favorited")
                
                # Re-search button
                if st.button("🔍 Re-search", key=f"res_{entry['id']}"):
                    st.info("Click 'Search Flights' above with pre-filled values")
                    # In production, would auto-fill the form
                
                # Quick view results
                if st.button("👁️ View Results", key=f"view_{entry['id']}"):
                    if entry.get('results'):
                        display_results_with_export(entry['results'], sort_by="price")
    
    # Favorite Routes Section
    if st.session_state.favorite_routes:
        st.subheader("⭐ Favorite Routes")
        for route in st.session_state.favorite_routes:
            st.markdown(f"""
            **{route['params'].get('origin', 'N/A')} → {route['params'].get('destination', 'N/A')}**
            - {route['timestamp'][:16]}
            """)
            if st.button(f"🔍 Search Again", key=f"fav_search_{route['id']}"):
                st.info("Click 'Search Flights' with these parameters")
else:
    st.info("No search history yet. Start searching for flights!")

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
