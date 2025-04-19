from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey, JSON, Text
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from database import Base

class Property(Base):
    __tablename__ = "properties"

    id = Column(Integer, primary_key=True, index=True)
    address = Column(String, nullable=False)
    location = Column(String, nullable=False)
    features = Column(JSON)  # Store property features as JSON
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relationship with images
    images = relationship("PropertyImage", back_populates="property")

class PropertyImage(Base):
    __tablename__ = "property_images"

    id = Column(Integer, primary_key=True, index=True)
    property_id = Column(Integer, ForeignKey("properties.id"))
    file_path = Column(String, nullable=False)
    clip_features = Column(JSON)  # Store CLIP embeddings as JSON
    detected_features = Column(JSON)  # Changed from ARRAY to JSON
    upload_date = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relationship with property
    property = relationship("Property", back_populates="images")

class ImageAnalysis(Base):
    __tablename__ = "image_analysis"

    id = Column(Integer, primary_key=True, index=True)
    image_id = Column(Integer, ForeignKey("property_images.id"))
    analysis_type = Column(String)  # e.g., 'CLIP', 'OCR'
    results = Column(JSON)  # Store analysis results as JSON
    confidence_score = Column(Float)
    created_at = Column(DateTime(timezone=True), server_default=func.now()) 