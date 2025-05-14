// Background script for the DID Viewer extension

// Store found DataObjects
let foundDataObjects = [];

// Listen for installation event
chrome.runtime.onInstalled.addListener(function() {
  console.log('DID Viewer extension installed');
  // Initialize storage
  chrome.storage.local.set({ dataObjects: [] });
});

// Listen for messages from content scripts and popup
chrome.runtime.onMessage.addListener(function(request, sender, sendResponse) {
  if (request.action === 'ping') {
    sendResponse({ status: 'pong' });
  } 
  else if (request.action === 'dataObjectsFound') {
    // Store the found DataObjects
    foundDataObjects = request.dataObjects || [];
    
    // Also store in chrome.storage for persistence
    chrome.storage.local.set({ dataObjects: foundDataObjects }, function() {
      console.log(`Found ${foundDataObjects.length} DataObject elements`);
      
      // Notify all tabs about the update
      chrome.tabs.query({}, function(tabs) {
        tabs.forEach(tab => {
          chrome.tabs.sendMessage(tab.id, {
            action: 'dataObjectsUpdated',
            count: foundDataObjects.length
          }).catch(err => {
            // Ignore errors from tabs that don't have our content script
          });
        });
      });
    });
    
    sendResponse({ status: 'success', count: foundDataObjects.length });
  }
  else if (request.action === 'getDataObjects') {
    // Return the stored DataObjects
    chrome.storage.local.get(['dataObjects'], function(result) {
      sendResponse({ dataObjects: result.dataObjects || [] });
    });
    return true; // Required for async response
  }
  else if (request.action === 'clearDataObjects') {
    // Clear stored DataObjects
    foundDataObjects = [];
    chrome.storage.local.set({ dataObjects: [] }, function() {
      sendResponse({ status: 'success' });
    });
    return true; // Required for async response
  }
  else if (request.action === 'scanForDataObjects') {
    // Request a scan from the content script
    chrome.tabs.query({active: true, currentWindow: true}, function(tabs) {
      if (tabs[0]) {
        chrome.tabs.sendMessage(tabs[0].id, 
          {action: 'scanForDataObjects'}, 
          function(response) {
            sendResponse(response);
          }
        );
      }
    });
    return true; // Required for async response
  }
  
  return true; // Required for async response
});

// Listen for tab updates to scan for DataObjects when a page loads
chrome.tabs.onUpdated.addListener(function(tabId, changeInfo, tab) {
  if (changeInfo.status === 'complete' && tab.active) {
    // Wait a bit for the page to fully load
    setTimeout(() => {
      chrome.tabs.sendMessage(tabId, {action: 'scanForDataObjects'});
    }, 1000);
  }
});

// Listen for tab activation to update the popup with current tab's DataObjects
chrome.tabs.onActivated.addListener(function(activeInfo) {
  // Get the current tab
  chrome.tabs.get(activeInfo.tabId, function(tab) {
    if (tab && tab.url && tab.url.startsWith('http')) {
      // Request a scan of the newly activated tab
      chrome.tabs.sendMessage(tab.id, {action: 'scanForDataObjects'});
    }
  });
});
