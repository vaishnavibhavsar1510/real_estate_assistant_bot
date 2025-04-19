from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from typing import Optional, List, Dict, Any
import os
from dotenv import load_dotenv
import torch
from PIL import Image
from transformers import CLIPProcessor, CLIPModel
import cloudinary
import cloudinary.uploader
import numpy as np
from datetime import datetime
import requests
from io import BytesIO
import shutil
import aiofiles
import time
import json

from database import get_db, get_vector_store

# Load environment variables
load_dotenv()

# Configure Cloudinary
cloudinary.config(
    cloud_name = os.getenv('CLOUDINARY_CLOUD_NAME'),
    api_key = os.getenv('CLOUDINARY_API_KEY'),
    api_secret = os.getenv('CLOUDINARY_API_SECRET')
)

app = FastAPI(title="Real Estate Chatbot API")

# Configure CORS with more specific settings
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3001", "http://127.0.0.1:3001"],  # Allow both localhost variations
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["*"]
)

# Initialize CLIP model and processor
model = CLIPModel.from_pretrained("openai/clip-vit-base-patch32")
processor = CLIPProcessor.from_pretrained("openai/clip-vit-base-patch32")

class ChatMessage(BaseModel):
    message: str
    location: Optional[str] = None
    last_analysis: Optional[Dict[str, Any]] = None

class PropertyFeature(BaseModel):
    feature: str
    confidence: float
    recommendation: str

class RealEstateTextAgent:
    def __init__(self):
        # Knowledge base for common real estate queries
        self.knowledge_base = {
            "notice_period": {
                "question_patterns": ["notice", "vacating", "move out", "leaving"],
                "response": """The notice period typically depends on your lease agreement and local laws, but generally:
                1. For month-to-month tenancy: 30 days notice is standard
                2. For fixed-term leases: Check your lease agreement
                3. Some jurisdictions require 60 days notice
                Always provide written notice and check your specific lease terms."""
            },
            "rent_increase": {
                "question_patterns": ["increase rent", "raise rent", "rent hike"],
                "response": """Regarding rent increases during a contract:
                1. During a fixed-term lease: Landlord cannot increase rent unless specified in the lease
                2. For month-to-month: Usually requires 30-60 days written notice
                3. Check local rent control laws
                4. Increases must be reasonable and follow local regulations"""
            },
            "deposit_issues": {
                "question_patterns": ["deposit", "security deposit", "not returning deposit"],
                "response": """If your landlord isn't returning your deposit:
                1. Review your lease agreement
                2. Document property condition with photos/videos
                3. Send a formal written request
                4. Know your timeline (usually 21-30 days)
                5. Consider small claims court if necessary
                6. Contact local tenant rights organization"""
            },
            "rental_agreement": {
                "question_patterns": ["rental agreement", "lease agreement", "before signing", "documents check"],
                "response": """Key documents to check before signing a rental agreement:
                1. Lease agreement terms and conditions
                2. Property inspection report
                3. Maintenance responsibilities
                4. Utility arrangements
                5. Security deposit terms
                6. Pet policies
                7. Insurance requirements
                8. Property ownership verification"""
            },
            "landlord_entry": {
                "question_patterns": ["landlord enter", "entry without notice", "access property"],
                "response": """Regarding landlord entry:
                1. Usually requires 24-48 hours notice
                2. Exceptions for emergencies
                3. Must be during reasonable hours
                4. Should have legitimate reason
                5. Document unauthorized entries
                6. Know your right to privacy"""
            },
            "subletting": {
                "question_patterns": ["sublet", "sublease", "rent out"],
                "response": """Regarding subletting:
                1. Check your lease agreement first
                2. Get written permission from landlord
                3. Screen potential subtenants
                4. Create a formal sublease agreement
                5. Understand you're still responsible to the landlord
                6. Consider insurance implications"""
            },
            "maintenance_issues": {
                "question_patterns": ["maintenance", "repairs", "fixing"],
                "response": """Your rights regarding maintenance issues:
                1. Right to habitable living conditions
                2. Document all issues with photos/videos
                3. Submit written repair requests
                4. Follow up in writing
                5. Know repair timeline requirements
                6. Possible remedies: rent withholding, repair and deduct
                7. Contact housing authorities if necessary"""
            },
            "property_verification": {
                "question_patterns": ["verify property", "check ownership", "legal owner"],
                "response": """Steps to verify property ownership:
                1. Check public property records
                2. Request title search
                3. Verify tax records
                4. Check for liens or encumbrances
                5. Use online property databases
                6. Consider title insurance
                7. Consult a real estate attorney"""
            },
            "buying_process": {
                "question_patterns": ["buying house", "purchase property", "steps buying"],
                "response": """Steps in buying a house:
                1. Check financial readiness
                2. Get pre-approved for mortgage
                3. Find a real estate agent
                4. House hunting
                5. Make an offer
                6. Home inspection
                7. Property appraisal
                8. Final mortgage approval
                9. Closing process"""
            },
            "property_taxes": {
                "question_patterns": ["property tax", "tax when buying", "purchase tax"],
                "response": """Taxes involved in property purchase:
                1. Property transfer tax
                2. Stamp duty (varies by location)
                3. Registration charges
                4. Capital gains tax (for seller)
                5. GST on new constructions
                6. Annual property tax
                Consider consulting a tax professional."""
            },
            "hidden_charges": {
                "question_patterns": ["hidden charges", "additional costs", "extra fees"],
                "response": """Common hidden charges in real estate:
                1. Property taxes
                2. Insurance costs
                3. Maintenance fees
                4. Utility deposits
                5. HOA/society charges
                6. Registration fees
                7. Legal fees
                8. Broker commission
                9. Renovation/repair costs"""
            },
            "property_dispute": {
                "question_patterns": ["dispute", "litigation", "legal issues"],
                "response": """To check for property disputes:
                1. Search court records
                2. Check with local property registrar
                3. Review title insurance report
                4. Consult property lawyer
                5. Check for encumbrances
                6. Verify tax payment history
                7. Review property documents"""
            }
        }

    def find_best_match(self, query: str) -> str:
        query = query.lower()
        best_match = None
        max_matches = 0

        for topic, data in self.knowledge_base.items():
            matches = sum(1 for pattern in data["question_patterns"] if pattern.lower() in query)
            if matches > max_matches:
                max_matches = matches
                best_match = topic

        if best_match:
            return self.knowledge_base[best_match]["response"]
        
        return """I apologize, but I don't have specific information about that query. 
                Please rephrase your question or consult with a real estate professional or legal expert for accurate advice."""

