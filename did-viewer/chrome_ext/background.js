// Background script for the DID Viewer extension
// Currently used for future extension functionality

// Listen for installation event
chrome.runtime.onInstalled.addListener(function() {
  console.log('DID Viewer extension installed');
});

// Listen for messages from content scripts
chrome.runtime.onMessage.addListener(function(request, sender, sendResponse) {
  // Handle any background messages here if needed
  if (request.action === 'ping') {
    sendResponse({status: 'pong'});
  }
  return true; // Required for async response
});
