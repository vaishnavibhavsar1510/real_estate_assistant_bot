class RealEstateAgent:
    def __init__(self):
        self.context = {}

    def process_message(self, message: str, location: str = None, image_url: str = None) -> str:
        """
        Process incoming messages and generate appropriate responses.
        """
        # Store context
        self.context['location'] = location
        self.context['last_image'] = image_url

        # Basic response logic
        if image_url:
            return self.process_image_query(message, image_url)
        elif location:
            return self.process_location_query(message, location)
        else:
            return self.process_general_query(message)

    def process_image_query(self, message: str, image_url: str) -> str:
        """Handle queries related to uploaded images"""
        return f"I see you've shared an image. Based on the image and your message '{message}', I can help analyze the property features and provide relevant information."

    def process_location_query(self, message: str, location: str) -> str:
        """Handle queries related to specific locations"""
        return f"Regarding properties in {location}: {self.generate_location_response(message)}"

    def process_general_query(self, message: str) -> str:
        """Handle general real estate queries"""
        return self.generate_general_response(message)

    def generate_location_response(self, message: str) -> str:
        """Generate responses for location-specific queries"""
        message = message.lower()
        if "price" in message:
            return "I can help you understand the property prices in this area. Would you like to know about average prices, price trends, or specific property types?"
        elif "school" in message:
            return "I can provide information about nearby schools, their ratings, and distance from properties in this area."
        else:
            return "I can help you with information about properties, neighborhoods, amenities, and market trends in this location. What specific details would you like to know?"

    def generate_general_response(self, message: str) -> str:
        """Generate responses for general queries"""
        message = message.lower()
        if "buy" in message:
            return "I can help you with the home buying process. Would you like to know about available properties, financing options, or the steps involved in purchasing a home?"
        elif "sell" in message:
            return "I can assist you with selling your property. Would you like information about market values, listing strategies, or preparing your home for sale?"
        elif "rent" in message:
            return "I can help you find rental properties or provide information about the rental market. Are you looking to rent a property or are you a landlord?"
        else:
            return "I'm your real estate assistant. I can help you with buying, selling, or renting properties, provide market insights, or answer questions about specific locations. What would you like to know?" 