class IssueDetectionAgent:
    def __init__(self):
        self.conversation_context = []
        self.last_analysis = None
        self.current_issue = None
        self.professionals = {
            "structural_damage": {
                "professionals": [
                    "Structural Engineer",
                    "Licensed Building Contractor",
                    "Foundation Specialist",
                    "Construction Project Manager"
                ],
                "qualifications": "Look for professionals with:\n- Licensed structural engineer certification\n- Experience with foundation repairs\n- Local building code knowledge\n- Insurance and bonding"
            },
            "water_damage": {
                "professionals": [
                    "Water Damage Restoration Specialist",
                    "Licensed Plumber",
                    "Moisture Control Expert",
                    "Building Inspector"
                ],
                "qualifications": "Look for professionals with:\n- IICRC certification\n- Water damage restoration experience\n- Mold remediation knowledge\n- Insurance claim experience"
            },
            "mold": {
                "professionals": [
                    "Certified Mold Inspector",
                    "Mold Remediation Specialist",
                    "Indoor Air Quality Expert",
                    "Environmental Hygienist"
                ],
                "qualifications": "Look for professionals with:\n- IICRC or ACAC certification\n- Mold assessment experience\n- Air quality testing capabilities\n- Remediation protocol knowledge"
            },
            "window_issues": {
                "professionals": [
                    "Window Installation Specialist",
                    "Glass Repair Technician",
                    "Energy Efficiency Expert",
                    "General Contractor"
                ],
                "qualifications": "Look for professionals with:\n- Window installation certification\n- Energy efficiency expertise\n- Weatherization experience\n- Manufacturer certifications"
            }
        }
        self.issue_details = {
            "structural_damage": {
                "repair_steps": [
                    "Professional inspection by structural engineer",
                    "Foundation assessment and soil testing",
                    "Development of repair plan",
                    "Installation of temporary support structures",
                    "Repair or reinforce damaged structural elements",
                    "Address any underlying foundation issues",
                    "Final structural integrity verification"
                ],
                "estimated_cost": "$5,000 - $25,000",
                "timeline": "2-8 weeks",
                "prevention": [
                    "Regular structural inspections",
                    "Maintain proper drainage around foundation",
                    "Monitor for new cracks or movement",
                    "Address water issues promptly"
                ]
            },
            "water_damage": {
                "repair_steps": [
                    "Emergency water extraction",
                    "Identify and fix the water source",
                    "Industrial drying of affected areas",
                    "Moisture testing of walls and floors",
                    "Remove damaged materials",
                    "Sanitize and treat for mold prevention",
                    "Replace damaged materials"
                ],
                "estimated_cost": "$2,000 - $8,000",
                "timeline": "1-2 weeks",
                "prevention": [
                    "Regular plumbing inspections",
                    "Install water detection systems",
                    "Maintain proper ventilation",
                    "Regular gutter maintenance"
                ]
            },
            "mold": {
                "repair_steps": [
                    "Professional mold inspection",
                    "Air quality testing",
                    "Containment setup",
                    "HVAC system protection",
                    "Remove affected materials",
                    "Clean and sanitize area",
                    "Apply preventive treatments"
                ],
                "estimated_cost": "$500 - $6,000",
                "timeline": "3-7 days",
                "prevention": [
                    "Control indoor humidity (30-50%)",
                    "Fix leaks immediately",
                    "Improve ventilation",
                    "Regular inspections"
                ]
            },
            "window_issues": {
                "repair_steps": [
                    "Window inspection and assessment",
                    "Measure window opening",
                    "Remove damaged window",
                    "Repair frame if needed",
                    "Install new window",
                    "Seal and weatherproof",
                    "Test operation and efficiency"
                ],
                "estimated_cost": "$200 - $1,500 per window",
                "timeline": "1-3 days",
                "prevention": [
                    "Regular maintenance checks",
                    "Clean tracks and mechanisms",
                    "Replace weatherstripping as needed",
                    "Address drafts promptly"
                ]
            }
        }

    def _add_to_context(self, role: str, content: str):
        """Add message to conversation context"""
        self.conversation_context.append({"role": role, "content": content})
        # Keep only last 5 messages for context
        if len(self.conversation_context) > 5:
            self.conversation_context = self.conversation_context[-5:]

    def _get_current_context(self) -> str:
        """Get relevant context from conversation history"""
        if not self.conversation_context:
            return ""
        return "\n".join([f"{'Bot:' if msg['role'] == 'assistant' else 'User:'} {msg['content']}" 
                         for msg in self.conversation_context[-3:]])

    def analyze_image(self, features: List[PropertyFeature]):
        """Process image analysis results with chain of thought"""
        detected_issues = []
        thoughts = []
        
        # Step 1: Analyze each detected feature
        thoughts.append("Analyzing detected features:")
        for feature in features:
            if feature.confidence >= 0.2:
                # Clean up the feature name to match our issue_details keys
                feature_type = feature.feature.lower().replace(" ", "_")
                if "window" in feature_type:
                    feature_type = "window_issues"
                elif "mold" in feature_type:
                    feature_type = "mold"
                elif "water" in feature_type:
                    feature_type = "water_damage"
                elif "structural" in feature_type:
                    feature_type = "structural_damage"
                
                issue = {
                    "type": feature_type,
                    "confidence": feature.confidence,
                    "recommendation": feature.recommendation
                }
                detected_issues.append(issue)
                thoughts.append(f"- Found {issue['type']} with {issue['confidence']:.2f} confidence")
                thoughts.append(f"  Recommendation: {issue['recommendation']}")

        # Step 2: Store analysis results
        self.last_analysis = {
            "timestamp": datetime.now().isoformat(),
            "detected_issues": detected_issues,
            "details": {}
        }

        # Add issue details for detected issues
        for issue in detected_issues:
            issue_type = issue["type"]
            if issue_type in self.issue_details:
                self.last_analysis["details"][issue_type] = self.issue_details[issue_type]

        # Step 3: Generate response
        if not detected_issues:
            response = "I didn't detect any significant issues in this image. Would you like me to look for something specific?"
        else:
            response_parts = []
            for issue in detected_issues:
                issue_type = issue["type"].replace("_", " ")
                confidence_level = "high" if issue["confidence"] > 0.7 else "moderate"
                response_parts.append(f"I've detected {issue_type} with {confidence_level} confidence.")
                response_parts.append(f"Quick assessment: {issue['recommendation']}")
            
            response_parts.append("\nI can provide more specific details about repair steps, prevention measures, or cost breakdown for any of these issues. What would you like to know more about?")
            response = " ".join(response_parts)

        # Store conversation context
        self._add_to_context("user", "Image uploaded for analysis")
        self._add_to_context("assistant", response)
        return response

    def handle_followup_question(self, question: str) -> str:
        """Handle follow-up questions using chain of thought reasoning"""
        try:
            thoughts = ["Processing follow-up question..."]
            
            if not self.last_analysis:
                thoughts.append("No recent image analysis found")
                return "I don't have any recent property analysis to reference. Please upload an image first."

            detected_issues = self.last_analysis.get("detected_issues", [])
            if not detected_issues:
                thoughts.append("No issues detected in last analysis")
                return "No issues were detected in the last analysis."

            # Get the first detected issue
            current_issue = detected_issues[0]
            issue_type = current_issue["type"]
            
            # Ensure we have details for this issue type
            if issue_type not in self.issue_details:
                return f"I apologize, but I don't have detailed information about {issue_type.replace('_', ' ')}. Please consult a professional for an assessment."

            # Get the details for this issue
            details = self.issue_details[issue_type]

            # Step 1: Analyze question type
            thoughts.append("Analyzing question type...")
            question = question.lower()
            
            # Check if asking about professionals
            if any(word in question for word in ["who", "contact", "professional", "expert", "call", "hire"]):
                thoughts.append("User is asking about professional help")
                return self._get_professional_info(issue_type)

            # Step 2: Identify question intent
            thoughts.append("Identifying question intent...")
            
            if any(word in question for word in ["repair", "fix", "steps", "how to", "process"]):
                return self._generate_repair_response(issue_type, details)
            elif any(word in question for word in ["cost", "price", "expensive", "money", "charges"]):
                return self._generate_cost_response(issue_type, details)
            elif any(word in question for word in ["time", "long", "duration", "timeline", "when"]):
                return self._generate_timeline_response(issue_type, details)
            elif any(word in question for word in ["prevent", "avoid", "stop", "future"]):
                return self._generate_prevention_response(issue_type, details)
            
            # If no specific intent is detected, provide an overview
            return self._generate_overview_response(issue_type, details)
            
        except Exception as e:
            print(f"Error in handle_followup_question: {str(e)}")
            return "I apologize, but I encountered an error processing your request. Please try asking your question again."

    def _get_professional_info(self, issue_type: str) -> str:
        """Generate information about professionals to contact"""
        prof_info = self.professionals.get(issue_type, {})
        if not prof_info:
            return "I recommend consulting a general contractor or home inspector for an assessment."

        response = f"For {issue_type.replace('_', ' ')}, you should contact:\n\n"
        response += "Recommended Professionals:\n"
        response += "\n".join(f"• {prof}" for prof in prof_info["professionals"])
        response += f"\n\nQualifications to look for:\n{prof_info['qualifications']}"
        response += "\n\nAlways verify:\n"
        response += "• Professional licenses\n"
        response += "• Insurance coverage\n"
        response += "• Local certifications\n"
        response += "• Previous experience with similar issues"
        return response

    def _generate_repair_response(self, issue_type: str, details: dict) -> str:
        """Generate detailed repair information"""
        try:
            response = f"Here's a detailed repair plan for the {issue_type.replace('_', ' ')}:\n\n"
            response += "Step-by-step repair process:\n"
            for i, step in enumerate(details.get('repair_steps', []), 1):
                response += f"{i}. {step}\n"
            
            if 'timeline' in details:
                response += f"\nEstimated Timeline: {details['timeline']}"
            if 'estimated_cost' in details:
                response += f"\nTypical Cost Range: {details['estimated_cost']}"
                
            response += "\n\nWould you like information about professionals who can help with these repairs?"
            return response
        except Exception as e:
            print(f"Error in _generate_repair_response: {str(e)}")
            return "I apologize, but I encountered an error generating the repair information. Please try again."

    def _generate_cost_response(self, issue_type: str, details: dict) -> str:
        """Generate detailed cost information"""
        try:
            response = f"Cost breakdown for {issue_type.replace('_', ' ')} repair:\n\n"
            if 'estimated_cost' in details:
                response += f"Total Estimated Range: {details['estimated_cost']}\n\n"
            else:
                response += "Cost estimation requires professional assessment.\n\n"
                
            response += "This typically includes:\n"
            response += "• Initial inspection and assessment\n"
            response += "• Labor costs\n"
            response += "• Materials and equipment\n"
            response += "• Permits if required\n"
            response += "• Clean-up and disposal\n\n"
            response += "Factors that may affect cost:\n"
            response += "• Severity of the damage\n"
            response += "• Property location\n"
            response += "• Material choices\n"
            response += "• Underlying issues discovered\n"
            response += "• Emergency/rush service needs"
            return response
        except Exception as e:
            print(f"Error in _generate_cost_response: {str(e)}")
            return "I apologize, but I encountered an error generating the cost information. Please try again."

    def _generate_timeline_response(self, issue_type: str, details: dict) -> str:
        """Generate detailed timeline information"""
        try:
            response = f"Timeline for {issue_type.replace('_', ' ')} repair:\n\n"
            if 'timeline' in details:
                response += f"Total Estimated Duration: {details['timeline']}\n\n"
            else:
                response += "Timeline estimation requires professional assessment.\n\n"
                
            response += "Process Breakdown:\n"
            response += "1. Initial Assessment: 1-2 days\n"
            response += "2. Planning and Permits: 2-3 days\n"
            response += "3. Material Procurement: 1-5 days\n"
            response += "4. Actual Repair Work: Varies\n"
            response += "5. Final Inspection: 1-2 days\n\n"
            response += "Factors that may affect timeline:\n"
            response += "• Contractor availability\n"
            response += "• Material availability\n"
            response += "• Weather conditions\n"
            response += "• Permit processing\n"
            response += "• Additional issues discovered"
            return response
        except Exception as e:
            print(f"Error in _generate_timeline_response: {str(e)}")
            return "I apologize, but I encountered an error generating the timeline information. Please try again."

    def _generate_prevention_response(self, issue_type: str, details: dict) -> str:
        """Generate detailed prevention information"""
        response = f"Prevention measures for {issue_type.replace('_', ' ')}:\n\n"
        response += "Recommended steps:\n"
        response += "\n".join(f"• {step}" for step in details['prevention'])
        response += "\n\nRegular Maintenance Schedule:\n"
        response += "• Monthly visual inspections\n"
        response += "• Quarterly detailed checks\n"
        response += "• Annual professional assessment\n"
        response += "\nWarning signs to watch for:\n"
        response += "• Changes in appearance\n"
        response += "• Unusual sounds or smells\n"
        response += "• Water stains or moisture\n"
        response += "• Cracks or movement"
        return response

    def _generate_overview_response(self, issue_type: str, details: dict) -> str:
        """Generate general overview information"""
        response = f"Overview of the {issue_type.replace('_', ' ')} issue:\n\n"
        response += "I can provide detailed information about:\n\n"
        response += f"1. Repair Steps ({len(details['repair_steps'])} step process)\n"
        response += f"2. Cost Estimates ({details['estimated_cost']})\n"
        response += f"3. Timeline ({details['timeline']})\n"
        response += f"4. Prevention Measures ({len(details['prevention'])} recommendations)\n"
        response += "5. Professional Help\n\n"
        response += "What specific aspect would you like to know more about?"
        return response

