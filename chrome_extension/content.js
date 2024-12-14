let isScrapingActive = false;

async function scrapeJobs() {
    while (isScrapingActive) {
        // Query all job tiles
        const jobTiles = document.querySelectorAll('article.job-tile.cursor-pointer');
        let processedCount = 0;

        for (const jobTile of jobTiles) {
            if (!isScrapingActive) return;

            const jobId = jobTile.getAttribute('data-ev-job-uid');
            if (!jobId) continue;

            // Scroll the job tile into view
            jobTile.scrollIntoView({ behavior: 'smooth', block: 'center' });
            await wait(500);

            // Click the job to open description
            jobTile.click();
            console.log('Clicked job with ID:', jobId);

            // Wait for the job description to load
            await wait(2000);

            // Query the description element fresh each time
            const descriptionElement = document.querySelector('.air3-slider-content .air3-card-section p.text-body-sm');
            console.log({ descriptionElement })
            if (descriptionElement) {
                const description = descriptionElement.textContent || '';
                console.log(`About to send job ${jobId} to background. First 50 chars:`, description.substring(0, 50));

                try {
                    const response = await sendMessageToBackground({
                        type: 'JOB_DATA',
                        data: {
                            jobId,
                            description,
                            timestamp: Date.now()
                        }
                    });
                    console.log(`Background script response for job ${jobId}:`, response);
                } catch (error) {
                    console.error(`Failed to send job ${jobId} to background:`, error);
                }
            } else {
                console.warn(`No description element found for job ${jobId}`);
            }

            // Close the popup
            const closeButton = document.querySelector('button[data-test="slider-close-desktop"]');
            if (closeButton) {
                closeButton.click();
                await wait(500);
            }

            processedCount++;
            
            // Scroll down to reveal more jobs
            window.scrollBy({ top: 200, behavior: 'smooth' });
            await wait(500);
        }

        console.log(`Processed ${processedCount} jobs on current page`);
        
        // After processing all jobs on the page, try to go to next page
        const nextButton = document.querySelector('button[data-ev-label="pagination_next_page"]:not([disabled])');
        console.log('Looking for next page button...', { nextButtonFound: !!nextButton });
        
        if (nextButton) {
            console.log('Found next page button, attempting to click...');
            // Ensure the button is visible
            nextButton.scrollIntoView({ behavior: 'smooth', block: 'center' });
            await wait(1000);
            
            try {
                nextButton.click();
                console.log('Successfully clicked next page button');
                await wait(3000); // Wait for the new page to load
                window.scrollTo({ top: 0, behavior: 'smooth' });
                await wait(1000);
            } catch (error) {
                console.error('Error clicking next page button:', error);
                break;
            }
        } else {
            console.log('No more pages available - next button not found');
            break;
        }
    }
}

function createSideMenu() {
    const sideMenu = document.createElement('div');
    sideMenu.id = 'ai-scraper-side-menu';
    sideMenu.innerHTML = `
        <div class="side-menu-content">
            <div class="header">
                <h2>Job Scraper</h2>
                <div class="button-group">
                    <button id="startScrapingSide" class="start-button">Start</button>
                    <button id="stopScrapingSide" class="stop-button" disabled>Stop</button>
                </div>
            </div>
            <div id="logsSide" class="logs"></div>
        </div>
    `;

    document.body.appendChild(sideMenu);
    injectSideMenuStyles();
    initializeSideMenu();
}

function initializeSideMenu() {
    const startButton = document.getElementById('startScrapingSide');
    const stopButton = document.getElementById('stopScrapingSide');
    const logsContainer = document.getElementById('logsSide');

    function addLog(message) {
        const logEntry = document.createElement('div');
        logEntry.className = 'log-entry';
        logEntry.textContent = `[${new Date().toLocaleTimeString()}] ${message}`;
        logsContainer.appendChild(logEntry);
        logsContainer.scrollTop = logsContainer.scrollHeight;
    }

    startButton.addEventListener('click', () => {
        isScrapingActive = true;
        startButton.disabled = true;
        stopButton.disabled = false;
        addLog('Started scraping');
        scrapeJobs().catch(error => {
            console.error('Scraping error:', error);
            addLog(`Error: ${error.message}`);
        });
    });

    stopButton.addEventListener('click', () => {
        isScrapingActive = false;
        startButton.disabled = false;
        stopButton.disabled = true;
        addLog('Stopped scraping');
    });
}

function injectSideMenuStyles() {
    const styles = document.createElement('style');
    styles.textContent = `
        #ai-scraper-side-menu {
            position: fixed;
            top: 0;
            right: -400px;
            width: 400px;
            height: 100vh;
            background: white;
            box-shadow: -2px 0 5px rgba(0,0,0,0.2);
            z-index: 10000;
            transition: right 0.3s ease;
            font-family: Arial, sans-serif;
        }
        #ai-scraper-side-menu.open {
            right: 0;
        }
        .side-menu-content {
            padding: 20px;
        }
        .header {
            display: flex;
            flex-direction: column;
            gap: 10px;
            margin-bottom: 15px;
            padding-bottom: 10px;
            border-bottom: 1px solid #eee;
        }
        .button-group {
            display: flex;
            gap: 10px;
        }
        .start-button, .stop-button {
            flex: 1;
            padding: 8px 15px;
            border: none;
            border-radius: 4px;
            cursor: pointer;
            color: white;
        }
        .start-button {
            background-color: #2196F3;
        }
        .stop-button {
            background-color: #f44336;
        }
        .start-button:disabled, .stop-button:disabled {
            background-color: #ccc;
            cursor: not-allowed;
        }
        .logs {
            height: calc(100vh - 200px);
            overflow-y: auto;
            background-color: #f5f5f5;
            padding: 10px;
            border-radius: 4px;
            font-family: monospace;
        }
        .log-entry {
            margin: 5px 0;
            padding: 5px;
            border-radius: 3px;
            white-space: pre-wrap;
            word-break: break-word;
        }
    `;
    document.head.appendChild(styles);
}

// Listen for toggle message from background
chrome.runtime.onMessage.addListener((message, sender, sendResponse) => {
    if (message.type === 'TOGGLE_SIDE_MENU') {
        let sideMenu = document.getElementById('ai-scraper-side-menu');
        if (sideMenu) {
            sideMenu.classList.toggle('open');
        } else {
            createSideMenu();
            sideMenu = document.getElementById('ai-scraper-side-menu');
            sideMenu.classList.add('open');
        }
        sendResponse({ success: true });
    }
});

// Utility functions
function wait(ms) {
    return new Promise(resolve => setTimeout(resolve, ms));
}

function sendMessageToBackground(msg) {
    return new Promise((resolve, reject) => {
        chrome.runtime.sendMessage(msg, (response) => {
            if (chrome.runtime.lastError) {
                return reject(chrome.runtime.lastError);
            }
            resolve(response);
        });
    });
}

// Initialize side menu on load
createSideMenu();
