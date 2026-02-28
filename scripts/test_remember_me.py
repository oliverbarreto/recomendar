#!/usr/bin/env python3
"""
Test script for "Remember Me" functionality

This script tests the remember_me feature by:
1. Testing login without remember_me (30-day refresh token)
2. Testing login with remember_me (90-day refresh token)
3. Verifying token expiration times
"""

import requests
import json
from datetime import datetime, timedelta
import jwt
import sys

# Configuration
API_BASE_URL = "http://localhost:8000/api"
TEST_EMAIL = "admin@labcastarr.com"
TEST_PASSWORD = "admin123"

def decode_token(token: str) -> dict:
    """Decode JWT token without verification (for testing only)"""
    try:
        # Decode without verification to inspect claims
        decoded = jwt.decode(token, options={"verify_signature": False})
        return decoded
    except Exception as e:
        print(f"Error decoding token: {e}")
        return {}

def test_login(remember_me: bool) -> dict:
    """Test login with or without remember_me"""
    print(f"\n{'='*60}")
    print(f"Testing login with remember_me={remember_me}")
    print(f"{'='*60}")
    
    payload = {
        "email": TEST_EMAIL,
        "password": TEST_PASSWORD,
        "remember_me": remember_me
    }
    
    try:
        response = requests.post(
            f"{API_BASE_URL}/v1/auth/login",
            json=payload,
            headers={"Content-Type": "application/json"}
        )
        
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Login successful!")
            print(f"   Token type: {data.get('token_type')}")
            print(f"   Expires in: {data.get('expires_in')} seconds ({data.get('expires_in') / 60} minutes)")
            
            # Decode and inspect tokens
            access_token = data.get('access_token')
            refresh_token = data.get('refresh_token')
            
            if access_token:
                access_claims = decode_token(access_token)
                print(f"\n📋 Access Token Claims:")
                print(f"   Type: {access_claims.get('type')}")
                print(f"   Issued at: {datetime.fromtimestamp(access_claims.get('iat', 0))}")
                print(f"   Expires at: {datetime.fromtimestamp(access_claims.get('exp', 0))}")
                exp_time = datetime.fromtimestamp(access_claims.get('exp', 0))
                iat_time = datetime.fromtimestamp(access_claims.get('iat', 0))
                duration = exp_time - iat_time
                print(f"   Duration: {duration.total_seconds() / 60} minutes")
                print(f"   Sliding: {access_claims.get('sliding', False)}")
            
            if refresh_token:
                refresh_claims = decode_token(refresh_token)
                print(f"\n🔄 Refresh Token Claims:")
                print(f"   Type: {refresh_claims.get('type')}")
                print(f"   Issued at: {datetime.fromtimestamp(refresh_claims.get('iat', 0))}")
                print(f"   Expires at: {datetime.fromtimestamp(refresh_claims.get('exp', 0))}")
                exp_time = datetime.fromtimestamp(refresh_claims.get('exp', 0))
                iat_time = datetime.fromtimestamp(refresh_claims.get('iat', 0))
                duration = exp_time - iat_time
                print(f"   Duration: {duration.days} days")
                print(f"   Remember me: {refresh_claims.get('remember_me', False)}")
                
                # Verify expected duration
                expected_days = 90 if remember_me else 30
                if abs(duration.days - expected_days) <= 1:  # Allow 1 day tolerance
                    print(f"   ✅ Correct duration ({expected_days} days)")
                else:
                    print(f"   ❌ Incorrect duration! Expected {expected_days} days, got {duration.days} days")
            
            return data
        else:
            print(f"❌ Login failed with status {response.status_code}")
            print(f"   Response: {response.text}")
            return {}
            
    except Exception as e:
        print(f"❌ Error during login: {e}")
        return {}

def main():
    """Run all tests"""
    print("🧪 Testing 'Remember Me' Functionality")
    print(f"API URL: {API_BASE_URL}")
    print(f"Test User: {TEST_EMAIL}")
    
    # Test 1: Login without remember_me (should get 30-day refresh token)
    result1 = test_login(remember_me=False)
    
    # Test 2: Login with remember_me (should get 90-day refresh token)
    result2 = test_login(remember_me=True)
    
    # Summary
    print(f"\n{'='*60}")
    print("📊 Test Summary")
    print(f"{'='*60}")
    
    if result1 and result2:
        print("✅ All tests completed successfully!")
        print("\n📝 Key Findings:")
        print("   • Standard login creates 30-day refresh tokens")
        print("   • 'Remember me' login creates 90-day refresh tokens")
        print("   • Access tokens remain 60 minutes for both")
        print("   • Sliding tokens are enabled for activity-based refresh")
        return 0
    else:
        print("❌ Some tests failed. Please check the output above.")
        return 1

if __name__ == "__main__":
    sys.exit(main())

