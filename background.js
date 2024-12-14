// Runs in the background context
chrome.action.onClicked.addListener((tab) => {
    if (tab.url.includes('upwork.com')) {
        chrome.tabs.sendMessage(tab.id, { type: 'TOGGLE_SIDE_MENU' });
    }
});

chrome.runtime.onMessage.addListener((message, sender, sendResponse) => {
    if (message.type === 'JOB_DATA') {
        const { jobId, description, timestamp } = message.data;
        console.log('=== New Job Data Received ===');
        console.log('Timestamp:', new Date(timestamp).toISOString());
        console.log('Job ID:', jobId);
        console.log('Description Preview:', description.substring(0, 50));
        console.log('Full Description Length:', description.length);
        console.log('========================');

        // Forward the description to your local server
        fetch('http://localhost:3000/job', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                jobId,
                description,
                timestamp
            })
        })
            .then(response => response.json())
            .then(data => {
                console.log(`Server response for job ${jobId}:`, data);
                sendResponse({ success: true, receivedAt: Date.now() });
            })
            .catch(error => {
                console.error(`Error saving job ${jobId}:`, error);
                sendResponse({ success: false, error: error.message });
            });

        return true; // Keep the message channel open for async response
    }
});
