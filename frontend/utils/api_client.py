import requests
import streamlit as st
from typing import List, Dict, Optional


class APIClient:
    
    def __init__(self, base_url: str = "http://localhost:8000"):
        self.base_url = base_url
    
    def _handle_response(self, response):
        """Handle API response"""
        if response.status_code == 200:
            return response.json()
        else:
            st.error(f"API Error: {response.status_code}")
            return None
    
    # products
    def get_products(self, category: Optional[str] = None) -> List[Dict]:
        """Get all products"""
        url = f"{self.base_url}/products"
        params = {"category": category} if category else {}
        
        try:
            response = requests.get(url, params=params)
            return self._handle_response(response) or []
        except Exception as e:
            st.error(f"Connection error: {e}")
            return []
    
    def get_product(self, product_id: int) -> Optional[Dict]:
        """Get single product"""
        url = f"{self.base_url}/products/{product_id}"
        
        try:
            response = requests.get(url)
            return self._handle_response(response)
        except Exception as e:
            st.error(f"Connection error: {e}")
            return None
    
    def get_categories(self) -> List[str]:
        """Get all categories"""
        url = f"{self.base_url}/categories"
        
        try:
            response = requests.get(url)
            return self._handle_response(response) or []
        except Exception as e:
            st.error(f"Connection error: {e}")
            return []
    
    # users
    def get_users(self) -> List[Dict]:
        """Get all users"""
        url = f"{self.base_url}/users"
        
        try:
            response = requests.get(url)
            return self._handle_response(response) or []
        except Exception as e:
            st.error(f"Connection error: {e}")
            return []
    
    def get_user(self, user_id: int) -> Optional[Dict]:
        """Get single user"""
        url = f"{self.base_url}/users/{user_id}"
        
        try:
            response = requests.get(url)
            return self._handle_response(response)
        except Exception as e:
            st.error(f"Connection error: {e}")
            return None
    
    # interactions
    def track_interaction(self, user_id: int, product_id: int, 
                         interaction_type: str) -> bool:
        """Track user interaction"""
        url = f"{self.base_url}/interactions"
        
        data = {
            "user_id": user_id,
            "product_id": product_id,
            "interaction_type": interaction_type
        }
        
        try:
            response = requests.post(url, json=data)
            return response.status_code == 200
        except Exception as e:
            st.error(f"Connection error: {e}")
            return False
    
    def get_user_interactions(self, user_id: int) -> List[Dict]:
        """Get user's interaction history"""
        url = f"{self.base_url}/users/{user_id}/interactions"
        
        try:
            response = requests.get(url)
            return self._handle_response(response) or []
        except Exception as e:
            st.error(f"Connection error: {e}")
            return []
    
    # recommendations (core)
    def get_recommendations(self, user_id: int, n: int = 10, 
                          personality: str = 'friendly',
                          include_explanations: bool = True) -> Dict:
        """Get personalized recommendations"""
        url = f"{self.base_url}/recommendations/{user_id}"
        
        params = {
            "n": n,
            "personality": personality,
            "include_explanations": include_explanations
        }
        
        try:
            response = requests.get(url, params=params)
            return self._handle_response(response) or {"recommendations": []}
        except Exception as e:
            st.error(f"Connection error: {e}")
            return {"recommendations": []}
    
    # analytics
    def get_user_analytics(self, user_id: int) -> Dict:
        """Get user behavior analytics"""
        url = f"{self.base_url}/analytics/user/{user_id}"
        
        try:
            response = requests.get(url)
            return self._handle_response(response) or {}
        except Exception as e:
            st.error(f"Connection error: {e}")
            return {}
    
    # health check
    def health_check(self) -> bool:
        """Check if API is running"""
        try:
            response = requests.get(f"{self.base_url}/", timeout=2)
            return response.status_code == 200
        except:
            return False


# global API client instance
@st.cache_resource
def get_api_client():
    """Get cached API client"""
    return APIClient()