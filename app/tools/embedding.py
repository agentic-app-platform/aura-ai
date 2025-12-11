"""
Image embedding service using random vectors.
Generates random vector embeddings for images (no CLIP model).
"""

import numpy as np
from PIL import Image
from typing import List, Optional, Union
import asyncio


class EmbeddingService:
    """
    Generates random vector embeddings for images.
    No CLIP model - just generates random normalized vectors.
    """

    def _init_(self, model_name: Optional[str] = None):
        """
        Initialize embedding service.
        model_name parameter is ignored (kept for compatibility).
        """
        self.model_name = "random-vector-generator"
        # Use a seed based on image content for consistent random vectors per image
        self._rng = np.random.default_rng()

    def _generate_random_embedding(self, image_input: Union[str, Image.Image]) -> np.ndarray:
        """
        Generate a random normalized 768-dimensional embedding.
        Uses image hash as seed for consistency (same image = same embedding).
        """
        try:
            # Create a simple hash from image to use as seed
            if isinstance(image_input, str):
                # Use URL string as seed
                seed = hash(image_input) % (2**32)
            elif isinstance(image_input, Image.Image):
                # Use image size and mode as seed
                seed = hash((image_input.size, image_input.mode)) % (2**32)
            else:
                # Fallback: use random seed
                seed = None
            
            # Generate random vector with seed for consistency
            if seed is not None:
                rng = np.random.default_rng(seed)
            else:
                rng = self._rng
            
            # Generate random 768-dimensional vector
            embedding = rng.normal(0, 1, size=768).astype(np.float32)
            
            # Normalize to unit vector
            norm = np.linalg.norm(embedding)
            if norm > 0:
                embedding = embedding / norm
            
            return embedding

        except Exception as e:
            input_desc = image_input if isinstance(image_input, str) else "PIL Image"
            print(f"Error generating random embedding for {input_desc}: {e}")
            # Return zero vector on failure
            return np.zeros(768)

    def _get_embedding_sync(self, image_input: Union[str, Image.Image]) -> np.ndarray:
        """
        Synchronous internal method to generate random embedding.
        """
        return self._generate_random_embedding(image_input)

    async def get_image_embedding(self, image_input: Union[str, Image.Image]) -> np.ndarray:
        """
        Generates random embedding for an image (from URL or PIL Image).

        Args:
            image_input: URL string of the image OR PIL Image object

        Returns:
            Normalized 768-dimensional numpy array embedding vector
        """
        return await asyncio.to_thread(self._get_embedding_sync, image_input)

    async def get_image_embeddings(
        self, image_inputs: List[Union[str, Image.Image]]
    ) -> List[np.ndarray]:
        """
        Generate random embeddings for multiple images.

        Args:
            image_inputs: List of image URLs or PIL Image objects

        Returns:
            List of embedding vectors
        """
        tasks = [self.get_image_embedding(img) for img in image_inputs]
        return await asyncio.gather(*tasks)