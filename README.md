# Figma GPT App

This repository contains a Python application that connects to the Figma REST API and uses OpenAI's ChatGPT API to generate feature suggestions from detailed information about a design. Unlike the first version, which only looked at frame names, this iteration extracts a rich context including pages, frames, nested layers, component definitions, style definitions and annotations. The resulting context is sent to ChatGPT to help it understand the intended UX/UI when proposing user stories or feature titles.

## How it works

1. **Fetch design data from Figma.**  The app uses the `/v1/files/{file_key}` endpoint of the Figma REST API to retrieve the full JSON structure of a file.  Authentication is done via a personal access token passed in the `X‑Figma‑Token` header.
2. **Extract rich context.**  It walks the document tree to gather:
   - Page names and top‑level frame names.
   - A flattened list of all layers with their type, name and truncated text content.
   - Component definitions and component set (variant) definitions including names and descriptions.
   - Style definitions (colour, text, grid, effect) with their names and types.
   - References to components and styles from individual layers.
   - Comments on the file, captured as annotations.
3. **Generate feature suggestions.**  The collected context is serialised to JSON and included in a prompt to the ChatGPT API.  The model returns a JSON array of dictionaries with `title` and `description` fields, summarising how the design's UX/UI might translate into requirements.

## Running locally

Install the dependencies and set the required environment variables:

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

# Set your tokens (replace placeholders with actual values)
export FIGMA_TOKEN="your-figma-token"
export FIGMA_FILE_KEY="your-file-key"
export OPENAI_API_KEY="your-openai-api-key"

python figma_gpt_app.py
```
