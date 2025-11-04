"""
Enhanced Streamlit app with multi-city search, progress indicators, 
flight comparison, search history, and export functionality.
"""

import streamlit as st
import requests
import json
import re
import os
import pandas as pd
import time
from datetime import datetime, timedelta
from io import BytesIO
import base64
from typing import List, Dict, Any

# Session state initialization
if 'search_history' not in st.session_state:
    st.session_state.search_history = []
if 'favorite_routes' not in st.session_state:
    st.session_state.favorite_routes = []
if 'current_search_id' not in st.session_state:
    st.session_state.current_search_id = None
if 'search_results' not in st.session_state:
    st.session_state.search_results = {}

def parse_price(price_str):
    """Parse price string with various whitespace and currency formats"""
    if not price_str:
        return 0
    clean_price = re.sub(r'[^\d,.\s]', '', price_str)
    clean_price = re.sub(r'\s+', '', clean_price)
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

def save_search_to_history(search_params: dict, results: dict):
    """Save search to history"""
    search_entry = {
        'id': f"search_{int(time.time())}",
        'timestamp': datetime.now().isoformat(),
        'params': search_params,
        'results': results,
        'favorite': False
    }
    st.session_state.search_history.insert(0, search_entry)
    # Keep only last 50 searches
    if len(st.session_state.search_history) > 50:
        st.session_state.search_history = st.session_state.search_history[:50]

def export_to_csv(data: List[Dict]) -> BytesIO:
    """Export flight data to CSV"""
    df = pd.DataFrame(data)
    output = BytesIO()
    df.to_csv(output, index=False)
    output.seek(0)
    return output

def export_to_json(data: Dict) -> str:
    """Export flight data to JSON"""
    return json.dumps(data, indent=2, default=str)

