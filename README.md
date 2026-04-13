# Coding Platform Study Solver

This project is a local Chrome extension plus Python backend that helps you study supported coding-platform problems from inside the browser.

What it does:

- detects when a supported problem page is open
- extracts the visible problem statement and starter code from the current tab
- sends that data to a local backend
- generates a draft solution
- shows the result inside the extension popup
- lets you copy the generated code and notes manually

Important limitation:

- This project is a study assistant. It does not auto-submit solutions or claim hidden tests passed.
- It does not inject an in-page control panel anymore. The coding site page is left alone and the extension popup is the UI.
- It does not include stealth, anti-detection bypass, or any attempt to evade platform safeguards.

## Supported Platforms

- `LeetCode`
- `HackerRank`
- `CodeChef`
- `Codeforces`
- `AtCoder`

The extension uses a platform-adapter registry in `extension/platforms.js`, so more sites can be added cleanly.

## Project Layout

- `extension/`: Chrome extension files
- `backend/`: local Python backend and tests
- `run_backend.cmd`: starts the backend using a known local Python interpreter
- `run_backend_tests.cmd`: runs backend verification tests

## Quick Start

1. Start the backend:

```cmd
run_backend.cmd
```

2. Load the Chrome extension:

- Open `chrome://extensions`
- Enable Developer Mode
- Click `Load unpacked`
- Select the `extension` folder

3. Open a supported problem page.

4. Click the extension icon.

5. In the popup:

- configure the backend and AI provider if needed
- click `Solve Current Page`
- review the output in the popup
- use `Copy Code` or `Copy Notes`

## How To Use

1. Double-click `run_backend.cmd`.
2. In Chrome, open `chrome://extensions`.
3. Turn on `Developer mode`.
4. Click `Load unpacked` and choose the `extension` folder inside this project.
5. Open a supported problem page.
6. Click `Solve Current Page` in the popup.
7. Copy the generated code manually into the site editor if you want to test it.

## Compliance Notes

- Keep submissions manual.
- Use it as a visible drafting tool, not a hidden automation layer.
- Avoid excessive request loops or unattended interaction on third-party platforms.
- If a site changes its DOM or editor integration, update selectors instead of trying to bypass platform behavior.

## Backend Configuration

By default the backend can run in three useful modes:

- `Local Fallback`: free, offline, weaker starter drafts
- `OpenAI Compatible`: any hosted OpenAI-compatible API
- `Ollama Local`: free local model runtime on your machine

The popup now includes a `Quick Setup` selector for the common paths.

### Fastest free setup: Ollama

1. Install Ollama.
2. Pull a local model, for example:

```cmd
ollama pull llama3.2
```

3. Keep Ollama running.
4. In the popup choose:

- Quick Setup: `Ollama Local (Free)`
- Model: `llama3.2` or any model you have pulled
- API URL: `http://127.0.0.1:11434/v1/chat/completions`
- API Key: leave blank

You can also copy [provider_config.ollama.example.json](backend/provider_config.ollama.example.json) to `backend/provider_config.local.json`.

### OpenAI or another hosted provider

The backend now supports both of these OpenAI-compatible endpoint styles:

- `https://.../v1/responses`
- `https://.../v1/chat/completions`

That means you can use OpenAI-compatible providers beyond the OpenAI API itself as long as you supply:

- a supported model name
- the provider's base URL for `responses` or `chat/completions`
- an API key when the provider requires one

The backend also supports environment variables before startup:

- `LEETBOT_PROVIDER=openai`
- `LEETBOT_API_KEY=...`
- `LEETBOT_MODEL=...`
- `LEETBOT_API_URL=...`

The backend uses only the Python standard library, so no package install is required.

## Verification

Run:

```cmd
run_backend_tests.cmd
```

This checks the provider fallback logic and the HTTP API round-trip.

## Notes

- DOM selectors can change over time, so the content script is structured around per-platform adapters for easier updates.
- The extension now uses a popup-only workflow to avoid interfering with coding site editors or navigation.

## Open Source

This project is available under the [MIT License](LICENSE).

Before publishing to GitHub:

- do not commit `backend/provider_config.local.json`
- rotate any API key that has already been pasted into chat, screenshots, or local files you may upload
- keep only the example config files in the public repo
