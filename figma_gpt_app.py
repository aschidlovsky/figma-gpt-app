"""
figma_gpt_app.py
=================

This module demonstrates how to build a simple integration between Figma and
OpenAI's ChatGPT API using Python.  The goal of the integration is to fetch
information about a design from Figma and analyse it with ChatGPT.  The
resulting analysis can then be used to write requirements or features, but
this example does **not** push anything into Azure DevOps.

Key points:

* **Figma REST API.**  Figma exposes a REST API; the ``/v1/files/{file_key}``
  endpoint returns the full JSON document of a Figma file.  The Figma R
  package documentation summarises this endpoint: it uses the ``/v1/files/``
  path and requires a personal access token to authenticate【876613816359908†L21-L45】.
  The returned JSON includes pages, frames and other nodes that represent
  the design.

* **OpenAI ChatGPT API.**  The ChatGPT API is called via
  ``https://api.openai.com/v1/chat/completions``.  The caller must set an
  ``OPENAI_API_KEY`` environment variable or pass an explicit API key when
  calling ``generate_features_from_figma``.  The model (e.g. ``gpt-4`` or
  ``gpt-3.5-turbo``) and sampling parameters can be configured.

* **Security.**  This code accepts API tokens via arguments or environment
  variables.  Never commit your tokens into source control.  In production
  you should implement proper error handling, logging and secure storage of
  credentials.

This example is for demonstration purposes.  It shows how to fetch a Figma
file, extract frame names, craft a prompt and send it to ChatGPT to generate
feature descriptions.  You can build upon these primitives to suit your
workflow (e.g. summarising designs, generating acceptance criteria, etc.).
"""

from __future__ import annotations

import json
import os
from typing import Any, Dict, Iterable, List, Optional

import requests


class FigmaClient:
    """Simple wrapper around the Figma REST API."""

    def __init__(self, token: str, base_url: str = "https://api.figma.com/v1"):
        self.token = token
        self.base_url = base_url.rstrip("/")

    def _headers(self) -> Dict[str, str]:
        """Return headers for Figma API requests."""
        return {"X-Figma-Token": self.token}

    def get_file(self, file_key: str) -> Dict[str, Any]:
        """Fetch the full document tree of a Figma file.

        The Figma API's ``/v1/files/{file_key}`` endpoint returns the full
        structure of a file, including pages and nodes.  You must supply
        your personal access token in the ``X-Figma-Token`` header
        【876613816359908†L21-L45】.

        :param file_key: The key of the Figma file (found in its URL).
        :returns: Parsed JSON response from the API.
        :raises: ``requests.HTTPError`` for non‑200 responses.
        """
        url = f"{self.base_url}/files/{file_key}"
        resp = requests.get(url, headers=self._headers())
        if not resp.ok:
            # Raise an exception with detailed message for any error response.
            resp.raise_for_status()
        return resp.json()


def extract_frame_names(file_data: Dict[str, Any]) -> List[str]:
    """Extract the names of top‑level frames from a Figma file JSON structure.

    This helper walks through the pages in the file and collects the names
    of any immediate children whose ``type`` is ``FRAME``.  The logic is
    simple but can be adjusted to suit your needs (e.g. include nested
    frames or specific component names).

    :param file_data: The JSON object returned by ``FigmaClient.get_file``.
    :returns: A list of frame names.
    """
    frames: List[str] = []
    document = file_data.get("document", {})
    pages = document.get("children", [])
    for page in pages:
        for node in page.get("children", []):
            if node.get("type") == "FRAME":
                name = node.get("name")
                if name:
                    frames.append(name)
    return frames


