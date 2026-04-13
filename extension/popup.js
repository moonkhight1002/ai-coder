const defaults = {
  backendUrl: "http://127.0.0.1:8765",
  providerPreset: "openai",
  providerName: "openai",
  modelName: "gpt-4.1-mini",
  apiKey: "",
  apiUrl: "https://api.openai.com/v1/responses"
};

const presets = {
  openai: {
    providerName: "openai",
    modelName: "gpt-4.1-mini",
    apiKey: "",
    apiUrl: "https://api.openai.com/v1/responses",
    apiKeyPlaceholder: "sk-...",
    help: "Requires OpenAI API credits. Use this for the hosted OpenAI Responses API."
  },
  ollama: {
    providerName: "openai",
    modelName: "llama3.2",
    apiKey: "",
    apiUrl: "http://127.0.0.1:11434/v1/chat/completions",
    apiKeyPlaceholder: "Optional for local Ollama",
    help: "Free local setup. Install Ollama, pull a model such as `llama3.2`, then keep Ollama running."
  },
  rule_based: {
    providerName: "rule_based",
    modelName: "rule-based",
    apiKey: "",
    apiUrl: "https://api.openai.com/v1/responses",
    apiKeyPlaceholder: "Not used in fallback mode",
    help: "Works fully offline with no model provider, but only creates a starter draft."
  }
};

const backendUrlInput = document.getElementById("backendUrl");
const providerPresetInput = document.getElementById("providerPreset");
const providerNameInput = document.getElementById("providerName");
const modelNameInput = document.getElementById("modelName");
const apiKeyInput = document.getElementById("apiKey");
const apiUrlInput = document.getElementById("apiUrl");
const presetHelp = document.getElementById("presetHelp");
const saveButton = document.getElementById("saveButton");
const solveButton = document.getElementById("solveButton");
const copyCodeButton = document.getElementById("copyCodeButton");
const copyExplanationButton = document.getElementById("copyExplanationButton");
const statusText = document.getElementById("statusText");
const backendBadge = document.getElementById("backendBadge");
const pageBadge = document.getElementById("pageBadge");
const providerBadge = document.getElementById("providerBadge");
const problemMeta = document.getElementById("problemMeta");
const resultSummary = document.getElementById("resultSummary");
const codeOutput = document.getElementById("codeOutput");
const notesOutput = document.getElementById("notesOutput");

function setStatus(text) {
  statusText.textContent = text;
}

function setBadge(element, text, online = null) {
  element.textContent = text;
  if (online === null) {
    element.className = "badge badge-muted";
    return;
  }
  element.className = `badge ${online ? "badge-success" : "badge-muted"}`;
}

function currentSettings() {
  return {
    backendUrl: backendUrlInput.value.trim() || defaults.backendUrl,
    providerPreset: providerPresetInput.value || defaults.providerPreset,
    providerName: providerNameInput.value || defaults.providerName,
    modelName: modelNameInput.value.trim() || defaults.modelName,
    apiKey: apiKeyInput.value.trim(),
    apiUrl: apiUrlInput.value.trim() || defaults.apiUrl
  };
}

function inferPreset(settings) {
  const providerName = (settings.providerName || "").trim().toLowerCase();
  const apiUrl = (settings.apiUrl || "").trim().toLowerCase();
  if (providerName === "rule_based") {
    return "rule_based";
  }
  if (apiUrl.includes("127.0.0.1:11434") || apiUrl.includes("localhost:11434")) {
    return "ollama";
  }
  return "openai";
}

function applyPreset(presetName) {
  const preset = presets[presetName] || presets.openai;
  providerPresetInput.value = presetName;
  providerNameInput.value = preset.providerName;
  modelNameInput.value = preset.modelName;
  apiKeyInput.value = preset.apiKey;
  apiKeyInput.placeholder = preset.apiKeyPlaceholder;
  apiUrlInput.value = preset.apiUrl;
  presetHelp.textContent = preset.help;
}

function describeError(error) {
  const text = String(error?.message || error || "Unexpected error");
  if (text.includes("HTTP 429")) {
    return "The model provider rejected the request for quota or billing. Switch Quick Setup to Ollama Local for a free setup, or add provider credits.";
  }
  if (text.includes("Unable to reach model provider")) {
    return "The backend could not reach your model provider. If you picked Ollama, make sure Ollama is installed and running.";
  }
  return text;
}

async function checkBackend(url) {
  try {
    const response = await fetch(`${url}/api/health`);
    if (!response.ok) {
      throw new Error("Health check failed");
    }
    const payload = await response.json();
    setBadge(backendBadge, "Online", true);
    setBadge(providerBadge, payload.provider || "unknown");
    return payload;
  } catch (error) {
    setBadge(backendBadge, "Offline", false);
    return null;
  }
}

