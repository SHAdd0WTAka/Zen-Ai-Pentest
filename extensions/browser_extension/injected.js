/**
 * Zen-AI Pentest Companion - Injected Script
 *
 * Runs in the page context (has access to page's JavaScript)
 */

(function() {
    'use strict';

    // Zen-AI Scanner object accessible from page
    window.zenAiScanner = {
        version: '1.0.0',

        scan: function(payload) {
            console.log('[Zen-AI] Scanning:', payload);

            const results = {
                url: window.location.href,
                timestamp: Date.now(),
                findings: []
            };

            // Check for common libraries
            const libraries = this.detectLibraries();
            if (libraries.length > 0) {
                results.findings.push({
                    type: 'libraries',
                    severity: 'info',
                    data: libraries
                });
            }

            // Check for exposed API endpoints
            const endpoints = this.detectEndpoints();
            if (endpoints.length > 0) {
                results.findings.push({
                    type: 'endpoints',
                    severity: 'info',
                    data: endpoints
                });
            }

            // Check for potential XSS vectors
            const xssVectors = this.detectXSSVectors();
            if (xssVectors.length > 0) {
                results.findings.push({
                    type: 'xss_vectors',
                    severity: 'medium',
                    data: xssVectors
                });
            }

            return results;
        },

        detectLibraries: function() {
            const libs = [];

            // jQuery
            if (window.jQuery) {
                libs.push({ name: 'jQuery', version: window.jQuery.fn.jquery });
            }

            // React
            if (window.React) {
                libs.push({ name: 'React', version: window.React.version });
            }

            // Angular
            if (window.angular) {
                libs.push({ name: 'Angular', version: window.angular.version?.full });
            }

            // Vue
            if (window.Vue) {
                libs.push({ name: 'Vue', version: window.Vue.version });
            }

            // Bootstrap
            if (window.bootstrap) {
                libs.push({ name: 'Bootstrap', version: 'detected' });
            }

            // Check for common global objects
            const globals = Object.keys(window).filter(k => !['window', 'document', 'navigator'].includes(k));
            if (globals.includes('_')) libs.push({ name: 'Lodash/Underscore' });
            if (globals.includes('moment')) libs.push({ name: 'Moment.js' });
            if (globals.includes('axios')) libs.push({ name: 'Axios' });

            return libs;
        },

        detectEndpoints: function() {
            const endpoints = [];

            // Collect all URLs from scripts
            document.querySelectorAll('script[src]').forEach(script => {
                const src = script.getAttribute('src');
                if (src && (src.includes('/api/') || src.includes('/graphql'))) {
                    endpoints.push(src);
                }
            });

            // Check fetch/XHR overrides
            if (window._fetch || window._xhr) {
                endpoints.push('Fetch/XHR intercepted');
            }

            return [...new Set(endpoints)];
        },

        detectXSSVectors: function() {
            const vectors = [];

            // Check for innerHTML usage
            const html = document.documentElement.innerHTML;

            // Dangerous patterns
            const patterns = [
                { pattern: /eval\s*\(/gi, name: 'eval()' },
                { pattern: /document\.write\s*\(/gi, name: 'document.write()' },
                { pattern: /innerHTML\s*=/gi, name: 'innerHTML assignment' },
                { pattern: /setTimeout\s*\(\s*["']/gi, name: 'setTimeout with string' },
                { pattern: /setInterval\s*\(\s*["']/gi, name: 'setInterval with string' },
                { pattern: /javascript:/gi, name: 'javascript: URL' }
            ];

            patterns.forEach(({ pattern, name }) => {
                if (pattern.test(html)) {
                    vectors.push(name);
                }
            });

            return vectors;
        },

        extractTokens: function() {
            const tokens = [];
            const html = document.documentElement.innerHTML;

            // API keys
            const apiKeyPattern = /[a-zA-Z0-9_-]{32,64}/g;
            const matches = html.match(apiKeyPattern) || [];

            matches.forEach(match => {
                if (match.toLowerCase().includes('key') ||
                    match.toLowerCase().includes('token') ||
                    match.toLowerCase().includes('secret')) {
                    tokens.push({
                        type: 'potential_key',
                        value: match.substring(0, 10) + '...'
                    });
                }
            });

            return tokens;
        }
    };

    // Notify content script that injected script is ready
    window.postMessage({
        type: 'ZEN_AI_READY',
        version: '1.0.0'
    }, '*');

    console.log('[Zen-AI] Injected script ready');
})();