# Initialize agents
text_agent = RealEstateTextAgent()
issue_agent = IssueDetectionAgent()

def get_image_embedding(image_path: str) -> np.ndarray:
    """Get CLIP embedding for an image"""
    image = Image.open(image_path)
    inputs = processor(images=image, return_tensors="pt")
    with torch.no_grad():
        features = model.get_image_features(**inputs)
    return features.numpy().flatten()

def analyze_image_with_clip(image_path: str) -> List[PropertyFeature]:
    """Analyze image using CLIP model"""
    features = [
        "water damage", "mold growth", "structural cracks", "poor lighting",
        "broken fixtures", "paint peeling", "electrical issues", "plumbing problems",
        "ceiling damage", "wall damage", "floor damage", "window issues"
    ]
    
    try:
        # If image_path is a URL, download it first
        if image_path.startswith('http'):
            response = requests.get(image_path)
            image = Image.open(BytesIO(response.content))
        else:
            image = Image.open(image_path)

        # Process image with CLIP
        inputs = processor(images=image, text=features, return_tensors="pt", padding=True)
        outputs = model(**inputs)
        
        logits_per_image = outputs.logits_per_image
        probs = logits_per_image.softmax(dim=1)[0]
        
        detected_features = []
        for feature, confidence in zip(features, probs.tolist()):
            if confidence > 0.2:  # Confidence threshold
                recommendation = get_recommendation(feature, confidence)
                detected_features.append(PropertyFeature(
                    feature=feature,
                    confidence=confidence,
                    recommendation=recommendation
                ))
        
        return detected_features
    except Exception as e:
        print(f"Error analyzing image: {str(e)}")
        return []

