document.addEventListener('DOMContentLoaded', function() {
  const didInput = document.getElementById('didInput');
  const loadDidBtn = document.getElementById('loadDid');
  const saveDidBtn = document.getElementById('saveDid');
  const didDisplay = document.getElementById('didDisplay');
  const dataObjectsInfo = document.getElementById('dataObjectsInfo');
  const scanPageBtn = document.getElementById('scanPage');
  const clearDataObjectsBtn = document.getElementById('clearDataObjects');

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

  // Scan the current page for DataObject elements
  function scanForDataObjects() {
    dataObjectsInfo.innerHTML = '<div>Scanning page for &lt;DataObject&gt; elements...</div>';
    dataObjectsInfo.style.display = 'block';
    
    chrome.tabs.query({active: true, currentWindow: true}, function(tabs) {
      chrome.tabs.sendMessage(
        tabs[0].id, 
        {action: 'scanForDataObjects'}, 
        function(response) {
          if (chrome.runtime.lastError) {
            dataObjectsInfo.innerHTML = '<div>Error scanning page. Please refresh and try again.</div>';
            return;
          }
          updateDataObjectsDisplay(response.dataObjects || []);
        }
      );
    });
  }

  // Update the display with found DataObject elements
  function updateDataObjectsDisplay(dataObjects) {
    if (!dataObjects || dataObjects.length === 0) {
      dataObjectsInfo.innerHTML = '<div>No &lt;DataObject&gt; elements found on this page.</div>';
      dataObjectsInfo.style.display = 'block';
      return;
    }
    
    let html = `<div>Found ${dataObjects.length} &lt;DataObject&gt; element${dataObjects.length === 1 ? '' : 's'}:</div>`;
    
    dataObjects.forEach((obj, index) => {
      const id = obj.id || `data-object-${index}`;
      let content = obj.innerHTML || '';
      
      // Truncate content if too long
      const maxLength = 100;
      const truncatedContent = content.length > maxLength 
        ? content.substring(0, maxLength) + '...' 
        : content;
      
      // Highlight found DIDs in content
      let displayContent = truncatedContent;
      if (obj.foundDIDs && obj.foundDIDs.length > 0) {
        // Create a unique marker to avoid replacing already highlighted content
        const marker = '___DID_MARKER___';
        let tempContent = displayContent;
        
        // First, replace all DIDs with markers
        obj.foundDIDs.forEach(did => {
          tempContent = tempContent.replace(new RegExp(did.replace(/[.*+?^${}()|[\]\\]/g, '\\$&'), 'g'), marker);
        });
        
        // Then replace markers with highlighted spans
        displayContent = tempContent.split(marker)
          .map((part, i) => {
            if (i === 0) return part;
            const did = obj.foundDIDs[i - 1];
            return `</span><span class="found-did" title="${did}">${did}</span><span>${part}`;
          })
          .join('');
      }
      
      html += `
        <div class="data-object">
          <div class="data-object-id">${id}</div>
          <div class="data-object-content" title="${content.replace(/"/g, '&quot;')}">
            ${displayContent}
          </div>
          ${obj.foundDIDs && obj.foundDIDs.length > 0 ? 
            `<div style="margin-top: 4px; color: #5f6368; font-size: 11px;">
              Contains ${obj.foundDIDs.length} DID${obj.foundDIDs.length === 1 ? '' : 's'}
            </div>` : ''
          }
        </div>
      `;
    });
    
    dataObjectsInfo.innerHTML = html;
    dataObjectsInfo.style.display = 'block';
  }

  // Load DataObjects when popup opens
  function loadDataObjects() {
    chrome.runtime.sendMessage(
      {action: 'getDataObjects'}, 
      function(response) {
        if (response && response.dataObjects) {
          updateDataObjectsDisplay(response.dataObjects);
        } else {
          // If no data, scan the page
          scanForDataObjects();
        }
      }
    );
  }

  // Initial load
  loadDataObjects();

  // Button event listeners
  scanPageBtn.addEventListener('click', scanForDataObjects);
  
  clearDataObjectsBtn.addEventListener('click', function() {
    chrome.runtime.sendMessage(
      {action: 'clearDataObjects'}, 
      function() {
        dataObjectsInfo.innerHTML = '<div>Cleared DataObject cache. Refresh the page and scan again.</div>';
        dataObjectsInfo.style.display = 'block';
      }
    );
  });

  // Listen for updates from the background script
  chrome.runtime.onMessage.addListener(function(request, sender, sendResponse) {
    if (request.action === 'dataObjectsUpdated') {
      // Refresh the display when new DataObjects are found
      loadDataObjects();
    }
  });
});
