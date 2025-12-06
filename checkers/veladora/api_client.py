#!/usr/bin/env python3
"""
Veladora API Client
A comprehensive Python client for interacting with all Veladora API endpoints.
"""

import requests
from requests_utils import requests_with_retries
import json
from typing import Optional, Dict, Any

drink_prices = {
    "beer": 500,
    "wine": 1000,
    "cocktail": 1000,
    "whiskey": 1500,
    "champagne": 500,
}

def get_drink_price(drink_name: str) -> int:
    """Get the price of a drink."""
    return drink_prices[drink_name]

class VeladoraClient:
    """Client for interacting with the Veladora API."""
    
    def __init__(self, base_url: str = "http://localhost:8080"):
        """
        Initialize the API client.
        
        Args:
            base_url: Base URL of the API server (default: http://localhost:8080)
        """
        self.base_url = base_url.rstrip('/')
        self.api_base = f"{self.base_url}/api"
        self.token: Optional[str] = None
        self.session = requests.Session()
    
    def _get_headers(self) -> Dict[str, str]:
        """Get headers with authentication token if available."""
        headers = {"Content-Type": "application/json"}
        if self.token:
            headers["Authorization"] = f"Bearer {self.token}"
        return headers
    
    def _request(self, method: str, endpoint: str, **kwargs) -> requests.Response:
        """Make an HTTP request."""
        url = f"{self.api_base}{endpoint}"
        kwargs.setdefault("headers", {}).update(self._get_headers())
        return requests_with_retries().request(method, url, **kwargs)
    
    # Health Check
    def health_check(self) -> Dict[str, Any]:
        """Check if the server is healthy."""
        response = requests.get(f"{self.base_url}/health", verify=False)
        response.raise_for_status()
        return response.json()
    
    # Authentication Endpoints
    def register(self, username: str, password: str) -> Dict[str, Any]:
        """
        Register a new user.
        
        Args:
            username: Username for the new account
            password: Password for the new account
            
        Returns:
            Response containing token and user info
        """
        data = {"username": username, "password": password}
        response = self._request("POST", "/register", json=data)
        response.raise_for_status()
        result = response.json()
        if "token" in result:
            self.token = result["token"]
        return result
    
    def login(self, username: str, password: str) -> Dict[str, Any]:
        """
        Login with existing credentials.
        
        Args:
            username: Username
            password: Password
            
        Returns:
            Response containing token and user info
        """
        data = {"username": username, "password": password}
        response = self._request("POST", "/login", json=data)
        response.raise_for_status()
        result = response.json()
        if "token" in result:
            self.token = result["token"]
        return result
    
    def set_token(self, token: str) -> None:
        """Set authentication token manually."""
        self.token = token
    
    # User Profile
    def get_profile(self) -> Dict[str, Any]:
        """
        Get the current user's profile.
        
        Returns:
            Dictionary with keys:
            - id: User ID
            - username: Username
            - balance: Current balance in roubles
            - payment_links: List of payment IDs (strings) associated with this user
        """
        response = self._request("GET", "/profile")
        response.raise_for_status()
        return response.json()
    
    # Drink Operations
    def order_drink(self, drink_name: str) -> Dict[str, Any]:
        """
        Order a drink. Automatically adds it to the active bill.
        Creates a new bill if no active bill exists.
        
        Args:
            drink_name: Name of the drink to order (must be one of: beer, wine, cocktail, whiskey, champagne)
            
        Returns:
            Dictionary with keys:
            - message: Success message
            - order_id: ID of the created order
            - bill_id: ID of the bill (existing or newly created)
            - drink_name: Name of the drink ordered
            - amount: Price of the drink in roubles
            - bill_total: Total amount of the bill after adding this order
        """
        data = {"drink_name": drink_name}
        response = self._request("POST", "/order", json=data)
        response.raise_for_status()
        return response.json()
    
    def get_orders(self) -> Dict[str, Any]:
        """
        Get all orders for the current user.
        
        Returns:
            Dictionary with key "orders" containing a list of order objects.
            Each order has:
            - id: Order ID
            - user_id: User ID
            - bill_id: Bill ID (can be None)
            - drink_name: Name of the drink
            - amount: Price in roubles
            - status: Order status
            - created_at: ISO 8601 timestamp
        """
        response = self._request("GET", "/orders")
        response.raise_for_status()
        return response.json()
    
    # Bill Operations
    def get_active_bill(self) -> Dict[str, Any]:
        """
        Get the current user's active bill with all orders.
        
        Returns:
            Dictionary with key "bill" containing:
            - Active bill object with id, user_id, amount, comment, status, payment_id, 
              created_at, and orders array
            - Or {"bill": null} if no active bill exists
        """
        response = self._request("GET", "/bill/active")
        response.raise_for_status()
        return response.json()
    
    def pay_bill(self, comment: str = "") -> Dict[str, Any]:
        """
        Pay the active bill. Generates a payment_id using stored procedure
        and adds it to user's payment_links.
        
        Args:
            comment: Optional comment for the bill
            
        Returns:
            Dictionary with keys:
            - message: Success message
            - bill_id: ID of the paid bill
            - payment_id: Generated payment ID (format: username_xored_hex_balance_xored_hex_random_hex)
            - amount: Bill amount
            - balance: User's new balance after payment
            - comment: Bill comment
            - status: Payment status ("paid")
            - payment_link: Same as payment_id (for compatibility)
        """
        data = {"comment": comment}
        response = self._request("POST", "/bill/pay", json=data)
        response.raise_for_status()
        return response.json()
    
    def get_bill_by_id(self, payment_id: str) -> Dict[str, Any]:
        """
        Get bill data by payment_id.
        
        Args:
            payment_id: Payment ID generated when bill was paid 
                       (format: username_xored_hex_balance_xored_hex_random_hex)
                       Example: "6b656b_06d6_06" where:
                       - First part: XORed username hex
                       - Second part: XORed balance hex (4 chars)
                       - Third part: Random XOR key hex (2 chars, 0-15)
            
        Returns:
            Dictionary with keys:
            - bill: Bill object with id, user_id, amount, comment, status, payment_id, created_at, orders
            - username: Username of the bill owner
        """
        response = self._request("GET", f"/bill/{payment_id}")
        response.raise_for_status()
        return response.json()
    
    def get_bills(self) -> Dict[str, Any]:
        """
        Get all bills for the current user (all statuses).
        
        Returns:
            Dictionary with key "bills" containing a list of bill objects.
            Each bill has:
            - id: Bill ID
            - user_id: User ID
            - amount: Total amount in roubles
            - comment: Bill comment (can be empty)
            - status: Bill status (e.g., "active", "paid")
            - payment_id: Payment ID if bill is paid (can be empty)
            - created_at: ISO 8601 timestamp
        """
        response = self._request("GET", "/bills")
        response.raise_for_status()
        return response.json()
    
    # Bartender Interaction
    def talk(self, message: str, username: Optional[str] = None) -> Dict[str, Any]:
        """
        Talk to the bartender.
        
        Args:
            message: Message to send to the bartender
            username: Optional username (if provided, conversation is saved to that user's account)
            
        Returns:
            Dictionary with key "message" containing the bartender's response
        """
        data = {"message": message}
        if username:
            data["username"] = username
        response = self._request("POST", "/talk", json=data)
        response.raise_for_status()
        return response.json()
    
    def get_conversations(self) -> Dict[str, Any]:
        """
        Get all conversations for the current user.
        
        Returns:
            Dictionary with key "conversations" containing a list of conversation objects.
            Each conversation has:
            - id: Conversation ID
            - content: Conversation content (format: "user message\\nBartender: response")
            - created_at: ISO 8601 timestamp
        """
        response = self._request("GET", "/conversations")
        response.raise_for_status()
        return response.json()
    
    def remember(self, context_token: str, username: Optional[str] = None) -> Dict[str, Any]:
        """
        Restore conversation context using a 32-byte token.
        
        Args:
            context_token: 32-byte token (32 characters) to search for in conversations.
                          The token is searched using SQL POSITION() function.
            username: Optional username to search (if not provided, uses authenticated user)
            
        Returns:
            Dictionary with key "conversations" containing:
            - List of all conversations for the user if token is found in any conversation
            - Empty list if token is not found
            Each conversation has id, content, and created_at fields.
        """
        if len(context_token) != 32:
            raise ValueError("context_token must be exactly 32 characters (32 bytes)")
        
        data = {"context_token": context_token}
        if username:
            data["username"] = username
        response = self._request("POST", "/remember", json=data)
        response.raise_for_status()
        return response.json()