def get_recommendation(feature: str, confidence: float) -> str:
    """Get a recommendation based on the detected feature"""
    recommendations = {
        "water damage": "Contact a water damage restoration specialist immediately. This could lead to mold and structural issues if not addressed.",
        "mold growth": "Schedule a mold inspection and remediation service. Ensure proper ventilation and fix any water leaks.",
        "structural cracks": "Have a structural engineer assess the severity of the cracks. This could indicate foundation issues.",
        "poor lighting": "Consider installing additional lighting fixtures or larger windows. Good lighting can significantly improve the space.",
        "broken fixtures": "Have a licensed contractor repair or replace the damaged fixtures. This is typically a straightforward fix.",
        "paint peeling": "Sand the area, prime, and repaint. Check for underlying moisture issues that might be causing the paint to peel.",
        "electrical issues": "Contact a licensed electrician for an inspection. Electrical problems can pose serious safety risks.",
        "plumbing problems": "Have a professional plumber inspect the system. Address leaks and water pressure issues promptly.",
        "ceiling damage": "Inspect for roof leaks and have a contractor assess the damage. This could indicate water infiltration.",
        "wall damage": "Evaluate if it's superficial or structural. Minor repairs can be done by a general contractor.",
        "floor damage": "Consider repairs or replacement depending on severity. Check for underlying subfloor issues.",
        "window issues": "Have a window specialist check for proper sealing and operation. This affects energy efficiency."
    }
    
    return recommendations.get(feature, "Please consult a specialist for this issue.")

