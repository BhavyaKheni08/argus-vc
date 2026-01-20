import os
from tavily import TavilyClient

# Initialize the Tavily client
# The client is instantiated globally as requested, expecting the environment variable to be present.
_api_key = os.getenv("TAVILY_API_KEY")
# We handle the case where the key might be missing gracefully in the function or during init if possible.
# However, the prompt implies simple instantiation. 
# We'll stick to a global client but adding a check in the function is good practice.
tavily_client = TavilyClient(api_key=_api_key) if _api_key else None

def perform_live_search(query: str, search_depth="advanced", topic="general") -> str:
    """
    Performs a live search using the Tavily API and returns formatted results.

    Args:
        query (str): The search query.
        search_depth (str): The depth of search ("basic" or "advanced"). Defaults to "advanced".
        topic (str): The topic of search ("general" or "news"). Defaults to "general".

    Returns:
        str: A formatted string of search results suitable for LLM consumption.
    """
    if not tavily_client:
        return "Error: TAVILY_API_KEY is not set in the environment variables."

    try:
        # The Tavily Python SDK handles the parameters directly.
        # We pass the topic and search_depth as requested.
        response = tavily_client.search(
            query=query,
            search_depth=search_depth,
            topic=topic
        )

        results = response.get("results", [])
        if not results:
            return "No results found."

        formatted_output = ""
        for result in results:
            title = result.get("title", "No Title")
            url = result.get("url", "No URL")
            content = result.get("content", "No Content")

            formatted_output += f"Source: {title} - {url} \n Content: {content} \n\n"

        return formatted_output.strip()

    except Exception as e:
        # Handle connection errors and other exceptions gracefully
        return f"Error occurred during search: {str(e)}"
