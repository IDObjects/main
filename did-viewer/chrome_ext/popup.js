document.addEventListener('DOMContentLoaded', function() {
  const didInput = document.getElementById('didInput');
  const loadDidBtn = document.getElementById('loadDid');
  const saveDidBtn = document.getElementById('saveDid');
  const didDisplay = document.getElementById('didDisplay');

  // Load saved DID from storage when popup opens
  chrome.storage.local.get(['savedDid'], function(result) {
    if (result.savedDid) {
      didInput.value = result.savedDid;
    }
  });

  // Load DID into the current page
  loadDidBtn.addEventListener('click', function() {
    const did = didInput.value.trim();
    if (did) {
      // Send message to content script to handle the DID
      chrome.tabs.query({active: true, currentWindow: true}, function(tabs) {
        chrome.tabs.sendMessage(tabs[0].id, {action: 'loadDid', did: did});
      });
      
      // Save the DID to storage
      chrome.storage.local.set({savedDid: did}, function() {
        console.log('DID saved to storage');
      });
      
      // Display the DID in the popup
      didDisplay.textContent = `Loaded DID: ${did}`;
      didDisplay.style.display = 'block';
    }
  });

  // Save DID to storage
  saveDidBtn.addEventListener('click', function() {
    const did = didInput.value.trim();
    if (did) {
      chrome.storage.local.set({savedDid: did}, function() {
        console.log('DID saved to storage');
        didDisplay.textContent = `Saved DID: ${did}`;
        didDisplay.style.display = 'block';
        
        // Hide the message after 2 seconds
        setTimeout(() => {
          didDisplay.style.display = 'none';
        }, 2000);
      });
    }
  });
});