@app.get("/")
async def root():
    return {"message": "Welcome to Real Estate Chatbot API"}

@app.post("/chat")
async def chat(message: ChatMessage):
    try:
        # Update agent's last analysis if provided
        if message.last_analysis:
            issue_agent.last_analysis = message.last_analysis
            
        # First check if this is an image-related question
        if issue_agent.last_analysis and issue_agent.last_analysis.get("detected_issues"):
            detected_issues = issue_agent.last_analysis["detected_issues"]
            issue_types = [issue["type"].replace("_", " ") for issue in detected_issues]
            
            # Keywords that indicate question is about the image analysis
            image_related_keywords = [
                "repair", "fix", "issue", "problem", "damage",
                "cost", "price", "timeline", "time", "how long",
                "steps", "process", "prevent", "avoid", "professional",
                "who", "contact", "help"
            ]
            
            # Check if question contains issue types or image-related keywords
            is_image_related = any(issue_type in message.message.lower() for issue_type in issue_types) or \
                             any(keyword in message.message.lower() for keyword in image_related_keywords)
            
            if is_image_related:
                response = issue_agent.handle_followup_question(message.message)
                if "I don't have any recent property analysis" not in response and \
                   "I apologize, but I don't have specific information" not in response:
                    return {"response": response}
        
        # If not image-related or no good response from issue agent, use text agent
        response = text_agent.find_best_match(message.message)
        return {"response": response}

    except Exception as e:
        print(f"Error in chat endpoint: {str(e)}")
        return {"response": "I apologize, but I encountered an error processing your request. Please try again."}

