// Listen for messages from the popup
chrome.runtime.onMessage.addListener(function(request, sender, sendResponse) {
  if (request.action === 'loadDid') {
    // Create or update a div to display the DID
    let didDisplay = document.getElementById('didViewerDisplay');
    
    if (!didDisplay) {
      didDisplay = document.createElement('div');
      didDisplay.id = 'didViewerDisplay';
      didDisplay.style.position = 'fixed';
      didDisplay.style.bottom = '20px';
      didDisplay.style.right = '20px';
      didDisplay.style.backgroundColor = 'white';
      didDisplay.style.padding = '10px';
      didDisplay.style.border = '1px solid #ccc';
      didDisplay.style.borderRadius = '4px';
      didDisplay.style.boxShadow = '0 2px 10px rgba(0,0,0,0.1)';
      didDisplay.style.zIndex = '10000';
      didDisplay.style.maxWidth = '300px';
      didDisplay.style.wordBreak = 'break-all';
      didDisplay.style.fontFamily = 'monospace';
      
      // Add close button
      const closeBtn = document.createElement('button');
      closeBtn.textContent = '×';
      closeBtn.style.position = 'absolute';
      closeBtn.style.top = '0';
      closeBtn.style.right = '5px';
      closeBtn.style.background = 'none';
      closeBtn.style.border = 'none';
      closeBtn.style.fontSize = '16px';
      closeBtn.style.cursor = 'pointer';
      closeBtn.onclick = function() {
        didDisplay.style.display = 'none';
      };
      
      didDisplay.appendChild(closeBtn);
      document.body.appendChild(didDisplay);
    }
    
    // Display the DID
    const didText = document.createElement('div');
    didText.textContent = `DID: ${request.did}`;
    didText.style.marginTop = '15px';
    
    // Clear previous content except the close button
    while (didDisplay.childNodes.length > 1) {
      didDisplay.removeChild(didDisplay.lastChild);
    }
    
    didDisplay.appendChild(didText);
    didDisplay.style.display = 'block';
    
    // Auto-hide after 10 seconds
    setTimeout(() => {
      if (didDisplay) {
        didDisplay.style.display = 'none';
      }
    }, 10000);
  }
});
