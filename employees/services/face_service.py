"""
Face recognition service using DeepFace with ArcFace model.
"""
import os
import logging
import numpy as np
from typing import List, Dict, Any
from deepface import DeepFace
from sklearn.preprocessing import normalize
from django.conf import settings

logger = logging.getLogger(__name__)


class FaceRecognitionError(Exception):
    """Custom exception for face recognition errors."""
    pass


class FaceService:
    """
    Service for facial recognition operations using DeepFace.
    Uses ArcFace model with RetinaFace detector.
    """
    
    MODEL_NAME = settings.DEEPFACE_MODEL
    DETECTOR_BACKEND = settings.DEEPFACE_DETECTOR
    
    @classmethod
    def extract_embedding(cls, image_path: str) -> np.ndarray:
        """
        Extract facial embedding from an image using DeepFace.
        
        Args:
            image_path: Path to the image file
            
        Returns:
            Normalized embedding vector as numpy array
            
        Raises:
            FaceRecognitionError: If face extraction fails
        """
        if not os.path.exists(image_path):
            raise FaceRecognitionError(f"Image file not found: {image_path}")
        
        try:
            logger.info(f"Extracting embedding from: {image_path}")
            
            # Extract face embedding using DeepFace
            embeddings = DeepFace.represent(
                img_path=image_path,
                model_name=cls.MODEL_NAME,
                detector_backend=cls.DETECTOR_BACKEND,
                enforce_detection=True,
                align=True
            )
            
            # DeepFace.represent returns a list of face representations
            if not embeddings or len(embeddings) == 0:
                raise FaceRecognitionError("No face detected in the image")
            
            if len(embeddings) > 1:
                raise FaceRecognitionError(
                    f"Multiple faces detected ({len(embeddings)}). "
                    "Please provide an image with a single face."
                )
            
            # Extract the embedding vector
            embedding = np.array(embeddings[0]['embedding'])
            
            # Normalize the embedding for cosine similarity
            normalized_embedding = normalize(embedding.reshape(1, -1))[0]
            
            logger.info(f"Successfully extracted embedding. Shape: {normalized_embedding.shape}")
            
            return normalized_embedding
            
        except ValueError as e:
            # DeepFace raises ValueError when no face is detected
            logger.error(f"Face detection failed: {str(e)}")
            raise FaceRecognitionError("No face detected in the image. Please provide a clear face photo.")
        
        except Exception as e:
            logger.error(f"Error extracting embedding: {str(e)}")
            raise FaceRecognitionError(f"Failed to process image: {str(e)}")
    
    @classmethod
    def validate_image(cls, image_path: str) -> Dict[str, Any]:
        """
        Validate that the image contains exactly one detectable face.
        
        Args:
            image_path: Path to the image file
            
        Returns:
            Dictionary with validation results
        """
        try:
            # Attempt to extract faces without getting embeddings
            faces = DeepFace.extract_faces(
                img_path=image_path,
                detector_backend=cls.DETECTOR_BACKEND,
                enforce_detection=True,
                align=True
            )
            
            face_count = len(faces)
            
            return {
                'valid': face_count == 1,
                'face_count': face_count,
                'message': cls._get_validation_message(face_count)
            }
            
        except Exception as e:
            return {
                'valid': False,
                'face_count': 0,
                'message': f"Face detection failed: {str(e)}"
            }
    
    @staticmethod
    def _get_validation_message(face_count: int) -> str:
        """Get appropriate validation message based on face count."""
        if face_count == 0:
            return "No face detected. Please provide a clear face photo."
        elif face_count == 1:
            return "Image is valid."
        else:
            return f"Multiple faces detected ({face_count}). Please provide an image with a single face."
    
    @staticmethod
    def embedding_to_list(embedding: np.ndarray) -> List[float]:
        """
        Convert numpy array embedding to list of floats for storage.
        
        Args:
            embedding: Numpy array embedding
            
        Returns:
            List of floats
        """
        return embedding.tolist()
    
    @staticmethod
    def list_to_embedding(embedding_list: List[float]) -> np.ndarray:
        """
        Convert list of floats back to numpy array.
        
        Args:
            embedding_list: List of floats
            
        Returns:
            Numpy array
        """
        return np.array(embedding_list)
