"""
Comprehensive test script for all Streamlit UX features.
Run this to verify all functionality works correctly.
"""

import requests
import json
from datetime import datetime, timedelta

API_BASE_URL = "http://localhost:8001"

def test_api_health():
    """Test API health endpoint"""
    print("🔍 Testing API Health...")
    try:
        response = requests.get(f"{API_BASE_URL}/health", timeout=5)
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        print("✅ API Health: PASSED")
        return True
    except Exception as e:
        print(f"❌ API Health: FAILED - {e}")
        return False

def test_single_search():
    """Test single flight search"""
    print("\n🔍 Testing Single Flight Search...")
    try:
        payload = {
            "trip_type": "one-way",
            "origin": "New York",
            "destination": "Los Angeles",
            "depart_date": (datetime.now() + timedelta(days=7)).strftime("%Y-%m-%d"),
            "adults": 1,
            "fetch_mode": "local"
        }
        response = requests.post(f"{API_BASE_URL}/search", json=payload, timeout=30)
        assert response.status_code == 200
        data = response.json()
        assert "flights" in data
        print(f"✅ Single Search: PASSED - Found {data.get('total_flights', 0)} flights")
        return True
    except Exception as e:
        print(f"❌ Single Search: FAILED - {e}")
        return False

def test_round_trip_search():
    """Test round-trip flight search"""
    print("\n🔍 Testing Round-Trip Flight Search...")
    try:
        payload = {
            "trip_type": "round-trip",
            "origin": "New York",
            "destination": "Los Angeles",
            "depart_date": (datetime.now() + timedelta(days=7)).strftime("%Y-%m-%d"),
            "return_date": (datetime.now() + timedelta(days=14)).strftime("%Y-%m-%d"),
            "adults": 1,
            "fetch_mode": "local"
        }
        response = requests.post(f"{API_BASE_URL}/search", json=payload, timeout=30)
        assert response.status_code == 200
        data = response.json()
        assert "flights" in data
        print(f"✅ Round-Trip Search: PASSED - Found {data.get('total_flights', 0)} flights")
        return True
    except Exception as e:
        print(f"❌ Round-Trip Search: FAILED - {e}")
        return False

def test_multi_city_search():
    """Test multi-city flight search"""
    print("\n🔍 Testing Multi-City Flight Search...")
    try:
        payload = {
            "trip_type": "multi-city",
            "segments": [
                {
                    "origin": "New York",
                    "destination": "Los Angeles",
                    "depart_date": (datetime.now() + timedelta(days=7)).strftime("%Y-%m-%d")
                },
                {
                    "origin": "Los Angeles",
                    "destination": "San Francisco",
                    "depart_date": (datetime.now() + timedelta(days=14)).strftime("%Y-%m-%d")
                }
            ],
            "adults": 1,
            "fetch_mode": "local"
        }
        response = requests.post(f"{API_BASE_URL}/search", json=payload, timeout=60)
        assert response.status_code == 200
        data = response.json()
        assert "flights" in data
        print(f"✅ Multi-City Search: PASSED - Found {data.get('total_flights', 0)} flights")
        return True
    except Exception as e:
        print(f"❌ Multi-City Search: FAILED - {e}")
        return False

def test_price_alert():
    """Test price alert creation"""
    print("\n🔍 Testing Price Alert Creation...")
    try:
        payload = {
            "trip_type": "one-way",
            "origin": "New York",
            "destination": "Los Angeles",
            "depart_date": (datetime.now() + timedelta(days=30)).strftime("%Y-%m-%d"),
            "target_price": 500.0,
            "currency": "USD",
            "email": "test@example.com",
            "notification_channels": ["email"]
        }
        response = requests.post(f"{API_BASE_URL}/alerts", json=payload, timeout=10)
        assert response.status_code == 200
        data = response.json()
        assert "alert_id" in data
        print(f"✅ Price Alert: PASSED - Created alert {data.get('alert_id', '')[:12]}")
        return True
    except Exception as e:
        print(f"❌ Price Alert: FAILED - {e}")
        return False

def test_webhook():
    """Test webhook registration"""
    print("\n🔍 Testing Webhook Registration...")
    try:
        payload = {"webhook_url": "https://example.com/webhook"}
        response = requests.post(f"{API_BASE_URL}/webhooks", data=payload, timeout=10)
        assert response.status_code == 200
        print("✅ Webhook Registration: PASSED")
        return True
    except Exception as e:
        print(f"❌ Webhook Registration: FAILED - {e}")
        return False