# Configure page
st.set_page_config(
    page_title="FlyMind - AI-Powered Flight Analytics",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS
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
    .progress-container {
        background: #f0f2f6;
        padding: 1rem;
        border-radius: 10px;
        margin: 1rem 0;
    }
    .comparison-card {
        background: white;
        padding: 1rem;
        border-radius: 10px;
        border: 2px solid #667eea;
        margin: 0.5rem 0;
    }
    .history-item {
        background: #f8f9fa;
        padding: 0.75rem;
        border-radius: 8px;
        margin: 0.5rem 0;
        border-left: 4px solid #667eea;
    }
</style>
""", unsafe_allow_html=True)

# Main Header
st.markdown("""
<div class="main-header">
    <div style="font-size: 3rem; font-weight: bold; margin-bottom: 0.5rem;">🧠 FlyMind</div>
    <div style="font-size: 1.2rem; opacity: 0.9;">AI-Powered Flight Analytics & Automation Suite</div>
</div>
""", unsafe_allow_html=True)

# Sidebar Configuration
st.sidebar.markdown("### ⚙️ Configuration")
if 'STREAMLIT_SERVER_HEADLESS' in os.environ:
    default_api_url = "https://your-deployed-api-url.flymind.com"
else:
    default_api_url = "http://localhost:8001"

API_BASE_URL = st.sidebar.text_input("API Base URL", default_api_url)

# API Health Check
if st.sidebar.button("🔄 Check API Health"):
    try:
        response = requests.get(f"{API_BASE_URL}/health", timeout=5)
        if response.status_code == 200:
            st.sidebar.success("✅ API Healthy")
        else:
            st.sidebar.error("❌ API Unhealthy")
    except:
        st.sidebar.error("❌ API Offline")

st.sidebar.markdown("---")

# Navigation
page = st.sidebar.selectbox(
    "📑 Navigation",
    ["✈️ Flight Search", "📊 Flight Comparison", "📚 Search History", "⭐ Favorite Routes"]
)

# ========== FLIGHT SEARCH PAGE ==========
if page == "✈️ Flight Search":
    st.header("✈️ Advanced Flight Search")
    
    # Trip Type Selection
    trip_type = st.radio("Trip Type", ["One Way", "Round Trip", "Multi City"], horizontal=True)
    
    # Multi-city search UI
    if trip_type == "Multi City":
        st.subheader("🌍 Multi-City Route")
        num_segments = st.number_input("Number of Stops", 2, 5, 2, help="Add 2-5 flight segments")
        
        segments = []
        for i in range(num_segments):
            st.markdown(f"### Segment {i+1}")
            col1, col2, col3 = st.columns([2, 2, 1])
            with col1:
                origin = st.text_input(f"From", key=f"seg_{i}_origin", placeholder="City or Airport")
            with col2:
                destination = st.text_input(f"To", key=f"seg_{i}_dest", placeholder="City or Airport")
            with col3:
                depart_date = st.date_input(f"Date", datetime.now() + timedelta(days=7*(i+1)), key=f"seg_{i}_date")
            
            if origin and destination:
                segments.append({
                    'origin': origin,
                    'destination': destination,
                    'depart_date': depart_date.strftime("%Y-%m-%d")
                })
        
        col1, col2 = st.columns(2)
        with col1:
            adults = st.number_input("Passengers", 1, 10, 1)
        with col2:
            seat_class = st.selectbox("Class", ["economy", "premium_economy", "business", "first"], index=0)
        
        with st.expander("🔧 Advanced Options"):
            max_stops = st.selectbox("Max Stops", ["any", "nonstop", "1", "2"], index=0)
            fetch_mode = st.selectbox("Search Mode", ["local", "remote"], index=0)
        
        if st.button("🔍 Search Multi-City Flights", type="primary"):
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
                
                # Progress indicator
                progress_bar = st.progress(0)
                status_text = st.empty()
                
                try:
                    status_text.text("🔄 Searching flights... This may take a while for multi-city routes.")
                    start_time = time.time()
                    
                    response = requests.post(f"{API_BASE_URL}/search", json=payload, timeout=120)
                    
                    elapsed_time = time.time() - start_time
                    progress_bar.progress(100)
                    
                    if response.status_code == 200:
                        data = response.json()
                        status_text.success(f"✅ Found {data.get('total_flights', 0)} flights in {elapsed_time:.1f}s")
                        
                        # Save to history
                        save_search_to_history(payload, data)
                        st.session_state.current_search_id = data.get('search_id')
                        st.session_state.search_results[data.get('search_id', 'latest')] = data
                        
                        # Display results
                        display_flight_results(data, is_multi_city=True)
                    else:
                        status_text.error(f"❌ Search failed: {response.status_code}")
                        st.text(response.text)
                except Exception as e:
                    status_text.error(f"❌ Error: {str(e)}")
    
    else:
        # Single/round-trip search (existing logic)
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
        
        with st.expander("🔧 Advanced Options"):
            max_stops = st.selectbox("Max Stops", ["any", "nonstop", "1", "2"], index=0)
            fetch_mode = st.selectbox("Search Mode", ["local", "remote"], index=0)
        
        if st.button("🔍 Search Flights", type="primary"):
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
            
            # Progress indicator
            progress_bar = st.progress(0)
            status_text = st.empty()
            estimated_time = st.empty()
            
            try:
                status_text.text("🔄 Searching flights...")
                start_time = time.time()
                
                # Simulate progress (actual progress would come from streaming API)
                for i in range(5):
                    time.sleep(0.5)
                    progress_bar.progress((i + 1) * 20)
                    status_text.text(f"🔄 Searching flights... {20*(i+1)}%")
                
                response = requests.post(f"{API_BASE_URL}/search", json=payload, timeout=60)
                
                elapsed_time = time.time() - start_time
                progress_bar.progress(100)
                
                if response.status_code == 200:
                    data = response.json()
                    status_text.success(f"✅ Found {data.get('total_flights', 0)} flights in {elapsed_time:.1f}s")
                    
                    # Save to history
                    save_search_to_history(payload, data)
                    st.session_state.current_search_id = data.get('search_id')
                    st.session_state.search_results[data.get('search_id', 'latest')] = data
                    
                    # Display results
                    display_flight_results(data)
                else:
                    status_text.error(f"❌ Search failed: {response.status_code}")
                    st.text(response.text)
            except Exception as e:
                status_text.error(f"❌ Error: {str(e)}")

def display_flight_results(data: dict, is_multi_city: bool = False):
    """Display flight results with export options"""
    if not data.get('flights'):
        st.warning("No flights found")
        return
    
    # Export buttons
    col_exp1, col_exp2, col_exp3 = st.columns(3)
    with col_exp1:
        if st.button("📥 Export to CSV"):
            csv_data = export_to_csv(data['flights'])
            st.download_button(
                label="⬇️ Download CSV",
                data=csv_data,
                file_name=f"flights_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                mime="text/csv"
            )
    with col_exp2:
        if st.button("📥 Export to JSON"):
            json_str = export_to_json(data)
            st.download_button(
                label="⬇️ Download JSON",
                data=json_str,
                file_name=f"flights_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json",
                mime="application/json"
            )
    with col_exp3:
        # Share link (would generate a shareable link in production)
        search_id = data.get('search_id', 'latest')
        share_url = f"{API_BASE_URL}/search/{search_id}"
        st.markdown(f"🔗 [Share Results]({share_url})")
    
    # Results display
    flights = data['flights']
    valid_flights = [f for f in flights if f.get('price') and parse_price(f['price']) > 0]
    
    # Summary metrics
    prices = [parse_price(f['price']) for f in valid_flights]
    col_stats1, col_stats2, col_stats3 = st.columns(3)
    with col_stats1:
        st.metric("Total Flights", len(valid_flights))
    with col_stats2:
        st.metric("Average Price", f"SEK {sum(prices)/len(prices):.0f}" if prices else "N/A")
    with col_stats3:
        st.metric("Lowest Price", f"SEK {min(prices):.0f}" if prices else "N/A")
    
    # Flight cards
    for i, flight in enumerate(valid_flights[:20]):
        price_num = parse_price(flight['price'])
        price_color = "🟢" if price_num <= min(prices) * 1.1 else "🟡" if price_num <= sum(prices)/len(prices) * 1.2 else "🔴"
        
        with st.expander(f"{price_color} {flight['name']} - {flight['price']} ({flight['duration']})"):
            col1, col2 = st.columns(2)
            with col1:
                st.markdown(f"**🛫 Departure:** {flight['departure']}")
                st.markdown(f"**🛬 Arrival:** {flight['arrival']}")
            with col2:
                st.markdown(f"**Duration:** {flight['duration']}")
                st.markdown(f"**Stops:** {flight['stops']}")
                st.markdown(f"**Price:** {flight['price']}")
            
            if is_multi_city and flight.get('segment_route'):
                st.info(f"Segment: {flight['segment_route']}")

# ========== FLIGHT COMPARISON PAGE ==========
elif page == "📊 Flight Comparison":
    st.header("📊 Flight Comparison")
    
    if not st.session_state.search_results:
        st.info("No search results available. Please search for flights first.")
    else:
        # Select searches to compare
        search_ids = list(st.session_state.search_results.keys())
        selected_searches = st.multiselect("Select searches to compare", search_ids, default=search_ids[:2] if len(search_ids) >= 2 else search_ids)
        
        if len(selected_searches) >= 2:
            # Get results
            results_to_compare = [st.session_state.search_results[sid] for sid in selected_searches]
            
            # Comparison table
            comparison_data = []
            for result in results_to_compare:
                flights = result.get('flights', [])
                if flights:
                    valid_flights = [f for f in flights if f.get('price') and parse_price(f['price']) > 0]
                    if valid_flights:
                        prices = [parse_price(f['price']) for f in valid_flights]
                        comparison_data.append({
                            'Search': f"Search {selected_searches[results_to_compare.index(result)]}",
                            'Total Flights': len(valid_flights),
                            'Lowest Price': min(prices),
                            'Average Price': sum(prices) / len(prices),
                            'Best Duration': min([parse_duration(f.get('duration', '')) for f in valid_flights])
                        })
            
            if comparison_data:
                st.subheader("📊 Comparison Table")
                df_compare = pd.DataFrame(comparison_data)
                st.dataframe(df_compare, use_container_width=True)
                
                # Price trend chart
                st.subheader("💰 Price Trends")
                chart_data = pd.DataFrame({
                    'Search': [d['Search'] for d in comparison_data],
                    'Lowest Price': [d['Lowest Price'] for d in comparison_data],
                    'Average Price': [d['Average Price'] for d in comparison_data]
                })
                st.bar_chart(chart_data.set_index('Search'))
                
                # Best time to book recommendation
                st.subheader("⏰ Best Time to Book")
                if comparison_data:
                    best_price = min([d['Lowest Price'] for d in comparison_data])
                    best_search = [d for d in comparison_data if d['Lowest Price'] == best_price][0]
                    st.success(f"💡 Best price found in {best_search['Search']}: SEK {best_price:.0f}")
                    st.info("📅 Tip: Book 2-3 months in advance for best prices. Tuesday and Wednesday flights are often cheaper.")

# ========== SEARCH HISTORY PAGE ==========
elif page == "📚 Search History":
    st.header("📚 Search History")
    
    if not st.session_state.search_history:
        st.info("No search history yet. Start searching for flights!")
    else:
        # Filter options
        col1, col2 = st.columns(2)
        with col1:
            show_favorites_only = st.checkbox("Show favorites only")
        with col2:
            sort_by = st.selectbox("Sort by", ["Newest first", "Oldest first", "Price (lowest)", "Price (highest)"])
        
        # Filter and sort history
        history_to_show = st.session_state.search_history
        if show_favorites_only:
            history_to_show = [h for h in history_to_show if h.get('favorite')]
        
        # Display history
        for entry in history_to_show[:20]:  # Show last 20
            with st.expander(f"🔍 {entry['params'].get('origin', 'N/A')} → {entry['params'].get('destination', 'N/A')} ({entry['timestamp'][:10]})"):
                col1, col2 = st.columns([3, 1])
                with col1:
                    st.json(entry['params'])
                    if entry.get('results'):
                        st.metric("Flights Found", entry['results'].get('total_flights', 0))
                with col2:
                    # Favorite button
                    favorite_key = f"fav_{entry['id']}"
                    is_favorite = st.button("⭐", key=favorite_key) if not entry.get('favorite') else st.button("⭐", key=favorite_key, disabled=True)
                    if is_favorite:
                        entry['favorite'] = True
                        st.session_state.favorite_routes.append(entry)
                        st.rerun()
                    
                    # Re-search button
                    if st.button("🔍 Re-search", key=f"res_{entry['id']}"):
                        # Set search params and switch to search page
                        st.session_state.auto_search_params = entry['params']
                        st.rerun()

# ========== FAVORITE ROUTES PAGE ==========
elif page == "⭐ Favorite Routes":
    st.header("⭐ Favorite Routes")
    
    if not st.session_state.favorite_routes:
        st.info("No favorite routes yet. Add favorites from search history!")
    else:
        for route in st.session_state.favorite_routes:
            st.markdown(f"""
            <div class="history-item">
                <strong>{route['params'].get('origin', 'N/A')} → {route['params'].get('destination', 'N/A')}</strong><br>
                <small>{route['timestamp'][:16]}</small>
            </div>
            """, unsafe_allow_html=True)
            
            if st.button(f"🔍 Search Again", key=f"fav_search_{route['id']}"):
                st.session_state.auto_search_params = route['params']
                st.rerun()

# Auto-search if params are set
if 'auto_search_params' in st.session_state:
    st.info("🔄 Auto-searching with saved parameters...")
    # This would trigger an automatic search
    # For now, just clear the flag
    del st.session_state.auto_search_params

