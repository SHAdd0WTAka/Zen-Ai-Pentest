/**
 * Zen-AI Pentest Companion - Popup Script
 */

// DOM Elements
const statusIndicator = document.getElementById('statusIndicator');
const statusText = document.getElementById('statusText');
const btnScanPage = document.getElementById('btnScanPage');
const btnIntercept = document.getElementById('btnIntercept');
const btnExtractCreds = document.getElementById('btnExtractCreds');
const btnCaptureDOM = document.getElementById('btnCaptureDOM');
const btnSaveConfig = document.getElementById('btnSaveConfig');
const btnViewRequests = document.getElementById('btnViewRequests');
const btnClearRequests = document.getElementById('btnClearRequests');
const apiUrlInput = document.getElementById('apiUrl');
const apiKeyInput = document.getElementById('apiKey');
const requestCountEl = document.getElementById('requestCount');
const resultsSection = document.getElementById('resultsSection');
const resultsContent = document.getElementById('resultsContent');

// State
let isIntercepting = false;
let interceptedCount = 0;

// Initialize
async function init() {
    await loadSettings();
    await checkConnection();
    await updateRequestCount();
    setupEventListeners();
}

// Load saved settings
async function loadSettings() {
    const settings = await chrome.storage.local.get(['apiUrl', 'apiKey', 'isIntercepting']);
    if (settings.apiUrl) apiUrlInput.value = settings.apiUrl;
    if (settings.apiKey) apiKeyInput.value = settings.apiKey;
    isIntercepting = settings.isIntercepting || false;
    updateInterceptButton();
}

// Save settings
async function saveSettings() {
    await chrome.storage.local.set({
        apiUrl: apiUrlInput.value,
        apiKey: apiKeyInput.value
    });
    showNotification('Settings saved!');
}

// Check API connection
async function checkConnection() {
    try {
        const settings = await chrome.storage.local.get('apiUrl');
        const apiUrl = settings.apiUrl || 'http://localhost:8000';

        const response = await fetch(`${apiUrl}/health`, {
            method: 'GET',
            signal: AbortSignal.timeout(3000)
        });

        if (response.ok) {
            setStatus('connected', 'Connected');
        } else {
            setStatus('error', 'API Error');
        }
    } catch (e) {
        setStatus('error', 'Disconnected');
    }
}

// Set status indicator
function setStatus(status, text) {
    statusIndicator.className = 'status-indicator' + (status ? ` ${status}` : '');
    statusText.textContent = text;
}

// Update intercept button state
function updateInterceptButton() {
    btnIntercept.innerHTML = `<span class="icon">${isIntercepting ? '⏹️' : '📡'}</span> ${isIntercepting ? 'Stop' : 'Intercept'}`;
    btnIntercept.className = `btn ${isIntercepting ? 'btn-danger' : 'btn-secondary'}`;
}

// Update request count
async function updateRequestCount() {
    const tabs = await chrome.tabs.query({ active: true, currentWindow: true });
    if (!tabs[0]) return;

    chrome.runtime.sendMessage(
        { type: 'GET_INTERCEPTED_REQUESTS', tabId: tabs[0].id },
        (response) => {
            interceptedCount = response?.requests?.length || 0;
            requestCountEl.textContent = interceptedCount;
        }
    );
}

// Show results
function showResults(results) {
    resultsSection.style.display = 'block';
    resultsContent.innerHTML = '';

    if (typeof results === 'object') {
        const pre = document.createElement('pre');
        pre.textContent = JSON.stringify(results, null, 2);
        pre.style.color = '#00d4ff';
        pre.style.fontSize = '10px';
        pre.style.whiteSpace = 'pre-wrap';
        pre.style.wordBreak = 'break-word';
        resultsContent.appendChild(pre);
    } else {
        resultsContent.textContent = results;
    }
}

// Show notification
function showNotification(message) {
    const notification = document.createElement('div');
    notification.style.cssText = `
        position: fixed;
        top: 10px;
        left: 50%;
        transform: translateX(-50%);
        background: #00d4ff;
        color: #000;
        padding: 8px 16px;
        border-radius: 4px;
        font-size: 12px;
        font-weight: 600;
        z-index: 10000;
        animation: fadeInOut 2s ease;
    `;
    notification.textContent = message;
    document.body.appendChild(notification);

    setTimeout(() => notification.remove(), 2000);
}

// Setup event listeners
function setupEventListeners() {
    btnSaveConfig.addEventListener('click', saveSettings);

    btnScanPage.addEventListener('click', async () => {
        const tabs = await chrome.tabs.query({ active: true, currentWindow: true });
        if (!tabs[0]) return;

        chrome.runtime.sendMessage({
            type: 'START_SCAN',
            payload: { url: tabs[0].url, type: 'quick' }
        });

        showNotification('Scan started!');
    });

    btnIntercept.addEventListener('click', async () => {
        isIntercepting = !isIntercepting;
        await chrome.storage.local.set({ isIntercepting });
        updateInterceptButton();

        chrome.runtime.sendMessage({
            type: 'INTERCEPT_REQUESTS',
            enable: isIntercepting
        });

        showNotification(isIntercepting ? 'Intercepting started!' : 'Intercepting stopped!');
    });

    btnExtractCreds.addEventListener('click', async () => {
        const tabs = await chrome.tabs.query({ active: true, currentWindow: true });
        if (!tabs[0]) return;

        chrome.runtime.sendMessage({
            type: 'EXTRACT_CREDS',
            tabId: tabs[0].id
        }, (response) => {
            showResults(response?.credentials || 'No credentials found');
        });
    });

    btnCaptureDOM.addEventListener('click', async () => {
        const tabs = await chrome.tabs.query({ active: true, currentWindow: true });
        if (!tabs[0]) return;

        chrome.runtime.sendMessage({
            type: 'CAPTURE_DOM',
            tabId: tabs[0].id
        }, (response) => {
            showResults(response?.dom || 'Failed to capture DOM');
        });
    });

    btnViewRequests.addEventListener('click', async () => {
        const tabs = await chrome.tabs.query({ active: true, currentWindow: true });
        if (!tabs[0]) return;

        chrome.runtime.sendMessage({
            type: 'GET_INTERCEPTED_REQUESTS',
            tabId: tabs[0].id
        }, (response) => {
            showResults(response?.requests || []);
        });
    });

    btnClearRequests.addEventListener('click', async () => {
        const tabs = await chrome.tabs.query({ active: true, currentWindow: true });
        if (!tabs[0]) return;

        chrome.runtime.sendMessage({
            type: 'CLEAR_REQUESTS',
            tabId: tabs[0].id
        });

        interceptedCount = 0;
        requestCountEl.textContent = '0';
        showNotification('Requests cleared!');
    });

    document.getElementById('linkOpenDashboard').addEventListener('click', (e) => {
        e.preventDefault();
        chrome.storage.local.get('apiUrl', (settings) => {
            const url = settings.apiUrl || 'http://localhost:8000';
            chrome.tabs.create({ url });
        });
    });
}

// Initialize when DOM is ready
document.addEventListener('DOMContentLoaded', init);
