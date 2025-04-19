from openai import OpenAI
import os
from typing import Optional, Dict, Any
import json

class TenancyFAQAgent:
    def __init__(self):
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            raise ValueError("OPENAI_API_KEY environment variable is not set")
        self.client = OpenAI()  # OpenAI will automatically use the environment variable
        
        self.faq_data = {
            "eviction": {
                "general": {
                    "answer": "Landlords must provide written notice before eviction. The notice period varies by location.",
                    "follow_up": "Would you like to know the specific notice period required in your area?"
                },
                "emergency": {
                    "answer": "In emergency cases like non-payment or illegal activity, shorter notice periods may apply.",
                    "follow_up": "Has your landlord specified the reason for eviction?"
                }
            },
            "rent_increase": {
                "general": {
                    "answer": "Rent increases are typically allowed at the end of a lease term with proper notice.",
                    "follow_up": "When did you receive notice of the rent increase?"
                },
                "mid_lease": {
                    "answer": "Mid-lease rent increases are generally not allowed unless specified in the lease agreement.",
                    "follow_up": "Would you like me to explain what your lease should say about rent increases?"
                }
            },
            "deposit": {
                "general": {
                    "answer": "Security deposits must be returned within a specified period after move-out, minus any legitimate deductions.",
                    "follow_up": "Have you already moved out and submitted your forwarding address?"
                },
                "dispute": {
                    "answer": "If there's a dispute about deductions, you should:\n1. Request an itemized list of deductions\n2. Gather evidence (photos, videos)\n3. Send a formal dispute letter\n4. Consider mediation or small claims court",
                    "follow_up": "Would you like a template for a formal dispute letter?"
                }
            },
            "repairs": {
                "general": {
                    "answer": "Landlords are responsible for maintaining the property in a habitable condition and making necessary repairs.",
                    "follow_up": "Have you notified your landlord about the needed repairs in writing?"
                },
                "emergency": {
                    "answer": "Emergency repairs (like no heat, water, or electricity) require immediate attention from the landlord.",
                    "follow_up": "Is this an emergency repair situation?"
                }
            }
        }

    async def get_response(self, message: str, location: Optional[str] = None) -> Dict[str, Any]:
        """Generate response for tenancy-related questions"""
        message = message.lower()
        response = {
            "answer": "",
            "follow_up": None,
            "location_specific": None
        }

        # Check for keywords and generate response
        if "evict" in message or "notice to quit" in message:
            if "emergency" in message or "immediate" in message:
                response.update(self.faq_data["eviction"]["emergency"])
            else:
                response.update(self.faq_data["eviction"]["general"])
                
        elif "rent" in message and ("increase" in message or "raise" in message):
            if "middle" in message or "during" in message:
                response.update(self.faq_data["rent_increase"]["mid_lease"])
            else:
                response.update(self.faq_data["rent_increase"]["general"])
                
        elif "deposit" in message or "security" in message:
            if "dispute" in message or "deduction" in message:
                response.update(self.faq_data["deposit"]["dispute"])
            else:
                response.update(self.faq_data["deposit"]["general"])
                
        elif "repair" in message or "fix" in message:
            if "emergency" in message or "urgent" in message:
                response.update(self.faq_data["repairs"]["emergency"])
            else:
                response.update(self.faq_data["repairs"]["general"])
        else:
            response = {
                "answer": "I can help you with questions about eviction, rent increases, deposits, repairs, and other tenancy matters. Please be more specific about your concern.",
                "follow_up": "What specific aspect of tenancy would you like to know about?",
                "location_specific": None
            }

        # Add location-specific note if location is provided
        if location:
            response["location_specific"] = f"\n\nNote: Laws may vary in {location}. Please consult local regulations or a legal professional for specific advice."
            
        return response

    def _get_location_specific_info(self, location: str) -> dict:
        # This could be expanded to include more location-specific data
        # For now, returning a basic structure
        return {
            "notice_periods": {
                "eviction": "Varies by location",
                "rent_increase": "Varies by location"
            },
            "deposit_rules": {
                "maximum_amount": "Varies by location",
                "return_period": "Varies by location"
            }
        } 