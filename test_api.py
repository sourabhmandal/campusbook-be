"""
Test script for the authentication API endpoints.
This script demonstrates how to use the class-based authentication API.
"""

import requests
import json
from typing import Dict, Any

# API Base URL
BASE_URL = "http://localhost:8000/users"

# Test data
TEST_USER = {
    "email": "testuser@example.com",
    "username": "testuser",
    "password": "TestPassword123!",
    "password_confirm": "TestPassword123!",
    "first_name": "Test",
    "last_name": "User",
    "phone_number": "+1234567890"
}

LOGIN_DATA = {
    "email": TEST_USER["email"],
    "password": TEST_USER["password"],
    "remember_me": False
}


def make_request(method: str, endpoint: str, data: Dict[str, Any] = None, headers: Dict[str, str] = None) -> requests.Response:
    """Make HTTP request to API endpoint."""
    url = f"{BASE_URL}{endpoint}"
    
    if headers is None:
        headers = {"Content-Type": "application/json"}
    
    if method.upper() == "GET":
        return requests.get(url, headers=headers)
    elif method.upper() == "POST":
        return requests.post(url, json=data, headers=headers)
    elif method.upper() == "PUT":
        return requests.put(url, json=data, headers=headers)
    else:
        raise ValueError(f"Unsupported method: {method}")


def test_user_registration():
    """Test user registration endpoint."""
    print("=== Testing User Registration ===")
    
    response = make_request("POST", "/auth/register/", TEST_USER)
    
    print(f"Status Code: {response.status_code}")
    print(f"Response: {json.dumps(response.json(), indent=2)}")
    
    if response.status_code == 201:
        print("✅ Registration successful!")
        return response.json()["data"]["tokens"]
    else:
        print("❌ Registration failed!")
        return None


def test_user_login():
    """Test user login endpoint."""
    print("\n=== Testing User Login ===")
    
    response = make_request("POST", "/auth/login/", LOGIN_DATA)
    
    print(f"Status Code: {response.status_code}")
    print(f"Response: {json.dumps(response.json(), indent=2)}")
    
    if response.status_code == 200:
        print("✅ Login successful!")
        return response.json()["data"]["tokens"]
    else:
        print("❌ Login failed!")
        return None


def test_user_profile(access_token: str):
    """Test user profile endpoint."""
    print("\n=== Testing User Profile ===")
    
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {access_token}"
    }
    
    response = make_request("GET", "/profile/", headers=headers)
    
    print(f"Status Code: {response.status_code}")
    print(f"Response: {json.dumps(response.json(), indent=2)}")
    
    if response.status_code == 200:
        print("✅ Profile retrieval successful!")
    else:
        print("❌ Profile retrieval failed!")


def test_token_refresh(refresh_token: str):
    """Test token refresh endpoint."""
    print("\n=== Testing Token Refresh ===")
    
    refresh_data = {"refresh_token": refresh_token}
    response = make_request("POST", "/auth/refresh/", refresh_data)
    
    print(f"Status Code: {response.status_code}")
    print(f"Response: {json.dumps(response.json(), indent=2)}")
    
    if response.status_code == 200:
        print("✅ Token refresh successful!")
        return response.json()["data"]["access_token"]
    else:
        print("❌ Token refresh failed!")
        return None


def test_user_logout(refresh_token: str):
    """Test user logout endpoint."""
    print("\n=== Testing User Logout ===")
    
    logout_data = {"refresh_token": refresh_token}
    response = make_request("POST", "/auth/logout/", logout_data)
    
    print(f"Status Code: {response.status_code}")
    print(f"Response: {json.dumps(response.json(), indent=2)}")
    
    if response.status_code == 200:
        print("✅ Logout successful!")
    else:
        print("❌ Logout failed!")


def main():
    """Run all API tests."""
    print("🚀 Starting API Authentication Tests")
    print("Make sure the Django development server is running on localhost:8000")
    print("-" * 60)
    
    try:
        # Test registration
        tokens = test_user_registration()
        if not tokens:
            print("❌ Cannot continue tests without successful registration")
            return
        
        access_token = tokens["access_token"]
        refresh_token = tokens["refresh_token"]
        
        # Test profile access
        test_user_profile(access_token)
        
        # Test token refresh
        new_access_token = test_token_refresh(refresh_token)
        if new_access_token:
            access_token = new_access_token
        
        # Test logout
        test_user_logout(refresh_token)
        
        # Test login with existing user
        login_tokens = test_user_login()
        
        print("\n" + "=" * 60)
        print("🎉 All tests completed!")
        
    except requests.exceptions.ConnectionError:
        print("❌ Connection Error: Make sure the Django server is running")
    except Exception as e:
        print(f"❌ Unexpected error: {str(e)}")


if __name__ == "__main__":
    main()
