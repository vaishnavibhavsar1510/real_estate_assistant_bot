from typing import Optional, Dict, Any
from .issue_detector.agent import IssueDetectorAgent
from .faq_agent.agent import TenancyFAQAgent

class AgentRouter:
    def __init__(self):
        self.issue_detector = IssueDetectorAgent()
        self.tenancy_faq = TenancyFAQAgent()
        
        # Keywords for classification
        self.tenancy_keywords = [
            "rent", "lease", "landlord", "tenant", "evict", 
            "deposit", "notice", "contract", "agreement"
        ]
        self.issue_keywords = [
            "damage", "broken", "leak", "mold", "crack",
            "repair", "fix", "issue", "problem", "wrong"
        ]

    async def route_message(
        self, 
        message: str, 
        image_path: Optional[str] = None,
        location: Optional[str] = None
    ) -> Dict[str, Any]:
        """Route the message to appropriate agent"""
        
        # If image is present, always use Issue Detector
        if image_path:
            return await self.issue_detector.analyze_image(image_path, message)
            
        # Check message keywords for routing
        message_lower = message.lower()
        
        # Check for tenancy-related keywords
        if any(keyword in message_lower for keyword in self.tenancy_keywords):
            response = await self.tenancy_faq.get_response(message, location)
            return {
                "agent": "tenancy_faq",
                "response": response
            }
            
        # Check for issue-related keywords
        if any(keyword in message_lower for keyword in self.issue_keywords):
            return {
                "agent": "issue_detector",
                "response": "I can help you better if you upload an image of the issue. Could you please share a photo?"
            }
            
        # If unclear, ask for clarification
        return {
            "agent": "router",
            "response": "I can help you with property issues (please share an image) or tenancy questions. Could you clarify if this is about a property issue or a tenancy matter?"
        } 