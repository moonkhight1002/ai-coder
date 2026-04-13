(function attachPlatformAdapters() {
  function textFromSelectors(selectors) {
    for (const selector of selectors) {
      const element = document.querySelector(selector);
      if (element && element.innerText && element.innerText.trim()) {
        return element.innerText.trim();
      }
      if (element && element.textContent && element.textContent.trim()) {
        return element.textContent.trim();
      }
    }
    return "";
  }

  function elementFromSelectors(selectors) {
    for (const selector of selectors) {
      const element = document.querySelector(selector);
      if (element) {
        return element;
      }
    }
    return null;
  }

  function genericNextUrl() {
    const anchors = [...document.querySelectorAll("a[href]")];
    const currentPath = location.pathname.replace(/\/+$/, "");
    const scored = anchors
      .map((candidate) => {
        const text = (candidate.textContent || "").trim().toLowerCase();
        let href = "";
        try {
          href = new URL(candidate.href, location.origin).href;
        } catch (error) {
          return null;
        }
        const url = new URL(href);
        const path = url.pathname.replace(/\/+$/, "");
        if (!isLikelyProblemUrl(url) || path === currentPath) {
          return null;
        }
        let score = 0;
        if (text === "next") score += 10;
        if (text.includes("next problem")) score += 12;
        if (text.includes("next question")) score += 12;
        if (candidate.getAttribute("aria-label")?.toLowerCase().includes("next")) score += 8;
        if (candidate.rel?.toLowerCase().includes("next")) score += 8;
        return { href, score };
      })
      .filter(Boolean)
      .sort((left, right) => right.score - left.score);

    const best = scored.find((item) => item.score > 0);
    return best ? best.href : "";
  }

  function isLikelyProblemUrl(url) {
    const path = url.pathname.toLowerCase();
    const host = url.hostname.toLowerCase();
    if (host === "leetcode.com") {
      return path.startsWith("/problems/") && path.split("/").filter(Boolean).length >= 2;
    }
    if (host === "www.hackerrank.com") {
      return /\/challenges\/[^/]+/.test(path);
    }
    if (host === "www.codechef.com") {
      return path.startsWith("/problems/") && path.split("/").filter(Boolean).length >= 2;
    }
    if (host === "codeforces.com") {
      return /\/(problemset\/problem|contest\/\d+\/problem)\/\d+\/[a-z0-9]+/.test(path);
    }
    if (host === "atcoder.jp") {
      return /\/contests\/[^/]+\/tasks\/[^/]+/.test(path);
    }
    return /problem|challenge|task/.test(path);
  }

  function leetCodeNextUrl() {
    const explicitSelectors = [
      'a[aria-label*="Next" i]',
      'button[aria-label*="Next" i]',
      'a[href^="/problems/"][rel="next"]'
    ];
    for (const selector of explicitSelectors) {
      const element = document.querySelector(selector);
      if (!element) {
        continue;
      }
      const href = element.getAttribute("href");
      if (href) {
        return new URL(href, location.origin).href;
      }
    }
    return genericNextUrl();
  }

  function hackerrankNextUrl() {
    return genericNextUrl();
  }

  function codeChefNextUrl() {
    return genericNextUrl();
  }

  function codeforcesNextUrl() {
    return genericNextUrl();
  }

  function atCoderNextUrl() {
    return genericNextUrl();
  }

  function genericLanguage() {
    return textFromSelectors([
      '[data-cy="lang-select"]',
      "button.rounded.items-center.whitespace-nowrap",
      ".language-select",
      "[aria-label*='Language']"
    ]) || "python3";
  }

  window.LEETBOT_PLATFORMS = [
    {
      id: "leetcode",
      label: "LeetCode",
      matches() {
        return location.hostname === "leetcode.com" && location.pathname.startsWith("/problems/");
      },
      title() {
        const text = textFromSelectors(["div.text-title-large a", "h1", "title"]);
        return text.replace(" - LeetCode", "").trim();
      },
      statement() {
        return textFromSelectors([
          '[data-track-load="description_content"]',
          '[data-cy="question-content"]',
          ".elfjS",
          "main"
        ]);
      },
      slug() {
        return location.pathname.split("/").filter(Boolean)[1] || "";
      },
      nextUrl() {
        return leetCodeNextUrl();
      },
      language() {
        return genericLanguage();
      }
    },
    {
      id: "hackerrank",
      label: "HackerRank",
      matches() {
        return location.hostname === "www.hackerrank.com" && /\/challenges\//.test(location.pathname);
      },
      title() {
        return textFromSelectors(["h1.challenge-title", "h1", "title"]).replace(" | HackerRank", "").trim();
      },
      statement() {
        return textFromSelectors([
          ".challenge-body-html",
          ".problem-statement",
          ".challenge_problem_statement"
        ]);
      },
      slug() {
        const parts = location.pathname.split("/").filter(Boolean);
        const challengeIndex = parts.indexOf("challenges");
        return challengeIndex >= 0 ? parts[challengeIndex + 1] || "" : "";
      },
      nextUrl() {
        return hackerrankNextUrl();
      },
      language() {
        return genericLanguage();
      }
    },
    {
      id: "codechef",
      label: "CodeChef",
      matches() {
        return location.hostname === "www.codechef.com" && location.pathname.startsWith("/problems/");
      },
      title() {
        return textFromSelectors(["h1", ".problem-title", "title"]).replace(" | CodeChef", "").trim();
      },
      statement() {
        return textFromSelectors([".problem-statement", "#problem-statement", "main"]);
      },
      slug() {
        return location.pathname.split("/").filter(Boolean)[1] || "";
      },
      nextUrl() {
        return codeChefNextUrl();
      },
      language() {
        return genericLanguage();
      }
    },
    {
      id: "codeforces",
      label: "Codeforces",
      matches() {
        return location.hostname === "codeforces.com" && /\/(problemset\/problem|contest\/\d+\/problem)\//.test(location.pathname);
      },
      title() {
        return textFromSelectors([".problem-statement .title", ".title", "title"]).replace(" - Codeforces", "").trim();
      },
      statement() {
        return textFromSelectors([".problem-statement", "#pageContent"]);
      },
      slug() {
        const parts = location.pathname.split("/").filter(Boolean);
        return parts.slice(-2).join("-");
      },
      nextUrl() {
        return codeforcesNextUrl();
      },
      language() {
        return genericLanguage();
      }
    },
    {
      id: "atcoder",
      label: "AtCoder",
      matches() {
        return location.hostname === "atcoder.jp" && /\/tasks\//.test(location.pathname);
      },
      title() {
        return textFromSelectors(["span.h2", ".h2", "h1", "title"]).replace(" - AtCoder", "").trim();
      },
      statement() {
        return textFromSelectors(["#task-statement", ".lang-en", "main"]);
      },
      slug() {
        const parts = location.pathname.split("/").filter(Boolean);
        return parts[parts.length - 1] || "";
      },
      nextUrl() {
        return atCoderNextUrl();
      },
      language() {
        return genericLanguage();
      }
    }
  ];

  window.LEETBOT_PLATFORM_HELPERS = {
    elementFromSelectors,
    genericLanguage,
    genericNextUrl
  };
})();
