chrome.runtime.onInstalled.addListener(() => {
  if (chrome.sidePanel?.setPanelBehavior) {
    chrome.sidePanel.setPanelBehavior({ openPanelOnActionClick: true });
  }
});

chrome.action.onClicked.addListener(async (tab) => {
  if (!tab.windowId) return;

  if (chrome.sidePanel?.open) {
    await chrome.sidePanel.open({ windowId: tab.windowId });
  }
});
