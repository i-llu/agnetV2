import requests
from .tool_config import Config

class WebService:

  def __init__(self):
     self.serpapi_key = Config.SERPAPI_KEY

  def web_search(self, query: str) -> str:
    try:
        response = requests.get(
            "https://serpapi.com/search",
            params={
                "q": query,
                "api_key": self.serpapi_key,
                "engine": "google",
            },
            timeout=10,
        )
        response.raise_for_status()
        data = response.json()

        results = data.get("organic_results", [])[:5]
        if not results:
            return "No results found."

        formatted = "\n\n".join(
            f"{r.get('title')}\n{r.get('link')}\n{r.get('snippet', '')}"
            for r in results
        )
        return formatted
    except Exception as e:
        return f"Search failed: {e}"