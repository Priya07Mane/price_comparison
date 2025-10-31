import numpy as np
import cv2
from PIL import Image
import io
from typing import Dict, Optional, List
import logging
from dataclasses import dataclass
import tensorflow as tf
from tensorflow.keras.applications import ResNet50, MobileNetV2
from tensorflow.keras.applications.resnet50 import preprocess_input as resnet_preprocess
from tensorflow.keras.applications.mobilenet_v2 import preprocess_input as mobilenet_preprocess
from tensorflow.keras.preprocessing import image as keras_image
import colorsys

logger = logging.getLogger(__name__)

@dataclass
class ImageAnalysisResult:
    """Result from AI image analysis"""
    category: str
    dominant_colors: List[str]
    color_name: str
    pattern: str
    style: str
    confidence: float
    description: str

class FashionImageAnalyzer:
    """AI-powered fashion item analyzer using transfer learning"""
    
    def __init__(self):
        self.base_model = None
        self.color_names = {
            'red': [(0, 50, 50), (10, 255, 255), (160, 50, 50), (180, 255, 255)],
            'pink': [(145, 50, 50), (165, 255, 255)],
            'purple': [(125, 50, 50), (145, 255, 255)],
            'blue': [(90, 50, 50), (125, 255, 255)],
            'green': [(35, 50, 50), (85, 255, 255)],
            'yellow': [(20, 50, 50), (35, 255, 255)],
            'orange': [(10, 50, 50), (20, 255, 255)],
            'brown': [(10, 50, 20), (20, 255, 200)],
            'white': [(0, 0, 200), (180, 30, 255)],
            'black': [(0, 0, 0), (180, 255, 50)],
            'grey': [(0, 0, 50), (180, 30, 200)],
        }
        
        # Fashion categories based on ImageNet classes
        self.category_mapping = {
            # Dresses
            'gown': 'dresses',
            'strapless': 'dresses',
            'cocktail_dress': 'dresses',
            'dress': 'dresses',
            'abaya': 'dresses',
            
            # Tops
            'jersey': 'tops',
            'sweatshirt': 'tops',
            'cardigan': 'tops',
            'blouse': 'tops',
            't-shirt': 'tops',
            'polo': 'tops',
            
            # Bottoms
            'jean': 'jeans',
            'denim': 'jeans',
            'trouser': 'jeans',
            'miniskirt': 'jeans',
            
            # Shoes
            'sandal': 'shoes',
            'running_shoe': 'shoes',
            'loafer': 'shoes',
            'boot': 'shoes',
            'shoe': 'shoes',
            
            # Accessories
            'sunglass': 'accessories',
            'bow_tie': 'accessories',
            'neck_brace': 'accessories',
            'bolo_tie': 'accessories',
        }
        
        self.initialize_model()
    
    def initialize_model(self):
        """Initialize the pre-trained model"""
        try:
            logger.info("Loading MobileNetV2 model...")
            self.base_model = MobileNetV2(
                weights='imagenet',
                include_top=True,
                input_shape=(224, 224, 3)
            )
            logger.info("Model loaded successfully")
        except Exception as e:
            logger.error(f"Error loading model: {e}")
            raise
    
    def preprocess_image(self, image_bytes: bytes) -> np.ndarray:
        """Preprocess image for model input"""
        try:
            # Convert bytes to PIL Image
            img = Image.open(io.BytesIO(image_bytes))
            
            # Convert to RGB if needed
            if img.mode != 'RGB':
                img = img.convert('RGB')
            
            # Resize to model input size
            img = img.resize((224, 224))
            
            # Convert to array
            img_array = keras_image.img_to_array(img)
            img_array = np.expand_dims(img_array, axis=0)
            
            # Preprocess
            img_array = mobilenet_preprocess(img_array)
            
            return img_array
            
        except Exception as e:
            logger.error(f"Error preprocessing image: {e}")
            raise
    
    def extract_dominant_colors(self, image_bytes: bytes, num_colors: int = 3) -> List[tuple]:
        """Extract dominant colors from image using K-means clustering"""
        try:
            # Convert to OpenCV format
            nparr = np.frombuffer(image_bytes, np.uint8)
            img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
            img = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
            
            # Reshape image to be a list of pixels
            pixels = img.reshape((-1, 3))
            pixels = np.float32(pixels)
            
            # K-means clustering
            criteria = (cv2.TERM_CRITERIA_EPS + cv2.TERM_CRITERIA_MAX_ITER, 100, 0.2)
            _, labels, centers = cv2.kmeans(pixels, num_colors, None, criteria, 10, cv2.KMEANS_RANDOM_CENTERS)
            
            # Convert to int
            centers = np.uint8(centers)
            
            # Count pixels in each cluster
            counts = np.bincount(labels.flatten())
            
            # Sort by frequency
            sorted_indices = np.argsort(-counts)
            dominant_colors = centers[sorted_indices]
            
            return [tuple(color) for color in dominant_colors]
            
        except Exception as e:
            logger.error(f"Error extracting colors: {e}")
            return [(128, 128, 128)]  # Default gray
    
    def rgb_to_color_name(self, rgb: tuple) -> str:
        """Convert RGB to human-readable color name"""
        try:
            # Convert RGB to HSV
            r, g, b = [x / 255.0 for x in rgb]
            h, s, v = colorsys.rgb_to_hsv(r, g, b)
            h = int(h * 180)  # Convert to OpenCV HSV range
            s = int(s * 255)
            v = int(v * 255)
            
            # Check against color ranges
            for color_name, ranges in self.color_names.items():
                if len(ranges) == 2:
                    lower, upper = ranges
                    if (lower[0] <= h <= upper[0] and 
                        lower[1] <= s <= upper[1] and 
                        lower[2] <= v <= upper[2]):
                        return color_name
                elif len(ranges) == 4:  # For red (wraps around)
                    lower1, upper1, lower2, upper2 = ranges
                    if ((lower1[0] <= h <= upper1[0] or lower2[0] <= h <= upper2[0]) and
                        lower1[1] <= s <= upper1[1] and 
                        lower1[2] <= v <= upper1[2]):
                        return color_name
            
            return 'multicolor'
            
        except Exception as e:
            logger.error(f"Error converting color: {e}")
            return 'unknown'
    
    def detect_pattern(self, image_bytes: bytes) -> str:
        """Detect pattern in clothing (simple edge-based detection)"""
        try:
            # Convert to OpenCV format
            nparr = np.frombuffer(image_bytes, np.uint8)
            img = cv2.imdecode(nparr, cv2.IMREAD_GRAYSCALE)
            
            # Detect edges
            edges = cv2.Canny(img, 50, 150)
            edge_density = np.count_nonzero(edges) / edges.size
            
            # Simple heuristic
            if edge_density > 0.15:
                return 'printed'
            elif edge_density > 0.08:
                return 'textured'
            else:
                return 'solid'
                
        except Exception as e:
            logger.error(f"Error detecting pattern: {e}")
            return 'solid'
    
    def predict_category(self, image_array: np.ndarray) -> tuple:
        """Predict clothing category using ImageNet model"""
        try:
            # Get predictions
            predictions = self.base_model.predict(image_array, verbose=0)
            
            # Decode predictions
            decoded = tf.keras.applications.mobilenet_v2.decode_predictions(predictions, top=5)[0]
            
            # Map to fashion categories
            for pred_id, pred_name, confidence in decoded:
                pred_name_lower = pred_name.lower().replace('_', ' ')
                
                # Check direct matches
                for keyword, category in self.category_mapping.items():
                    if keyword in pred_name_lower:
                        logger.info(f"Detected: {pred_name} -> {category} (confidence: {confidence:.2f})")
                        return category, pred_name, float(confidence)
            
            # Default to generic clothing category
            logger.info(f"No specific match, using top prediction: {decoded[0][1]}")
            return 'tops', decoded[0][1], float(decoded[0][2])
            
        except Exception as e:
            logger.error(f"Error predicting category: {e}")
            return 'tops', 'unknown', 0.5
    
    def analyze_image(self, image_bytes: bytes) -> ImageAnalysisResult:
        """Main method to analyze fashion item from image"""
        try:
            logger.info("Starting image analysis...")
            
            # Preprocess for model
            img_array = self.preprocess_image(image_bytes)
            
            # Predict category
            category, raw_prediction, confidence = self.predict_category(img_array)
            logger.info(f"Category: {category}, Confidence: {confidence:.2f}")
            
            # Extract colors
            dominant_colors_rgb = self.extract_dominant_colors(image_bytes, num_colors=3)
            logger.info(f"Dominant colors (RGB): {dominant_colors_rgb}")
            
            # Convert to color names
            color_names = [self.rgb_to_color_name(color) for color in dominant_colors_rgb]
            primary_color = color_names[0]
            logger.info(f"Color names: {color_names}, Primary: {primary_color}")
            
            # Detect pattern
            pattern = self.detect_pattern(image_bytes)
            logger.info(f"Pattern: {pattern}")
            
            # Determine style (simple heuristic based on category)
            style_map = {
                'dresses': 'casual',
                'tops': 'casual',
                'jeans': 'casual',
                'shoes': 'casual',
                'kurtas': 'ethnic',
                'sarees': 'ethnic',
                'shirts': 'formal'
            }
            style = style_map.get(category, 'casual')
            
            # Generate description
            pattern_desc = pattern if pattern != 'solid' else ''
            description = f"{primary_color} {pattern_desc} {category}".strip()
            
            result = ImageAnalysisResult(
                category=category,
                dominant_colors=color_names,
                color_name=primary_color,
                pattern=pattern,
                style=style,
                confidence=confidence,
                description=description
            )
            
            logger.info(f"Analysis complete: {description}")
            return result
            
        except Exception as e:
            logger.error(f"Error analyzing image: {e}")
            raise

# Singleton instance
_analyzer_instance = None

def get_analyzer() -> FashionImageAnalyzer:
    """Get or create analyzer instance"""
    global _analyzer_instance
    if _analyzer_instance is None:
        _analyzer_instance = FashionImageAnalyzer()
    return _analyzer_instance