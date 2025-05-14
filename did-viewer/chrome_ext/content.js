// Listen for messages from the popup
chrome.runtime.onMessage.addListener(function(request, sender, sendResponse) {
  if (request.action === 'loadDid') {
    handleDID(request.did);
  } else if (request.action === 'scanForDataObjects') {
    const dataObjects = findDataObjects();
    sendResponse({dataObjects: dataObjects});
  }
  return true; // Required for async response
});

// Function to display DID in a floating panel
function handleDID(did) {
  // Create or update a div to display the DID
  let didDisplay = document.getElementById('didViewerDisplay');
  
  if (!didDisplay) {
    didDisplay = createDisplayElement();
  }
  
  // Display the DID
  const didText = document.createElement('div');
  didText.textContent = `DID: ${did}`;
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

// Function to create the display element
function createDisplayElement() {
  const didDisplay = document.createElement('div');
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
  return didDisplay;
}

// Function to find and process DataObject elements
function findDataObjects() {
  const dataObjects = [];
  const elements = document.getElementsByTagName('DataObject');
  
  for (let i = 0; i < elements.length; i++) {
    const element = elements[i];
    const dataObject = {
      id: element.id || `data-object-${i}`,
      tagName: element.tagName,
      innerHTML: element.innerHTML,
      attributes: {},
      rect: element.getBoundingClientRect()
    };
    
    // Get all attributes
    for (let j = 0; j < element.attributes.length; j++) {
      const attr = element.attributes[j];
      dataObject.attributes[attr.name] = attr.value;
    }
    
    // Check for common DID patterns in attributes or content
    const didPattern = /did:[a-z0-9]+(:[a-zA-Z0-9._-]+)+/g;
    
    // Check attributes for DIDs
    for (const [key, value] of Object.entries(dataObject.attributes)) {
      const matches = value.match(didPattern);
      if (matches) {
        dataObject.foundDIDs = dataObject.foundDIDs || [];
        dataObject.foundDIDs.push(...matches);
      }
    }
    
    // Check content for DIDs
    const contentMatches = element.textContent.match(didPattern);
    if (contentMatches) {
      dataObject.foundDIDs = dataObject.foundDIDs || [];
      dataObject.foundDIDs.push(...contentMatches);
    }
    
    dataObjects.push(dataObject);
  }
  
  return dataObjects;
}

// Function to calculate SHA-256 hash of content
async function calculateHash(content) {
  const msgBuffer = new TextEncoder().encode(content);
  const hashBuffer = await crypto.subtle.digest('SHA-256', msgBuffer);
  const hashArray = Array.from(new Uint8Array(hashBuffer));
  return hashArray.map(b => b.toString(16).padStart(2, '0')).join('');
}

// Function to verify content hash against server
async function verifyContentHash(id, content) {
  try {
    const response = await fetch(`https://example.com/${encodeURIComponent(id)}/hash`);
    if (!response.ok) {
      throw new Error(`Failed to fetch hash: ${response.status} ${response.statusText}`);
    }
    
    const serverHash = (await response.text()).trim();
    const contentHash = await calculateHash(content);
    
    return {
      isValid: serverHash === contentHash,
      serverHash,
      contentHash
    };
  } catch (error) {
    console.error('Hash verification failed:', error);
    return {
      isValid: false,
      error: error.message
    };
  }
}

// Function to import RSA private key from JWK format
async function importPrivateKey(jwkKey) {
  try {
    return await window.crypto.subtle.importKey(
      'jwk',
      jwkKey,
      {
        name: 'RSA-OAEP',
        hash: { name: 'SHA-256' },
      },
      true,
      ['decrypt']
    );
  } catch (error) {
    console.error('Error importing private key:', error);
    throw new Error('Failed to import private key');
  }
}

// Function to decrypt content using AES key
async function decryptContent(encryptedContent, iv, aesKey) {
  try {
    // Import the AES key
    const importedKey = await window.crypto.subtle.importKey(
      'raw',
      aesKey,
      { name: 'AES-CBC' },
      false,
      ['decrypt']
    );

    // Decrypt the content
    const decrypted = await window.crypto.subtle.decrypt(
      {
        name: 'AES-CBC',
        iv: iv,
      },
      importedKey,
      encryptedContent
    );

    // Handle PKCS7 padding
    const padding = decrypted[decrypted.byteLength - 1];
    const unpadded = new Uint8Array(decrypted.slice(0, decrypted.byteLength - padding));
    
    return new TextDecoder().decode(unpadded);
  } catch (error) {
    console.error('Decryption error:', error);
    throw new Error('Failed to decrypt content');
  }
}

// Function to decrypt the encrypted AES key using RSA private key
async function decryptAesKey(encryptedKey, privateKey) {
  try {
    // Decrypt the AES key using RSA-OAEP
    const decryptedKey = await window.crypto.subtle.decrypt(
      {
        name: 'RSA-OAEP',
      },
      privateKey,
      encryptedKey
    );
    
    return decryptedKey;
  } catch (error) {
    console.error('Key decryption error:', error);
    throw new Error('Failed to decrypt AES key');
  }
}

// Function to fetch and process encrypted content
async function fetchAndProcessEncryptedData(element) {
  const id = element.getAttribute('id');
  if (!id) return null;

  try {
    // Fetch the encrypted data
    const response = await fetch(`https://example.com/${encodeURIComponent(id)}`);
    if (!response.ok) {
      throw new Error(`HTTP error! status: ${response.status}`);
    }
    
    const data = await response.json();
    
    // Check if the content is encrypted
    if (!data.encrypted_content || !data.encrypted_key || !data.iv) {
      throw new Error('Invalid encrypted data format');
    }
    
    // Get the private key from extension storage (you'll need to implement this)
    const result = await chrome.storage.local.get(['privateKeyJwk']);
    if (!result.privateKeyJwk) {
      throw new Error('No private key found in storage');
    }
    
    // Import the private key
    const privateKey = await importPrivateKey(result.privateKeyJwk);
    
    // Convert base64 strings to ArrayBuffer
    const encryptedKey = Uint8Array.from(atob(data.encrypted_key), c => c.charCodeAt(0)).buffer;
    const iv = Uint8Array.from(atob(data.iv), c => c.charCodeAt(0));
    const encryptedContent = Uint8Array.from(atob(data.encrypted_content), c => c.charCodeAt(0)).buffer;
    
    // Decrypt the AES key
    const aesKey = await decryptAesKey(encryptedKey, privateKey);
    
    // Decrypt the content
    const decryptedContent = await decryptContent(encryptedContent, iv, aesKey);
    
    return JSON.parse(decryptedContent);
    
  } catch (error) {
    console.error('Error processing encrypted data:', error);
    throw error;
  }
}

// Function to fetch and display content for a DATAOBJECT
async function fetchAndDisplayDataObject(element) {
  const id = element.getAttribute('id');
  if (!id) return;

  // Create a container div for the content
  const container = document.createElement('div');
  container.className = 'dataobject-content';
  container.style.border = '1px solid #e0e0e0';
  container.style.padding = '10px';
  container.style.margin = '5px 0';
  container.style.borderRadius = '4px';
  container.style.backgroundColor = '#f9f9f9';
  
  // Add loading state
  container.innerHTML = `
    <div style="display: flex; align-items: center; gap: 8px;">
      <span class="loader"></span>
      <span>Loading content for ${id}...</span>
    </div>
    <div class="hash-verification" style="margin-top: 8px; font-size: 12px; color: #666;">
      Verifying content integrity...
    </div>
  `;
  
  // Insert the container after the DATAOBJECT
  element.parentNode.insertBefore(container, element.nextSibling);
  
  try {
    // Try to fetch and decrypt the content
    const content = await fetchAndProcessEncryptedData(element);
    
    // Display the decrypted content
    container.innerHTML = `
      <div style="font-weight: bold; margin-bottom: 8px;">Decrypted content for ${id}:</div>
      <div style="white-space: pre-wrap; font-family: monospace; background: white; padding: 8px; border: 1px solid #eee; border-radius: 3px; max-height: 200px; overflow-y: auto;">
        ${JSON.stringify(content, null, 2)}
      </div>
      <div style="color: #2e7d32; margin-top: 8px; font-size: 12px;">
        ✓ Content successfully decrypted
      </div>
    `;
    
  } catch (error) {
    console.error('Error processing data object:', error);
    container.innerHTML = `
      <div style="color: #d32f2f;">
        Error decrypting content for ${id}: ${error.message}
      </div>
    `;
  }
}

// Scan for DataObject elements when the page loads
document.addEventListener('DOMContentLoaded', function() {
  // Initial scan
  const dataObjects = findDataObjects();
  
  // Notify the background script about found DataObjects
  if (dataObjects.length > 0) {
    chrome.runtime.sendMessage({
      action: 'dataObjectsFound',
      count: dataObjects.length,
      dataObjects: dataObjects
    });
  }
  
  // Fetch and display content for each DataObject
  dataObjects.forEach(dataObject => {
    const element = document.getElementById(dataObject.id);
    if (element) {
      fetchAndDisplayDataObject(element);
    }
  });
});

// Also scan for dynamically added DataObject elements
const observer = new MutationObserver(function(mutations) {
  for (const mutation of mutations) {
    for (const node of mutation.addedNodes) {
      if (node.nodeType === 1) { // Element node
        if (node.tagName === 'DATAOBJECT') {
          const dataObjects = findDataObjects();
          if (dataObjects.length > 0) {
            chrome.runtime.sendMessage({
              action: 'dataObjectsFound',
              count: dataObjects.length,
              dataObjects: dataObjects
            });
          }
          fetchAndDisplayDataObject(node);
        } else if (node.querySelectorAll) {
          const dataObjects = node.querySelectorAll('DataObject');
          if (dataObjects.length > 0) {
            chrome.runtime.sendMessage({
              action: 'dataObjectsFound',
              count: dataObjects.length,
              dataObjects: Array.from(dataObjects).map(el => ({
                id: el.id || '',
                tagName: el.tagName,
                innerHTML: el.innerHTML,
                attributes: Array.from(el.attributes).reduce((acc, attr) => {
                  acc[attr.name] = attr.value;
                  return acc;
                }, {})
              }))
            });
            dataObjects.forEach(dataObject => {
              fetchAndDisplayDataObject(dataObject);
            });
          }
        }
      }
    }
  }
});

// Start observing the document with the configured parameters
observer.observe(document.body, {
  childList: true,
  subtree: true
});