def generate_features_from_figma(
    frame_names: Iterable[str],
    openai_api_key: str,
    *,
    model: str = "gpt-4",
    temperature: float = 0.2,
    max_tokens: int = 512,
) -> List[Dict[str, str]]:
    """Generate user stories/features from Figma frame names using ChatGPT.

    Given a collection of frame names extracted from a design, this function
    constructs a prompt asking ChatGPT to write concise feature suggestions.
    It sends a ``POST`` request to the OpenAI API and parses the response
    into a list of dictionaries containing titles and descriptions.  If
    ``frame_names`` is empty, an empty list is returned.

    :param frame_names: A list or other iterable of frame names.
    :param openai_api_key: Your OpenAI API key.
    :param model: The model to use (default ``gpt-4``).
    :param temperature: Sampling temperature for the model.
    :param max_tokens: Maximum number of tokens in the response.
    :returns: A list of dicts with ``title`` and ``description`` keys.
    :raises: ``requests.HTTPError`` if the API call fails.
    """
    frame_names_list = list(frame_names)
    if not frame_names_list:
        return []
    # Format the frame names as a bullet list for the prompt.
    frames_formatted = "\n".join(f"- {name}" for name in frame_names_list)
    prompt = (
        "The following is a list of design sections extracted from a Figma "
        "file.  For each section, suggest a concise feature title and a short "
        "description (one sentence) suitable for inclusion in a product "
        "requirements document.  Respond with a JSON array where each element "
        "has 'title' and 'description' fields.\n"\
        f"\nDesign sections:\n{frames_formatted}\n"
    )
    # Build the chat messages structure expected by the OpenAI API.
    messages = [
        {"role": "system", "content": "You are a helpful product manager."},
        {"role": "user", "content": prompt},
    ]
    headers = {
        "Authorization": f"Bearer {openai_api_key}",
        "Content-Type": "application/json",
    }
    body = {
        "model": model,
        "temperature": temperature,
        "max_tokens": max_tokens,
        "messages": messages,
        "n": 1,
    }
    url = "https://api.openai.com/v1/chat/completions"
    resp = requests.post(url, headers=headers, data=json.dumps(body))
    if not resp.ok:
        resp.raise_for_status()
    data = resp.json()
    # Extract the content of the first choice.
    content = data.get("choices", [{}])[0].get("message", {}).get("content", "")
    # Try to parse the content as JSON.  If parsing fails, return an empty list.
    try:
        features: List[Dict[str, str]] = json.loads(content)
        # Ensure each element has title and description keys.
        return [
            {
                "title": item.get("title", "Untitled Feature"),
                "description": item.get("description", "")
            }
            for item in features if isinstance(item, dict)
        ]
    except json.JSONDecodeError:
        # If the model didn't respond with valid JSON, return the raw text as a
        # single element for diagnostic purposes.
        return [{"title": "Model response", "description": content}]


def main() -> None:
    """Example command line interface.

    This function demonstrates how to use the classes and functions defined
    above.  It expects the following environment variables to be set:

    * ``FIGMA_TOKEN`` – a personal access token with at least read access
      to the Figma file you want to process.
    * ``FIGMA_FILE_KEY`` – the key of the Figma file (found in the file's URL).
    * ``OPENAI_API_KEY`` – your OpenAI API key for ChatGPT.

    It fetches the file, extracts frame names, uses ChatGPT to generate
    feature suggestions, and prints the results to standard output.
    """
    figma_token = os.environ.get("FIGMA_TOKEN")
    figma_file_key = os.environ.get("FIGMA_FILE_KEY")
    openai_key = os.environ.get("OPENAI_API_KEY")
    if not (figma_token and figma_file_key and openai_key):
        print(
            "FIGMA_TOKEN, FIGMA_FILE_KEY and OPENAI_API_KEY environment variables "
            "must be set to run this example."
        )
        return
    figma_client = FigmaClient(figma_token)
    file_data = figma_client.get_file(figma_file_key)
    frame_names = extract_frame_names(file_data)
    if not frame_names:
        print("No frames were found in the Figma document.")
        return
    print(f"Found {len(frame_names)} top‑level frame(s): {', '.join(frame_names)}")
    features = generate_features_from_figma(frame_names, openai_key)
    print("\nGenerated feature suggestions:\n")
    for feature in features:
        print(f"- {feature['title']}: {feature['description']}")


if __name__ == "__main__":
    main()