function extractPostingText() {
  const selectors = [
    "[data-test-job-description]",
    ".jobs-description-content__text",
    ".description",
    "main"
  ];

  for (const selector of selectors) {
    const node = document.querySelector(selector);
    if (node && node.textContent && node.textContent.trim().length > 120) {
      return node.textContent.trim();
    }
  }

  return (document.body?.innerText || "").trim();
}

chrome.runtime.onMessage.addListener((message, _sender, sendResponse) => {
  if (message?.type === "hound-extract-posting") {
    sendResponse({ postingText: extractPostingText() });
  }
});