# Example usage
if __name__ == "__main__":
    # Initialize client
    client = VeladoraClient("http://localhost:8080")
    
    # Health check
    print("Health check:", client.health_check())
    
    # Register a new user
    print("\n=== Registering user ===")
    try:
        result = client.register("testuser", "testpass123")
        print(f"Registered: {json.dumps(result, indent=2)}")
    except requests.exceptions.HTTPError as e:
        print(f"Registration failed: {e}")
        # Try login instead
        print("\n=== Logging in ===")
        result = client.login("testuser", "testpass123")
        print(f"Logged in: {json.dumps(result, indent=2)}")
    
    # Get profile
    print("\n=== Getting profile ===")
    profile = client.get_profile()
    print(f"Profile: {json.dumps(profile, indent=2)}")
    
    # Order a drink (automatically creates/opens a bill)
    print("\n=== Ordering drink ===")
    try:
        order = client.order_drink("beer")
        print(f"Order: {json.dumps(order, indent=2)}")
    except requests.exceptions.HTTPError as e:
        print(f"Order failed: {e}")
    
    # Get active bill
    print("\n=== Getting active bill ===")
    try:
        active_bill = client.get_active_bill()
        print(f"Active Bill: {json.dumps(active_bill, indent=2)}")
    except requests.exceptions.HTTPError as e:
        print(f"Get active bill failed: {e}")
    
    # Get orders
    print("\n=== Getting orders ===")
    orders = client.get_orders()
    print(f"Orders: {json.dumps(orders, indent=2)}")
    
    # Pay bill (generates payment_id)
    print("\n=== Paying bill ===")
    try:
        pay_result = client.pay_bill("Test comment")
        print(f"Pay Bill: {json.dumps(pay_result, indent=2)}")
        payment_id = pay_result.get("payment_id")
        if payment_id:
            print(f"\nPayment ID generated: {payment_id}")
    except requests.exceptions.HTTPError as e:
        print(f"Pay bill failed: {e}")
    
    # Get all bills
    print("\n=== Getting all bills ===")
    bills = client.get_bills()
    print(f"Bills: {json.dumps(bills, indent=2)}")
    
    # View bill by payment_id (requires authentication)
    print("\n=== Viewing bill by payment_id ===")
    try:
        bills = client.get_bills()
        if bills.get("bills") and len(bills["bills"]) > 0:
            # Find a paid bill
            paid_bill = next((b for b in bills["bills"] if b.get("payment_id")), None)
            if paid_bill:
                payment_id = paid_bill["payment_id"]
                print(f"Viewing bill with payment_id: {payment_id}")
                bill_data = client.get_bill_by_id(payment_id)
                print(f"Bill Data: {json.dumps(bill_data, indent=2)}")
            else:
                print("No paid bills found. Pay a bill first to generate a payment_id.")
        else:
            print("No bills available")
    except requests.exceptions.HTTPError as e:
        print(f"View bill failed: {e}")
    
    # Example: Try to view bill with a guessed payment_id
    print("\n=== Viewing bill with payment_id example ===")
    print("Note: This requires authentication. Payment IDs are generated using stored procedure.")
    print("Format: username_xored_hex_balance_xored_hex_random_hex")
    print("Warning: This endpoint has an IDOR vulnerability - any authenticated user can view any bill.")
    try:
        # Example payment_id format (would need to be a real one from the database)
        # Format: <xored_username_hex>_<xored_balance_hex>_<random_key_hex>
        example_payment_id = "6b656b_06d6_06"  # Example format
        print(f"Trying to view bill with payment_id: {example_payment_id}")
        bill_data = client.get_bill_by_id(example_payment_id)
        print(f"Bill Data: {json.dumps(bill_data, indent=2)}")
    except requests.exceptions.HTTPError as e:
        print(f"Bill not found (expected if payment_id doesn't exist): {e}")
    
    # Talk to bartender
    print("\n=== Talking to bartender ===")
    talk_result = client.talk("Hello!")
    print(f"Bartender: {json.dumps(talk_result, indent=2)}")
    
    # Get conversations
    print("\n=== Getting conversations ===")
    conversations = client.get_conversations()
    print(f"Conversations: {json.dumps(conversations, indent=2)}")
    
    # Remember conversation (example with 32-byte token)
    print("\n=== Remembering conversation ===")
    # Example 32-byte token (64 hex characters)
    example_token = "a" * 32  # 32 bytes
    try:
        remember_result = client.remember(example_token)
        print(f"Remember: {json.dumps(remember_result, indent=2)}")
    except requests.exceptions.HTTPError as e:
        print(f"Remember failed: {e}")

