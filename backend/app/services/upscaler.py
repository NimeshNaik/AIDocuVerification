import io
import torch
import numpy as np
from PIL import Image
from transformers import AutoImageProcessor, Swin2SRForImageSuperResolution

class ImageUpscaler:
    """
    Service for upscaling images using Swin2SR model.
    """
    _instance = None
    _model = None
    _processor = None
    
    @classmethod
    def get_instance(cls):
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance
    
    def __init__(self):
        """Initialize model and processor (lazy loading recommended in production, but here we load on init/first use)."""
        self.device = "cuda" if torch.cuda.is_available() else "cpu"
        self.model_name = "caidas/swin2SR-classical-sr-x2-64"
        print(f"Initializing Upscaler with {self.model_name} on {self.device}...")
        
    def _load_model(self):
        """Load model if not already loaded."""
        if self._model is None:
            try:
                self._processor = AutoImageProcessor.from_pretrained(self.model_name)
                self._model = Swin2SRForImageSuperResolution.from_pretrained(self.model_name).to(self.device)
                print("Upscaler model loaded successfully.")
            except Exception as e:
                print(f"Error loading upscaler model: {e}")
                raise e

    def upscale_image(self, image_bytes: bytes) -> bytes:
        """
        Upscale an image by 4x.
        
        Args:
            image_bytes: Raw image bytes
            
        Returns:
            Upscaled image as JPEG bytes
        """
        self._load_model()
        
        try:
            # Load image
            image = Image.open(io.BytesIO(image_bytes)).convert("RGB")
            
            # Prepare input
            inputs = self._processor(image, return_tensors="pt").to(self.device)
            
            # Run inference
            with torch.no_grad():
                outputs = self._model(**inputs)
            
            # Post-process
            output = outputs.reconstruction.data.squeeze().float().cpu().clamp_(0, 1).numpy()
            output = np.moveaxis(output, 0, -1)
            output = (output * 255.0).round().astype(np.uint8)
            upscaled_image = Image.fromarray(output)
            
            # Save to bytes
            output_buffer = io.BytesIO()
            upscaled_image.save(output_buffer, format="JPEG", quality=95)
            return output_buffer.getvalue()
            
        except Exception as e:
            print(f"Upscaling failed: {e}")
            raise e

upscaler = ImageUpscaler.get_instance()
