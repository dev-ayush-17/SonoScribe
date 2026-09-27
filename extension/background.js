// SonoScribe Extension Background Service Worker
chrome.runtime.onInstalled.addListener(() => {
  console.log('SonoScribe Chrome Extension Installed');
});

// Listener for capture start/stop requests from popup
chrome.runtime.onMessage.addListener((request, sender, sendResponse) => {
  if (request.type === 'GET_ACTIVE_TAB_STREAM_ID') {
    chrome.tabs.query({ active: true, currentWindow: true }, (tabs) => {
      if (!tabs || tabs.length === 0) {
        sendResponse({ error: 'No active tab found' });
        return;
      }
      const activeTab = tabs[0];
      chrome.tabCapture.getMediaStreamId({ targetTabId: activeTab.id }, (streamId) => {
        if (chrome.runtime.lastError) {
          sendResponse({ error: chrome.runtime.lastError.message });
        } else {
          sendResponse({ streamId, tabTitle: activeTab.title, tabId: activeTab.id });
        }
      });
    });
    return true; // Asynchronous response
  }
});