def test_validation():
    """Test input validation"""
    print("\n🔍 Testing Input Validation...")
    tests_passed = 0
    tests_total = 3
    
    # Test invalid airport code
    try:
        payload = {
            "trip_type": "one-way",
            "origin": "INVALID123",
            "destination": "ALSOINVALID",
            "depart_date": (datetime.now() + timedelta(days=7)).strftime("%Y-%m-%d"),
            "adults": 1
        }
        response = requests.post(f"{API_BASE_URL}/search", json=payload, timeout=10)
        assert response.status_code == 400
        tests_passed += 1
        print("  ✅ Invalid airport code validation: PASSED")
    except Exception as e:
        print(f"  ❌ Invalid airport code validation: FAILED - {e}")
    
    # Test same origin/destination
    try:
        payload = {
            "trip_type": "one-way",
            "origin": "JFK",
            "destination": "JFK",
            "depart_date": (datetime.now() + timedelta(days=7)).strftime("%Y-%m-%d"),
            "adults": 1
        }
        response = requests.post(f"{API_BASE_URL}/search", json=payload, timeout=10)
        assert response.status_code == 400
        tests_passed += 1
        print("  ✅ Same origin/destination validation: PASSED")
    except Exception as e:
        print(f"  ❌ Same origin/destination validation: FAILED - {e}")
    
    # Test past date
    try:
        payload = {
            "trip_type": "one-way",
            "origin": "JFK",
            "destination": "LAX",
            "depart_date": (datetime.now() - timedelta(days=1)).strftime("%Y-%m-%d"),
            "adults": 1
        }
        response = requests.post(f"{API_BASE_URL}/search", json=payload, timeout=10)
        assert response.status_code == 400
        tests_passed += 1
        print("  ✅ Past date validation: PASSED")
    except Exception as e:
        print(f"  ❌ Past date validation: FAILED - {e}")
    
    print(f"✅ Input Validation: {tests_passed}/{tests_total} tests passed")
    return tests_passed == tests_total

def test_export_format():
    """Test that search results can be exported"""
    print("\n🔍 Testing Export Format...")
    try:
        payload = {
            "trip_type": "one-way",
            "origin": "New York",
            "destination": "Los Angeles",
            "depart_date": (datetime.now() + timedelta(days=7)).strftime("%Y-%m-%d"),
            "adults": 1,
            "fetch_mode": "local"
        }
        response = requests.post(f"{API_BASE_URL}/search", json=payload, timeout=30)
        assert response.status_code == 200
        data = response.json()
        
        # Test JSON export
        json_str = json.dumps(data, indent=2, default=str)
        assert len(json_str) > 0
        print("  ✅ JSON export format: PASSED")
        
        # Test CSV-ready format
        if data.get('flights'):
            flights = data['flights']
            assert isinstance(flights, list)
            print("  ✅ CSV-ready format: PASSED")
        
        print("✅ Export Format: PASSED")
        return True
    except Exception as e:
        print(f"❌ Export Format: FAILED - {e}")
        return False

def main():
    """Run all tests"""
    print("=" * 60)
    print("🧪 FLYMIND API FEATURE TEST SUITE")
    print("=" * 60)
    
    results = []
    
    # Core API tests
    results.append(("API Health", test_api_health()))
    results.append(("Single Search", test_single_search()))
    results.append(("Round-Trip Search", test_round_trip_search()))
    results.append(("Multi-City Search", test_multi_city_search()))
    results.append(("Price Alert", test_price_alert()))
    results.append(("Webhook", test_webhook()))
    results.append(("Input Validation", test_validation()))
    results.append(("Export Format", test_export_format()))
    
    # Summary
    print("\n" + "=" * 60)
    print("📊 TEST SUMMARY")
    print("=" * 60)
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for name, result in results:
        status = "✅ PASSED" if result else "❌ FAILED"
        print(f"{status}: {name}")
    
    print(f"\nTotal: {passed}/{total} tests passed")
    print("=" * 60)
    
    if passed == total:
        print("🎉 All tests passed! All features are working correctly.")
    else:
        print("⚠️  Some tests failed. Please check the errors above.")
    
    return passed == total

if __name__ == "__main__":
    try:
        success = main()
        exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\n\n⚠️  Tests interrupted by user")
        exit(1)
    except Exception as e:
        print(f"\n\n❌ Test suite error: {e}")
        import traceback
        traceback.print_exc()
        exit(1)


