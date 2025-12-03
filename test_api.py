"""
Test script for the EV Betting API

This script demonstrates how to interact with the API endpoints.
Make sure the API server is running before executing this script.

Run the API server first:
    python api.py

Then run this test script:
    python test_api.py
"""

import requests
import json

# API base URL
BASE_URL = "http://localhost:8000"

def print_response(title, response):
    """Helper function to print API responses"""
    print(f"\n{'='*60}")
    print(f"{title}")
    print(f"{'='*60}")
    print(f"Status Code: {response.status_code}")
    if response.status_code == 200:
        data = response.json()
        print(json.dumps(data, indent=2, default=str))
    else:
        print(f"Error: {response.text}")
    print()

def test_api():
    """Test various API endpoints"""
    
    # Test 1: Health check
    print("\n" + "="*60)
    print("Testing API Endpoints")
    print("="*60)
    
    response = requests.get(f"{BASE_URL}/health")
    print_response("1. Health Check", response)
    
    # Test 2: Get all active bets (limited to 10)
    response = requests.get(f"{BASE_URL}/bets", params={"limit": 10})
    print_response("2. Get All Active Bets (Limited to 10)", response)
    
    # Test 3: Get PrizePicks bets only
    response = requests.get(f"{BASE_URL}/bets", params={
        "bookmaker": "prizepicks",
        "limit": 10
    })
    print_response("3. Get PrizePicks Bets Only", response)
    
    # Test 4: Get Underdog bets only
    response = requests.get(f"{BASE_URL}/bets", params={
        "bookmaker": "underdog",
        "limit": 10
    })
    print_response("4. Get Underdog Bets Only", response)
    
    # Test 5: Get bets with minimum 5% EV
    response = requests.get(f"{BASE_URL}/bets", params={
        "min_ev": 5.0,
        "limit": 10
    })
    print_response("5. Get Bets with Minimum 5% EV", response)
    
    # Test 6: Get NFL bets
    response = requests.get(f"{BASE_URL}/bets", params={
        "sport": "NFL",
        "limit": 10
    })
    print_response("6. Get NFL Bets", response)
    
    # Test 7: Get bet statistics
    response = requests.get(f"{BASE_URL}/bets/stats")
    print_response("7. Get Bet Statistics", response)
    
    # Test 8: Get available bookmakers
    response = requests.get(f"{BASE_URL}/bets/bookmakers")
    print_response("8. Get Available Bookmakers", response)
    
    # Test 9: Get available markets
    response = requests.get(f"{BASE_URL}/bets/markets")
    print_response("9. Get Available Markets", response)
    
    # Test 10: Get PrizePicks bets using dedicated endpoint
    response = requests.get(f"{BASE_URL}/bets/by-bookmaker/prizepicks", params={"limit": 5})
    print_response("10. Get PrizePicks Bets (Dedicated Endpoint)", response)

    print("\n" + "="*60)
    print("Testing Complete!")
    print("="*60 + "\n")

if __name__ == "__main__":
    try:
        # First check if API is running
        response = requests.get(f"{BASE_URL}/health", timeout=2)
        if response.status_code == 200:
            test_api()
        else:
            print("API is not responding correctly. Please make sure it's running.")
    except requests.exceptions.ConnectionError:
        print("\nError: Could not connect to the API server.")
        print("Please make sure the API is running:")
        print("  python api.py")
        print("\nThen run this test script again.")
    except Exception as e:
        print(f"\nError: {e}")






