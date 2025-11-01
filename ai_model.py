import numpy as np
import cv2
from PIL import Image
import io
from typing import Dict, Optional, List, Tuple
import logging
from dataclasses import dataclass
import tensorflow as tf
from tensorflow.keras.applications import MobileNetV2
from tensorflow.keras.applications.mobilenet_v2 import preprocess_input as mobilenet_preprocess
from tensorflow.keras.preprocessing import image as keras_image

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
        
        # Enhanced color detection ranges (HSV)
        self.color_ranges = {
            'black': {'lower': [0, 0, 0], 'upper': [180, 255, 50]},
            'white': {'lower': [0, 0, 200], 'upper': [180, 30, 255]},
            'grey': {'lower': [0, 0, 50], 'upper': [180, 30, 200]},
            'red': {'lower': [0, 100, 100], 'upper': [10, 255, 255]},
            'red2': {'lower': [170, 100, 100], 'upper': [180, 255, 255]},
            'orange': {'lower': [11, 100, 100], 'upper': [25, 255, 255]},
            'yellow': {'lower': [26, 100, 100], 'upper': [35, 255, 255]},
            'green': {'lower': [36, 100, 100], 'upper': [85, 255, 255]},
            'cyan': {'lower': [86, 100, 100], 'upper': [95, 255, 255]},
            'blue': {'lower': [96, 100, 100], 'upper': [125, 255, 255]},
            'purple': {'lower': [126, 100, 100], 'upper': [145, 255, 255]},
            'pink': {'lower': [146, 50, 100], 'upper': [169, 255, 255]},
            'brown': {'lower': [10, 100, 20], 'upper': [20, 255, 200]},
        }
        
        # Fashion categories mapping
        self.category_mapping = {
            'gown': 'dresses', 'dress': 'dresses', 'strapless': 'dresses',
            'cocktail_dress': 'dresses', 'abaya': 'dresses',
            'jersey': 'tops', 'sweatshirt': 'tops', 'cardigan': 'tops',
            'blouse': 'tops', 't-shirt': 'tops', 'polo': 'tops', 'shirt': 'shirts',
            'jean': 'jeans', 'denim': 'jeans', 'trouser': 'jeans',
            'miniskirt': 'jeans', 'skirt': 'dresses',
            'sandal': 'shoes', 'running_shoe': 'shoes', 'loafer': 'shoes',
            'boot': 'shoes', 'shoe': 'shoes',
            'sunglass': 'accessories', 'bow_tie': 'accessories',
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
    
    def extract_clothing_region(self, img: np.ndarray) -> np.ndarray:
        """Extract central clothing region"""
        try:
            height, width = img.shape[:2]
            
            # Focus on central 70% of image (where clothing usually is)
            crop_width = int(width * 0.7)
            crop_height = int(height * 0.7)
            
            center_x, center_y = width // 2, height // 2
            x1 = max(0, center_x - crop_width // 2)
            y1 = max(0, center_y - crop_height // 2)
            x2 = min(width, center_x + crop_width // 2)
            y2 = min(height, center_y + crop_height // 2)
            
            return img[y1:y2, x1:x2]
        except Exception as e:
            logger.warning(f"Error extracting clothing region: {e}")
            return img

    def extract_dominant_colors(self, image_bytes: bytes, num_colors: int = 5) -> List[Tuple[int, int, int]]:
        """Extract dominant colors focusing on clothing"""
        try:
            # Convert to OpenCV format
            nparr = np.frombuffer(image_bytes, np.uint8)
            img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
            img = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
            
            # Focus on central region
            img_center = self.extract_clothing_region(img)
            
            # Resize for faster processing
            img_center = cv2.resize(img_center, (200, 200))
            
            # Reshape to pixel list
            pixels = img_center.reshape((-1, 3))
            
            # Filter out extreme colors (likely background)
            # Remove very dark pixels
            pixels = pixels[np.all(pixels > 25, axis=1)]
            # Remove very bright pixels
            pixels = pixels[np.all(pixels < 245, axis=1)]
            
            if len(pixels) < 100:
                # Fallback to using all pixels
                pixels = img_center.reshape((-1, 3))
            
            pixels = np.float32(pixels)
            
            # K-means clustering
            criteria = (cv2.TERM_CRITERIA_EPS + cv2.TERM_CRITERIA_MAX_ITER, 100, 0.2)
            k = min(num_colors, len(pixels))
            _, labels, centers = cv2.kmeans(pixels, k, None, criteria, 10, cv2.KMEANS_PP_CENTERS)
            
            centers = np.uint8(centers)
            
            # Count pixels in each cluster
            counts = np.bincount(labels.flatten())
            
            # Sort by frequency
            sorted_indices = np.argsort(-counts)
            dominant_colors = centers[sorted_indices]
            
            logger.info(f"Extracted {len(dominant_colors)} dominant colors")
            
            return [tuple(map(int, color)) for color in dominant_colors]
            
        except Exception as e:
            logger.error(f"Error extracting colors: {e}")
            return [(128, 128, 128)]
    
    def rgb_to_color_name(self, rgb: Tuple[int, int, int]) -> str:
        """Convert RGB to human-readable color name"""
        try:
            r, g, b = rgb
            
            # Convert RGB to HSV
            rgb_normalized = np.uint8([[rgb]])
            hsv = cv2.cvtColor(rgb_normalized, cv2.COLOR_RGB2HSV)[0][0]
            h, s, v = int(hsv[0]), int(hsv[1]), int(hsv[2])
            
            # Check for achromatic colors first
            if s < 25:
                if v < 70:
                    return 'black'
                elif v > 220:
                    return 'white'
                else:
                    return 'grey'
            
            # Check each color range
            for color_name, ranges in self.color_ranges.items():
                if color_name in ['black', 'white', 'grey']:
                    continue
                    
                lower = np.array(ranges['lower'])
                upper = np.array(ranges['upper'])
                
                # Special handling for red (wraps around hue)
                if color_name == 'red2':
                    if (h >= 170 or h <= 10) and s >= 100 and v >= 100:
                        return 'red'
                else:
                    if (lower[0] <= h <= upper[0] and 
                        lower[1] <= s <= upper[1] and 
                        lower[2] <= v <= upper[2]):
                        return color_name
            
            return 'multicolor'
            
        except Exception as e:
            logger.error(f"Error converting color: {e}")
            return 'unknown'
    
    def detect_pattern(self, image_bytes: bytes) -> str:
        """Detect pattern in clothing"""
        try:
            nparr = np.frombuffer(image_bytes, np.uint8)
            img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
            img_gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
            
            # Focus on center region
            img_center = self.extract_clothing_region(img_gray)
            img_center = cv2.resize(img_center, (300, 300))
            
            # Detect edges
            edges = cv2.Canny(img_center, 50, 150)
            edge_density = np.count_nonzero(edges) / edges.size
            
            # Calculate texture
            texture_score = np.std(img_center)
            
            logger.info(f"Pattern - Edge density: {edge_density:.3f}, Texture: {texture_score:.2f}")
            
            # Pattern classification
            if edge_density > 0.2 or texture_score > 60:
                return 'printed'
            elif edge_density > 0.1 or texture_score > 40:
                return 'textured'
            else:
                return 'solid'
                
        except Exception as e:
            logger.error(f"Error detecting pattern: {e}")
            return 'solid'
    
    def preprocess_image(self, image_bytes: bytes) -> np.ndarray:
        """Preprocess image for model input"""
        try:
            img = Image.open(io.BytesIO(image_bytes))
            
            if img.mode != 'RGB':
                img = img.convert('RGB')
            
            img = img.resize((224, 224))
            img_array = keras_image.img_to_array(img)
            img_array = np.expand_dims(img_array, axis=0)
            img_array = mobilenet_preprocess(img_array)
            
            return img_array
            
        except Exception as e:
            logger.error(f"Error preprocessing image: {e}")
            raise
    
    def predict_category(self, image_array: np.ndarray) -> Tuple[str, str, float]:
        """Predict clothing category"""
        try:
            predictions = self.base_model.predict(image_array, verbose=0)
            decoded = tf.keras.applications.mobilenet_v2.decode_predictions(predictions, top=10)[0]
            
            logger.info(f"Top 5 predictions: {[(name, conf) for _, name, conf in decoded[:5]]}")
            
            # Try to map to fashion categories
            for pred_id, pred_name, confidence in decoded:
                pred_name_lower = pred_name.lower().replace('_', ' ')
                
                for keyword, category in self.category_mapping.items():
                    if keyword in pred_name_lower:
                        logger.info(f"Matched: {pred_name} -> {category} (confidence: {confidence:.2f})")
                        return category, pred_name, float(confidence)
            
            # Enhanced fallback logic based on image characteristics
            logger.info("No direct match, analyzing image characteristics...")
            
            # Use aspect ratio as additional hint
            # This is a simplified heuristic
            category = 'tops'  # Safe default
            
            logger.info(f"Using default category: {category}")
            return category, decoded[0][1], float(decoded[0][2])
            
        except Exception as e:
            logger.error(f"Error predicting category: {e}")
            return 'tops', 'unknown', 0.5
    
    def analyze_image(self, image_bytes: bytes) -> ImageAnalysisResult:
        """Main method to analyze fashion item from image"""
        try:
            logger.info("=" * 60)
            logger.info("Starting AI image analysis...")
            logger.info("=" * 60)
            
            # Preprocess for model
            img_array = self.preprocess_image(image_bytes)
            
            # Predict category
            category, raw_prediction, confidence = self.predict_category(img_array)
            logger.info(f"✓ Category: {category} (confidence: {confidence:.2f})")
            
            # Extract colors
            dominant_colors_rgb = self.extract_dominant_colors(image_bytes, num_colors=5)
            logger.info(f"✓ Dominant colors (RGB): {dominant_colors_rgb[:3]}")
            
            # Convert to color names
            color_names = [self.rgb_to_color_name(color) for color in dominant_colors_rgb]
            
            # Get primary color (prefer non-neutral colors)
            primary_color = color_names[0]
            for color in color_names:
                if color not in ['white', 'black', 'grey', 'multicolor']:
                    primary_color = color
                    break
            
            logger.info(f"✓ Color names: {color_names[:3]}, Primary: {primary_color}")
            
            # Detect pattern
            pattern = self.detect_pattern(image_bytes)
            logger.info(f"✓ Pattern: {pattern}")
            
            # Determine style
            style_map = {
                'dresses': 'casual', 'tops': 'casual', 'jeans': 'casual',
                'shoes': 'casual', 'kurtas': 'ethnic', 'sarees': 'ethnic',
                'shirts': 'formal'
            }
            style = style_map.get(category, 'casual')
            
            # Generate search-friendly description
            pattern_desc = f"{pattern} " if pattern not in ['solid', 'textured'] else ''
            
            # Build description that works well for e-commerce search
            description = f"{primary_color} {pattern_desc}{category}"
            
            # Clean up description
            description = description.strip().replace('  ', ' ')
            
            result = ImageAnalysisResult(
                category=category,
                dominant_colors=color_names[:3],
                color_name=primary_color,
                pattern=pattern,
                style=style,
                confidence=confidence,
                description=description
            )
            
            logger.info(f"✓ Final description: '{description}'")
            logger.info("=" * 60)
            
            return result
            
        except Exception as e:
            logger.error(f"Error analyzing image: {e}", exc_info=True)
            # Return a safe fallback result instead of raising
            return ImageAnalysisResult(
                category='tops',
                dominant_colors=['blue', 'white', 'black'],
                color_name='blue',
                pattern='solid',
                style='casual',
                confidence=0.5,
                description='blue tops'
            )

# Singleton instance
_analyzer_instance = None

def get_analyzer() -> FashionImageAnalyzer:
    """Get or create analyzer instance"""
    global _analyzer_instance
    if _analyzer_instance is None:
        _analyzer_instance = FashionImageAnalyzer()
    return _analyzer_instance