(() => {
  if (window.__LEETBOT_BRIDGE_INSTALLED__) {
    return;
  }
  window.__LEETBOT_BRIDGE_INSTALLED__ = true;

  function selectBestModel() {
    if (!window.monaco || typeof window.monaco.editor?.getModels !== "function") {
      return null;
    }
    const models = window.monaco.editor
      .getModels()
      .filter((model) => model && typeof model.getValue === "function");
    if (!models.length) {
      return null;
    }
    models.sort((left, right) => right.getValue().length - left.getValue().length);
    return models[0];
  }

  function readMonacoValue() {
    try {
      const model = selectBestModel();
      if (model) {
        return { ok: true, value: model.getValue(), method: "monaco-bridge" };
      }
    } catch (error) {
      return { ok: false, message: String(error) };
    }
    return { ok: false, message: "No Monaco model found." };
  }

  function writeMonacoValue(code) {
    try {
      const model = selectBestModel();
      if (model) {
        model.setValue(code);
        return { ok: true, method: "monaco-bridge" };
      }
    } catch (error) {
      return { ok: false, message: String(error) };
    }
    return { ok: false, message: "No Monaco model found." };
  }

  window.addEventListener("leetbot:bridge:read", () => {
    window.dispatchEvent(
      new CustomEvent("leetbot:bridge:read-response", {
        detail: readMonacoValue()
      })
    );
  });

  window.addEventListener("leetbot:bridge:write", (event) => {
    const code = event.detail?.code || "";
    window.dispatchEvent(
      new CustomEvent("leetbot:bridge:write-response", {
        detail: writeMonacoValue(code)
      })
    );
  });
})();