@app.post("/upload-image")
async def upload_image(file: UploadFile = File(...)):
    os.makedirs("temp", exist_ok=True)
    timestamp = int(time.time())
    temp_file_path = f"temp/{timestamp}_{file.filename}"
    try:
        with open(temp_file_path, "wb") as buffer:
            content = await file.read()
            buffer.write(content)
        
        # Upload to Cloudinary
        upload_result = cloudinary.uploader.upload(temp_file_path)
        image_url = upload_result["secure_url"]
        
        # Analyze with CLIP
        features = analyze_image_with_clip(temp_file_path)
        
        # Convert features to proper format for the agent
        detected_issues = []
        for feature in features:
            issue_type = feature.feature.lower().replace(" ", "_")
            detected_issues.append({
                "type": issue_type,
                "confidence": feature.confidence,
                "recommendation": feature.recommendation
            })
        
        # Store analysis in agent and get response
        issue_agent.last_analysis = {
            "timestamp": datetime.now().isoformat(),
            "detected_issues": detected_issues,
            "image_url": image_url
        }
        
        response = issue_agent.analyze_image(features)
        
        return {
            "image_url": image_url,
            "response": response,
            "features": [{"type": f.feature, "confidence": f.confidence, "recommendation": f.recommendation} for f in features],
            "last_analysis": issue_agent.last_analysis
        }
    
    finally:
        if os.path.exists(temp_file_path):
            os.remove(temp_file_path)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000) 