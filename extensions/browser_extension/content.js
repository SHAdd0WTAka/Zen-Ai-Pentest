/**
 * Zen-AI Pentest Companion - Content Script
 *
 * Runs in the context of web pages
 */

// Inject script into page context
function injectScript() {
    const script = document.createElement('script');
    script.src = chrome.runtime.getURL('injected.js');
    script.onload = () => script.remove();
    (document.head || document.documentElement).appendChild(script);
}

// Listen for messages from injected script
window.addEventListener('message', (event) => {
    if (event.source !== window) return;
    if (event.data.type && event.data.type.startsWith('ZEN_AI_')) {
        // Forward to background script
        chrome.runtime.sendMessage(event.data);
    }
});

// Listen for messages from background/popup
chrome.runtime.onMessage.addListener((request, sender, sendResponse) => {
    if (request.type === 'GET_PAGE_INFO') {
        sendResponse({
            url: window.location.href,
            title: document.title,
            domain: window.location.hostname,
            cookies: document.cookie,
            forms: Array.from(document.forms).map(f => ({
                action: f.action,
                method: f.method,
                inputs: Array.from(f.elements).map(e => ({
                    type: e.type,
                    name: e.name,
                    id: e.id
                }))
            })),
            scripts: Array.from(document.scripts).map(s => s.src).filter(Boolean),
            meta: Array.from(document.getElementsByTagName('meta')).map(m => ({
                name: m.getAttribute('name'),
                content: m.getAttribute('content')
            }))
        });
    }
    return true;
});

// Initialize
injectScript();
console.log('[Zen-AI] Content script loaded');
