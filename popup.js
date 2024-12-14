// DOM Elements
const logsContainer = document.getElementById('logs');
const startButton = document.getElementById('startScraping');
const clearButton = document.getElementById('clearLogs');

// Load existing logs when popup opens
document.addEventListener('DOMContentLoaded', () => {
    chrome.storage.local.get(['scraper_logs'], (result) => {
        const logs = result.scraper_logs || [];
        logs.forEach(log => addLogToUI(log));
    });
    
    // Check if we're on Upwork
    chrome.tabs.query({ active: true, currentWindow: true }, (tabs) => {
        const currentTab = tabs[0];
        startButton.disabled = !currentTab.url.includes('upwork.com');
    });
});

// Add log entry to UI
function addLogToUI(log) {
    const logEntry = document.createElement('div');
    logEntry.className = `log-entry log-${log.type}`;
    
    const timestamp = new Date(log.timestamp).toLocaleTimeString();
    logEntry.textContent = `[${timestamp}] ${log.message}`;
    
    logsContainer.appendChild(logEntry);
    logsContainer.scrollTop = logsContainer.scrollHeight;
}

// Save log to storage
function saveLog(type, message) {
    const log = {
        type,
        message,
        timestamp: new Date().toISOString()
    };
    
    chrome.storage.local.get(['scraper_logs'], (result) => {
        const logs = result.scraper_logs || [];
        logs.push(log);
        
        // Keep only last 100 logs
        if (logs.length > 100) {
            logs.shift();
        }
        
        chrome.storage.local.set({ scraper_logs: logs });
        addLogToUI(log);
    });
}

// Listen for messages from background script
chrome.runtime.onMessage.addListener((message, sender, sendResponse) => {
    switch (message.type) {
        case 'progress':
            saveLog('info', `Processed ${message.current} of ${message.total} jobs (${Math.round((message.current / message.total) * 100)}%)`);
            break;
            
        case 'complete':
            saveLog('success', `Found ${message.jobs.length} AI-related jobs! Downloading results...`);
            break;
            
        case 'no_jobs_found':
            saveLog('info', 'No AI-related jobs found in the current listings.');
            break;
            
        case 'error':
            saveLog('error', `Error: ${message.message}`);
            break;
    }
});

// Start scraping button click handler
startButton.addEventListener('click', () => {
    chrome.tabs.query({ active: true, currentWindow: true }, (tabs) => {
        const currentTab = tabs[0];
        if (currentTab.url.includes('upwork.com')) {
            saveLog('info', 'Starting job scan...');
            startButton.disabled = true;
            
            chrome.tabs.sendMessage(currentTab.id, { action: 'startScraping' });
            
            // Re-enable button after 2 seconds
            setTimeout(() => {
                startButton.disabled = false;
            }, 2000);
        }
    });
});

// Clear logs button click handler
clearButton.addEventListener('click', () => {
    chrome.storage.local.set({ scraper_logs: [] });
    logsContainer.innerHTML = '';
    saveLog('info', 'Logs cleared');
}); 