from typing import Dict, Any, List
import torch
from PIL import Image
from transformers import CLIPProcessor, CLIPModel

class IssueDetectorAgent:
    def __init__(self):
        self.model = CLIPModel.from_pretrained("openai/clip-vit-base-patch32")
        self.processor = CLIPProcessor.from_pretrained("openai/clip-vit-base-patch32")
        
        # Define common property issues and their recommendations
        self.issues = {
            "water_damage": {
                "features": ["water damage", "water stains", "leaks", "moisture"],
                "recommendation": "Contact a water damage restoration specialist immediately. Check for active leaks and ensure proper ventilation."
            },
            "mold": {
                "features": ["mold", "mildew", "fungus", "black spots"],
                "recommendation": "Use a dehumidifier and contact a mold remediation specialist. This could be a health hazard."
            },
            "structural": {
                "features": ["cracks", "structural damage", "foundation issues", "uneven floors"],
                "recommendation": "Have a structural engineer assess the severity of these issues immediately."
            },
            "electrical": {
                "features": ["exposed wires", "electrical issues", "faulty wiring", "power problems"],
                "recommendation": "Contact a licensed electrician. Do not attempt DIY repairs on electrical issues."
            },
            "plumbing": {
                "features": ["plumbing issues", "pipe leaks", "drainage problems", "water pressure"],
                "recommendation": "Schedule an inspection with a licensed plumber to assess and fix the issues."
            }
        }

    async def analyze_image(self, image_path: str, context: str = "") -> Dict[str, Any]:
        """Analyze image for property issues"""
        try:
            # Prepare all features for CLIP
            all_features = []
            for issue in self.issues.values():
                all_features.extend(issue["features"])
            
            # Load and process image
            image = Image.open(image_path)
            inputs = self.processor(
                images=image,
                text=all_features,
                return_tensors="pt",
                padding=True
            )
            
            # Get model predictions
            with torch.no_grad():
                outputs = self.model(**inputs)
                logits_per_image = outputs.logits_per_image
                probs = logits_per_image.softmax(dim=1)[0]
            
            # Process results
            detected_issues = []
            for i, (feature, confidence) in enumerate(zip(all_features, probs.tolist())):
                if confidence > 0.2:  # Confidence threshold
                    # Find which issue category this feature belongs to
                    for issue_type, issue_info in self.issues.items():
                        if feature in issue_info["features"]:
                            detected_issues.append({
                                "type": issue_type,
                                "feature": feature,
                                "confidence": confidence,
                                "recommendation": issue_info["recommendation"]
                            })
            
            # Generate response
            if not detected_issues:
                return {
                    "response": "I don't see any significant issues in this image. Would you like me to look for specific problems?",
                    "detected_issues": []
                }
            
            # Sort issues by confidence
            detected_issues.sort(key=lambda x: x["confidence"], reverse=True)
            
            # Generate detailed response
            response = "I've detected the following issues:\n\n"
            for issue in detected_issues:
                response += f"• {issue['feature'].title()} (Confidence: {issue['confidence']:.1%})\n"
                response += f"  Recommendation: {issue['recommendation']}\n\n"
            
            if context:
                response += f"\nBased on your message '{context}', I recommend prioritizing these issues. Would you like more specific details about any of them?"
            
            return {
                "response": response,
                "detected_issues": detected_issues
            }
            
        except Exception as e:
            return {
                "response": f"Error analyzing image: {str(e)}",
                "detected_issues": []
            } 