// Configuration
const API_KEY = 'lXEzp6PHU4Y-sV8Y0U3dXqe1da7i6U-mMDjp2FcMOTg';
const API_URL = 'https://api.inten.to/ai/text/translate';

// Default provider configuration
const DEFAULT_PROVIDER = {
  provider: 'ai.text.translate.microsoft.translator_text_api.3-0',
  model: 'microsoft/translator-text-api-3.0'
};

// Listen for messages from popup
chrome.runtime.onMessage.addListener(function(request, sender, sendResponse) {
  if (request.action === 'translate') {
    console.log('Translation requested from', request.sourceLang, 'to', request.targetLang);
    translatePage(request.sourceLang, request.targetLang)
      .then(() => {
        console.log('Translation completed successfully');
        sendResponse({status: 'success'});
      })
      .catch(error => {
        console.error('Translation error:', error);
        sendResponse({status: 'error', message: error.message});
      });
    return true; // Required for async sendResponse
  }
});

async function translatePage(sourceLang, targetLang) {
  console.log('Starting page translation...');
  
  // Get all text nodes in the page
  const textNodes = getTextNodes(document.body);
  console.log(`Found ${textNodes.length} text nodes to translate`);
  
  // Group text nodes into chunks to minimize API calls
  const chunks = groupTextNodes(textNodes);
  console.log(`Grouped into ${chunks.length} chunks for translation`);
  
  // Translate each chunk
  for (let i = 0; i < chunks.length; i++) {
    const chunk = chunks[i];
    console.log(`Translating chunk ${i + 1}/${chunks.length} (${chunk.text.length} characters)`);
    
    try {
      const translatedText = await translateText(chunk.text, targetLang);
      console.log(`Chunk ${i + 1} translated successfully`);
      
      // Update the original text nodes with translated text
      chunk.nodes.forEach(node => {
        updateNodeWithTranslation(node, translatedText);
      });
    } catch (error) {
      console.error(`Error translating chunk ${i + 1}:`, error);
      // Continue with next chunk even if this one fails
      continue;
    }
  }
  
  console.log('Page translation completed');
}

function updateNodeWithTranslation(node, translatedText) {
  // Preserve original whitespace and formatting
  const originalText = node.nodeValue;
  const isStartOfLine = /^\s/.test(originalText);
  const isEndOfLine = /\s$/.test(originalText);
  
  // Add back original whitespace
  let finalText = translatedText;
  if (isStartOfLine) finalText = ' ' + finalText;
  if (isEndOfLine) finalText = finalText + ' ';
  
  // Update the node value
  node.nodeValue = finalText;
  
  // Handle overflow by adjusting parent element styles
  const parentElement = node.parentElement;
  if (parentElement) {
    // Store original styles if not already stored
    if (!parentElement.dataset.originalStyles) {
      const computedStyle = window.getComputedStyle(parentElement);
      parentElement.dataset.originalStyles = JSON.stringify({
        width: computedStyle.width,
        maxWidth: computedStyle.maxWidth,
        minWidth: computedStyle.minWidth,
        whiteSpace: computedStyle.whiteSpace,
        wordWrap: computedStyle.wordWrap,
        overflowWrap: computedStyle.overflowWrap,
        padding: computedStyle.padding,
        margin: computedStyle.margin,
        display: computedStyle.display,
        position: computedStyle.position
      });
    }
    
    // Apply styles to handle overflow
    const styles = {
      wordWrap: 'break-word',
      overflowWrap: 'break-word',
      whiteSpace: 'normal',
      maxWidth: '100%',
      boxSizing: 'border-box'
    };
    
    // Apply styles while preserving layout
    Object.assign(parentElement.style, styles);
    
    // Handle specific element types
    if (parentElement.tagName === 'TD' || parentElement.tagName === 'TH') {
      parentElement.style.width = 'auto';
      parentElement.style.minWidth = '0';
    }
    
    // Handle inline elements
    if (window.getComputedStyle(parentElement).display === 'inline') {
      parentElement.style.display = 'inline-block';
    }
    
    // Handle flex items
    if (parentElement.parentElement && 
        window.getComputedStyle(parentElement.parentElement).display === 'flex') {
      parentElement.style.flex = '1 1 auto';
    }
  }
}

function getTextNodes(node) {
  const textNodes = [];
  
  if (node.nodeType === Node.TEXT_NODE && node.nodeValue.trim()) {
    // Skip script and style tags
    const parent = node.parentElement;
    if (parent && 
        parent.tagName !== 'SCRIPT' && 
        parent.tagName !== 'STYLE' &&
        !parent.closest('script') &&
        !parent.closest('style') &&
        !parent.closest('noscript') &&
        !parent.closest('iframe')) {
      textNodes.push(node);
    }
  } else {
    const children = node.childNodes;
    for (let i = 0; i < children.length; i++) {
      textNodes.push(...getTextNodes(children[i]));
    }
  }
  
  return textNodes;
}

function groupTextNodes(textNodes) {
  const chunks = [];
  let currentChunk = { text: '', nodes: [] };
  
  textNodes.forEach(node => {
    const text = node.nodeValue.trim();
    if (text) {
      // Check if this node is part of a larger text block
      const parent = node.parentElement;
      const isBlockElement = parent && 
        ['P', 'DIV', 'H1', 'H2', 'H3', 'H4', 'H5', 'H6', 'LI', 'TD', 'TH'].includes(parent.tagName);
      
      // Start new chunk for block elements
      if (isBlockElement && currentChunk.text) {
        chunks.push(currentChunk);
        currentChunk = { text: '', nodes: [] };
      }
      
      currentChunk.text += text + ' ';
      currentChunk.nodes.push(node);
      
      // Create new chunk if current one is too long
      if (currentChunk.text.length > 1000) {
        chunks.push(currentChunk);
        currentChunk = { text: '', nodes: [] };
      }
    }
  });
  
  if (currentChunk.text) {
    chunks.push(currentChunk);
  }
  
  return chunks;
}

async function translateText(text, targetLang) {
    try {
        const response = await fetch('https://api.inten.to/ai/text/translate', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'apikey': API_KEY,
                'User-Agent': 'Intento.Integration.python/1.0'
            },
            body: JSON.stringify({
                context: {
                    text: text,
                    to: targetLang
                },
                service: {
                    provider: 'ai.text.translate.openai.gpt-3.5-turbo.translate',
                    model: 'openai/gpt-3.5-turbo'
                }
            })
        });

        if (!response.ok) {
            throw new Error(`Translation failed: ${response.statusText}`);
        }

        const data = await response.json();
        if (data.results && data.results.length > 0) {
            return data.results[0];
        } else {
            throw new Error('No translation results');
        }
    } catch (error) {
        console.error('Translation error:', error);
        throw error;
    }
} 