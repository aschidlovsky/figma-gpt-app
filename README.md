# Figma GPT App

This repository contains a simple Python application that connects to the
Figma REST API and uses OpenAI's ChatGPT API to generate concise feature
descriptions based on the names of top‑level frames in a Figma design.

## How it works

1. **Fetch design data from Figma.**  The app uses the `/v1/files/{file_key}`
   endpoint of the Figma REST API to retrieve the JSON structure of a file.
   Authentication is done via a personal access token passed in the
   `X‑Figma‑Token` header【876613816359908†L21-L45】.
2. **Extract frame names.**  The code walks the file tree and collects the
   names of top‑level frames (i.e. frames directly under each page).
3. **Generate feature suggestions.**  It sends the frame names to the ChatGPT
   API and asks the model to return a JSON array of objects with `title`
   and `description` fields.  The suggestions can be used to guide
   requirements writing or backlog grooming.

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

The script will print the names of the frames it finds and the feature
suggestions returned by ChatGPT.

## Deployment

You can deploy this app to cloud services such as [Railway](https://railway.app)
by creating a project, connecting your GitHub repository and configuring
environment variables.  The app runs as a simple one‑off script, so you
may need to wrap it in a web framework or scheduled job depending on your
deployment target.