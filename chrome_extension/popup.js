document.addEventListener('DOMContentLoaded', function() {
  const translateBtn = document.getElementById('translateBtn');
  const sourceLang = document.getElementById('sourceLang');
  const targetLang = document.getElementById('targetLang');
  const status = document.getElementById('status');

  // Load saved language preferences
  chrome.storage.sync.get(['sourceLanguage', 'targetLanguage'], function(result) {
    if (result.sourceLanguage) {
      sourceLang.value = result.sourceLanguage;
    }
    if (result.targetLanguage) {
      targetLang.value = result.targetLanguage;
    }
  });

  // Save language preferences when changed
  sourceLang.addEventListener('change', function() {
    chrome.storage.sync.set({ sourceLanguage: sourceLang.value });
  });

  targetLang.addEventListener('change', function() {
    chrome.storage.sync.set({ targetLanguage: targetLang.value });
  });

  translateBtn.addEventListener('click', function() {
    // Send message to content script
    chrome.tabs.query({active: true, currentWindow: true}, function(tabs) {
      chrome.tabs.sendMessage(tabs[0].id, {
        action: 'translate',
        sourceLang: sourceLang.value,
        targetLang: targetLang.value
      }, function(response) {
        if (response && response.status === 'success') {
          showStatus('Translation completed!', 'success');
        } else {
          showStatus('Translation failed. Please try again.', 'error');
        }
      });
    });
  });

  function showStatus(message, type) {
    status.textContent = message;
    status.className = `status ${type}`;
    status.style.display = 'block';
    setTimeout(() => {
      status.style.display = 'none';
    }, 3000);
  }
}); 