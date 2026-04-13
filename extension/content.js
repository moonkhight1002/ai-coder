const EMPTY_RESPONSE = {
  ok: false,
  error: "Unsupported page"
};

function getPlatform() {
  const adapters = window.LEETBOT_PLATFORMS || [];
  return adapters.find((item) => {
    try {
      return item.matches();
    } catch (error) {
      return false;
    }
  }) || null;
}

function extractLabeledBlocks(statement, labelPrefix) {
  return statement
    .split("\n")
    .map((line) => line.trim())
    .filter((line) => line.startsWith(labelPrefix));
}

function detectLanguage(platform) {
  try {
    return platform?.language?.() || "python3";
  } catch (error) {
    return "python3";
  }
}

function readVisibleEditorValue() {
  const textarea = document.querySelector(".monaco-editor textarea, [data-keybinding-context] textarea");
  if (textarea && typeof textarea.value === "string" && textarea.value.trim()) {
    return textarea.value;
  }

  const monacoLines = document.querySelector(".monaco-editor .view-lines");
  if (monacoLines && monacoLines.textContent && monacoLines.textContent.trim()) {
    return monacoLines.textContent;
  }

  const editorRegion = document.querySelector('[class*="monaco-editor"]');
  if (editorRegion && editorRegion.textContent && editorRegion.textContent.trim()) {
    return editorRegion.textContent;
  }

  return "";
}

function extractProblem() {
  const platform = getPlatform();
  if (!platform) {
    return EMPTY_RESPONSE;
  }

  const statement = platform.statement?.() || "";
  const title = platform.title?.() || document.title.trim();
  const slug = platform.slug?.() || location.pathname.split("/").filter(Boolean).join("-");
  const language = detectLanguage(platform);
  const starterCode = readVisibleEditorValue();
  const nextUrl = platform.nextUrl?.() || "";

  if (!statement) {
    return {
      ok: false,
      error: "Could not extract the problem statement from this page.",
      platform: platform.id,
      platformLabel: platform.label
    };
  }

  return {
    ok: true,
    problem: {
      platform: platform.id,
      platformLabel: platform.label,
      title,
      slug,
      url: location.href,
      statement,
      language,
      starterCode,
      nextUrl,
      examples: extractLabeledBlocks(statement, "Example"),
      constraints: extractLabeledBlocks(statement, "Constraints")
    }
  };
}

chrome.runtime.onMessage.addListener((message, sender, sendResponse) => {
  if (message?.type === "leetbot:extract-problem") {
    sendResponse(extractProblem());
    return true;
  }

  if (message?.type === "leetbot:ping") {
    sendResponse({
      ok: true,
      platform: getPlatform()?.label || "unsupported"
    });
    return true;
  }

  return false;
});
