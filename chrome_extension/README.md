# AI Job Market Chrome Extension

A Chrome extension for collecting job postings data from various job boards.

## Features

- Automatic job posting detection
- Data extraction from job descriptions
- Integration with backend analyzer
- Easy-to-use popup interface

## Installation

1. Clone the repository
2. Open Chrome and navigate to `chrome://extensions/`
3. Enable "Developer mode"
4. Click "Load unpacked" and select the `chrome_extension` directory

## Structure

```
chrome_extension/
├── manifest.json        # Extension configuration
├── background.js       # Background service worker
├── content.js         # Content script for job page parsing
├── popup.html        # Extension popup interface
├── popup.js         # Popup functionality
└── server.js       # Local server for data handling
```

## Development

1. Install dependencies:
```bash
npm install
```

2. Start the local server:
```bash
node server.js
```

3. Make changes to the extension files
4. Reload the extension in Chrome to see changes

## Contributing

1. Fork the repository
2. Create your feature branch
3. Commit your changes
4. Push to the branch
5. Open a Pull Request 