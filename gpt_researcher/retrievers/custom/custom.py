from typing import Any, Dict, List
import requests
import base64
import json
import sys
import os

class CustomRetriever:
    """
    Custom API Retriever
    """

    def __init__(self, query: str, query_domains=None):
        self.endpoint = os.getenv('RETRIEVER_ENDPOINT')
        if not self.endpoint:
            raise ValueError("RETRIEVER_ENDPOINT environment variable not set")

        self.params = self._populate_params()
        self.query = query

    def _populate_params(self) -> Dict[str, Any]:
        """
        Populates parameters from environment variables prefixed with 'RETRIEVER_ARG_'
        """
        return {
            key[len('RETRIEVER_ARG_'):].lower(): value
            for key, value in os.environ.items()
            if key.startswith('RETRIEVER_ARG_')
        }

    def search(self, max_results: int = 5) -> List[Dict[str, Any]]:
        """
        Performs the search using the custom retriever endpoint,
        decodes the Base64 payloads, and returns a list of dicts
        each having 'href', 'title', and 'body'.
        """
        try:
            response = requests.get(
                self.endpoint,
                params={**self.params, 'query': self.query}
            )
            response.raise_for_status()

            # Extract base64-encoded results
            data = response.json().get("results", [])

            wrapped: List[Dict[str, Any]] = []
            for enc in data:
                # Decode base64 and parse JSON
                decoded = base64.b64decode(enc).decode("utf-8")
                parsed = json.loads(decoded)

                href = parsed["URL"].strip()
                body = parsed.get("Clean-Text", "")
                title = body.split("\n", 1)[0]

                wrapped.append({
                    "href": href,
                    "title": title,
                    "body": body,
                })

                if len(wrapped) >= max_results:
                    break

            return wrapped

        except requests.RequestException as e:
            print(f"Failed to retrieve search results: {e}", file=sys.stderr)
            return []

