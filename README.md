# PropertyLoop - Real Estate Assistant

A sophisticated AI-powered real estate assistant that helps identify and analyze property issues using image processing and natural language understanding.

## 🛠️ Tools & Technologies

### Frontend
- React.js with TypeScript
- Material-UI (MUI) for modern UI components
- Axios for API communication
- React Dropzone for file uploads

### Backend
- FastAPI (Python) for high-performance API
- CLIP (Contrastive Language-Image Pre-Training) for image analysis
- PostgreSQL for data persistence
- Cloudinary for image storage
- Uvicorn as ASGI server

## 🤖 Agent System Architecture

The system implements a multi-agent architecture for intelligent property analysis:

### 1. Image Analysis Agent (CLIP-based)
- Processes uploaded property images
- Detects visual features and potential issues
- Generates detailed analysis reports
- Confidence scoring for detected features

### 2. Issue Detection Agent
- Contextual understanding of property problems
- Maintains conversation history
- Provides detailed information about:
  - Repair steps
  - Cost estimates
  - Repair timelines
  - Prevention measures

### 3. Chat Response Agent (OpenAI Model)
- Handles user queries
- Maintains conversation context
- Integrates insights from other agents
- Provides location-aware responses

## 🔍 Image-Based Issue Detection

The system uses OpenAI's CLIP model for advanced image analysis:

1. **Image Processing**
   - Image upload and preprocessing
   - Feature extraction using CLIP
   - Multi-label classification

2. **Issue Detection**
   - Structural damage identification
   - Water damage assessment
   - Mold detection
   - General property condition analysis

3. **Analysis Storage**
   - Results stored in PostgreSQL
   - JSON-based feature storage
   - Confidence scores tracking

## 💡 Use Cases

1. **Property Inspection**
   - Upload images of property issues
   - Receive instant analysis
   - Get repair recommendations

2. **Cost Assessment**
   - Estimated repair costs
   - Timeline projections
   - Material requirements

3. **Maintenance Planning**
   - Preventive measures
   - Maintenance schedules
   - Priority assessment

4. **Interactive Consultation**
   - Follow-up questions
   - Detailed explanations
   - Location-specific advice

## 🚀 Getting Started

### Prerequisites
- Python 3.8+
- Node.js 14+
- MongoDB (Atlas or Compass any)
- Cloudinary account
- VectorDB

### Installation

1. **Clone the repository**
```bash
git clone https://github.com/vaishnavibhavsar1510/real_estate_assistant_bot.git
cd real_estate_assistant_bot
```

2. **Backend Setup**
```bash
cd backend
touch .env   #Add all the API keys here Of Cloudinary, OpenAI, MongoDB.
pip install -r requirements.txt
# Configure environment variables (see .env.example)
uvicorn main:app --reload --port 8000
```

3. **Frontend Setup**
```bash
cd frontend
touch .env  #Optional, just to setup ports
npm install
npm start
```

### Environment Variables
Create a `.env` file in the backend directory:
```
DATABASE_URL=postgresql://user:password@localhost/db_name
CLOUDINARY_CLOUD_NAME=your_cloud_name
CLOUDINARY_API_KEY=your_api_key
CLOUDINARY_API_SECRET=your_api_secret
```
Create a `.env` file in the frontend directory (Optional):
```
PORT=3001
REACT_APP_API_URL=http://localhost:8000 
```

## 🌐 Deployment

The application is currently deployed at:
- Frontend: http://localhost:3001
- Backend API: http://localhost:8000

## 🎯 How to Use

1. Access the web interface at http://localhost:3001
2. Upload a property image using the drag-and-drop interface (Agent 1 handles)
3. Ask questions about detected issues (Agent 2 handles)
4. Get detailed analysis and recommendations
5. Follow up with specific queries about repairs, costs, or timelines

## 📝 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🤝 Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## 👥 Authors

- Vaishnavi Bhavsar - [GitHub](https://github.com/vaishnavibhavsar1510)

## 📞 Support or Contact

For support, email [vaishnavibhavsar03@gmail.com] or open an issue on GitHub. 
