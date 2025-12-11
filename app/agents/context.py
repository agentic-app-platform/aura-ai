from typing import Optional

from langchain_core.messages import AIMessage
from langchain_core.runnables.config import RunnableConfig
from langgraph.store.base import BaseStore

# from app.dao.chat_message_dao import get_messages
from app.schema import ChatQuery
from app.state import AgentState
from app.tools.extraction import ChatQueryExtraction, extract_chat_query_tool
from app.tools.intent import check_initial_intent


async def context_agent(
    state: AgentState, config: RunnableConfig, *, store: Optional[BaseStore] = None
):
    print("Context Agent")
    """
    Analyzes user intent and profile to determine next steps using an LLM.
    """
    # Extract user_id and thread_id from config
    user_id = config["metadata"]["user_id"]
    thread_id = config["metadata"]["thread_id"]

    # Check if the input is related to shopping (context-aware)
    initial_intent = await check_initial_intent(state.get("messages"))
    if not initial_intent.is_shopping_related:
        return {
            "user_intent": "general_chat",
            "next_step": "END",
            "current_agent": "context_agent",
            "messages": [AIMessage(content=initial_intent.response_if_not_related)],
        }

    # 1. Extract intents from conversation messages (last 5 user messages)
    # Context agent uses the whole messages history (emphasizes last messages)
    all_messages = state.get("messages", [])
    print(f"📋 Context agent using {len(all_messages)} messages from conversation history")
    extracted_data: ChatQueryExtraction = await extract_chat_query_tool(all_messages)

    # 2. Convert extraction to ChatQuery (stored in AgentState, not separate table)
    # Get existing chat_query_json from state if available
    existing_query = state.get("chat_query_json")
    
    if existing_query:
        # Update existing ChatQuery with new extracted data
        update_data = extracted_data.model_dump(exclude_none=True)
        for key, value in update_data.items():
            if hasattr(existing_query, key):
                setattr(existing_query, key, value)
        final_query = existing_query
    else:
        # Create new ChatQuery from extraction (no user_id/thread_id needed - stored in AgentState)
        final_query = ChatQuery(**extracted_data.model_dump(exclude_none=True))

    # Deterministic Routing based on Missing Fields
    missing_fields = []
    if not final_query.destination:
        missing_fields.append("destination")
    if not final_query.category:
        missing_fields.append("product type")
    if not final_query.occasion:
        missing_fields.append("occasion")

    if missing_fields:
        response_msg = f"To generate the best recommendations, I need to know the {', '.join(missing_fields)}."
        return {
            "user_intent": "clarification",
            "next_step": "END",
            "current_agent": "context_agent",
            "messages": [AIMessage(content=response_msg)],
        }
    else:
        # All fields present - proceed to research
        # Send initial message to user that we're processing
        return {
            "user_intent": "recommendation",
            "next_step": "research_agent",
            "current_agent": "context_agent",
            "messages": [
                AIMessage(
                    content="Great! I have all the details. Searching for products and generating styling visualizations... This may take a moment."
                )
            ],
            "chat_query_json": final_query,
        }
