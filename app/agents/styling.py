from typing import Optional, List
import numpy as np

from langchain_core.messages import AIMessage
from langchain_core.runnables.config import RunnableConfig
from langchain_core.stores import BaseStore

from app.state import AgentState
from app.tools.image_merging import ImageMergingService
from app.tools.embedding import EmbeddingService


def styling_agent(
    state: AgentState, config: RunnableConfig, *, store: Optional[BaseStore] = None
):
    """
    Visualizes products on the user by:
    1. Merging user photos with product images using Gemini 3 Pro Image Preview model
    2. Generating embeddings for each merged image using CLIP
    3. Returning list of vector embeddings
    """
    print("Styling Agent")
    
    # Get search results from research agent
    search_results = state.get("search_results", [])
    if not search_results:
        return {
            "messages": [AIMessage(content="I couldn't find any items to style.")],
            "current_agent": "styling_agent",
            "next_step": None,
            "merged_image_embeddings": [],
        }

    # Get user photos from profile
    user_profile = state.get("user_profile", {})
    user_photo_urls = user_profile.get("photo_urls", [])
    
    if not user_photo_urls:
        return {
            "messages": [
                AIMessage(
                    content="I need your photos to show how the products look on you. Please upload your photos."
                )
            ],
            "current_agent": "styling_agent",
            "next_step": None,
            "merged_image_embeddings": [],
        }

    # Initialize services
    image_merging_service = ImageMergingService()
    embedding_service = EmbeddingService()

    # Process each product with user photos
    merged_image_embeddings: List[np.ndarray] = []
    processed_count = 0

    # Use first user photo (can be extended to use multiple)
    user_photo_url = user_photo_urls[0]

    for product in search_results:
        try:
            # Merge user photo with product image using Gemini 3 Pro Image Preview
            merged_image = image_merging_service.merge_images(
                user_photo_url, product.image
            )

            # Generate embedding for merged image (now accepts PIL Image directly)
            embedding = embedding_service.get_image_embedding(merged_image)
            merged_image_embeddings.append(embedding)
            processed_count += 1

        except Exception as e:
            print(f"Error processing product {product.title}: {e}")
            continue

    if not merged_image_embeddings:
        return {
            "messages": [
                AIMessage(
                    content="I encountered an error while processing the images. Please try again."
                )
            ],
            "current_agent": "styling_agent",
            "next_step": None,
            "merged_image_embeddings": [],
        }

    return {
        "messages": [
            AIMessage(
                content=f"I've generated styling visualizations for {processed_count} product(s). Here are the embeddings."
            )
        ],
        "selected_item": search_results[0] if search_results else None,
        "current_agent": "styling_agent",
        "next_step": None,
        "merged_image_embeddings": merged_image_embeddings,
    }
