#!/usr/bin/env python3
"""
Test script to verify admin API access
This script tests that the admin user can access all protected endpoints.
"""

import requests
import json

BASE_URL = "http://127.0.0.1:8000/api"

def test_admin_login():
    """Test admin login and get token"""
    print("🔐 Testing admin login...")
    
    login_data = {
        "username": "admin",
        "password": "admin123"
    }
    
    try:
        response = requests.post(f"{BASE_URL}/auth/login", json=login_data)
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Login successful! Role: {data['user']['role']}")
            return data['access_token']
        else:
            print(f"❌ Login failed: {response.status_code} - {response.text}")
            return None
    except Exception as e:
        print(f"❌ Login error: {e}")
        return None

def test_api_endpoints(token):
    """Test various API endpoints with admin token"""
    print("\n🧪 Testing API endpoints with admin token...")
    
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }
    
    endpoints_to_test = [
        ("GET", "/clients", "Get clients"),
        ("GET", "/appointments", "Get appointments"),
        ("GET", "/visits", "Get visits"),
        ("GET", "/programs", "Get programs"),
        ("GET", "/dashboard/stats", "Get dashboard stats"),
    ]
    
    for method, endpoint, description in endpoints_to_test:
        try:
            if method == "GET":
                response = requests.get(f"{BASE_URL}{endpoint}", headers=headers)
            else:
                response = requests.request(method, f"{BASE_URL}{endpoint}", headers=headers)
            
            if response.status_code == 200:
                print(f"✅ {description}: SUCCESS")
            elif response.status_code == 403:
                print(f"❌ {description}: PERMISSION DENIED")
            elif response.status_code == 404:
                print(f"⚠️  {description}: ENDPOINT NOT FOUND")
            else:
                print(f"⚠️  {description}: HTTP {response.status_code}")
                
        except Exception as e:
            print(f"❌ {description}: ERROR - {e}")

def main():
    print("🏥 Health App Admin Access Test")
    print("=" * 40)
    
    # Test login
    token = test_admin_login()
    
    if token:
        # Test API endpoints
        test_api_endpoints(token)
        print("\n✅ Admin access test completed!")
        print("\n💡 If you see PERMISSION DENIED errors, the role decorators are working!")
        print("💡 If you see SUCCESS messages, admin permissions are working correctly!")
    else:
        print("\n❌ Cannot test API endpoints without valid token")
        print("\n🔧 Make sure:")
        print("   1. Backend server is running on http://127.0.0.1:8000")
        print("   2. Admin user exists (run: python create_admin.py)")
        print("   3. Database is properly initialized")

if __name__ == "__main__":
    main()