function loadSettings() {
  chrome.storage.local.get(defaults, async (settings) => {
    backendUrlInput.value = settings.backendUrl;
    const presetName = inferPreset(settings);
    applyPreset(presetName);
    providerNameInput.value = settings.providerName || defaults.providerName;
    modelNameInput.value = settings.modelName || defaults.modelName;
    apiKeyInput.value = settings.apiKey || "";
    apiUrlInput.value = settings.apiUrl || defaults.apiUrl;
    providerPresetInput.value = presetName;
    presetHelp.textContent = (presets[presetName] || presets.openai).help;
    setStatus("Settings loaded");
    await checkBackend(settings.backendUrl || defaults.backendUrl);
  });
}

async function syncBackendConfiguration(settings) {
  const providerResponse = await fetch(`${settings.backendUrl}/api/provider`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      provider: settings.providerName,
      model: settings.modelName,
      apiKey: settings.apiKey,
      apiUrl: settings.apiUrl
    })
  });
  if (!providerResponse.ok) {
    throw new Error("Provider configuration failed");
  }
  return providerResponse.json();
}

function withActiveTab(callback) {
  chrome.tabs.query({ active: true, currentWindow: true }, (tabs) => {
    const activeTab = tabs && tabs[0];
    if (!activeTab?.id) {
      setStatus("No active tab found");
      return;
    }
    callback(activeTab.id);
  });
}

async function extractProblemFromActiveTab() {
  return new Promise((resolve, reject) => {
    withActiveTab((tabId) => {
      chrome.tabs.sendMessage(tabId, { type: "leetbot:extract-problem" }, (response) => {
        if (chrome.runtime.lastError) {
          reject(new Error("Open a supported problem page first."));
          return;
        }
        if (!response?.ok) {
          reject(new Error(response?.error || "Problem extraction failed."));
          return;
        }
        resolve(response.problem);
      });
    });
  });
}

function renderProblem(problem) {
  setBadge(pageBadge, problem.platformLabel || problem.platform || "Unknown");
  problemMeta.textContent = `${problem.title} | ${problem.language} | ${problem.url}`;
}

function renderDraft(draft) {
  setBadge(providerBadge, draft.provider || "unknown");
  codeOutput.value = draft.code || "";
  const notes = [
    draft.analysis || "",
    draft.complexity ? `Complexity: ${draft.complexity}` : "",
    ...(draft.warnings || []).map((warning) => `Warning: ${warning}`)
  ]
    .filter(Boolean)
    .join("\n\n");
  notesOutput.value = notes;
  resultSummary.textContent = draft.provider === "rule_based"
    ? "Fallback draft generated. For full model output, switch Quick Setup to Ollama Local or another OpenAI-compatible provider."
    : "Model-generated draft ready.";
}

async function solveCurrentPage() {
  const settings = currentSettings();
  setStatus("Saving settings");
  chrome.storage.local.set(settings);
  await syncBackendConfiguration(settings);
  await checkBackend(settings.backendUrl);

  setStatus("Reading current page");
  const problem = await extractProblemFromActiveTab();
  renderProblem(problem);

  setStatus("Solving");
  const response = await fetch(`${settings.backendUrl}/api/solve`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      problem,
      autoSolve: false,
      autoAdvance: false
    })
  });
  const payload = await response.json();
  if (!response.ok) {
    throw new Error(payload.error || "Backend solve request failed");
  }

  renderDraft(payload.draft);
  setStatus("Done");
}

async function copyText(value, label) {
  if (!value) {
    setStatus(`No ${label.toLowerCase()} available to copy`);
    return;
  }
  await navigator.clipboard.writeText(value);
  setStatus(`${label} copied`);
}

saveButton.addEventListener("click", async () => {
  const settings = currentSettings();
  chrome.storage.local.set(settings);
  try {
    await syncBackendConfiguration(settings);
    await checkBackend(settings.backendUrl);
    setStatus("Settings saved");
  } catch (error) {
    const message = describeError(error);
    setStatus(message);
    resultSummary.textContent = message;
  }
});

solveButton.addEventListener("click", async () => {
  try {
    await solveCurrentPage();
  } catch (error) {
    const message = describeError(error);
    setStatus(message);
    resultSummary.textContent = message;
  }
});

providerPresetInput.addEventListener("change", () => {
  applyPreset(providerPresetInput.value);
});

copyCodeButton.addEventListener("click", async () => {
  try {
    await copyText(codeOutput.value, "Code");
  } catch (error) {
    setStatus("Copy failed");
  }
});

copyExplanationButton.addEventListener("click", async () => {
  try {
    await copyText(notesOutput.value, "Notes");
  } catch (error) {
    setStatus("Copy failed");
  }
});

loadSettings();
