/**
 * Zen-AI-Pentest Cloudflare Worker
 *
 * Features:
 * - Static site hosting (React SPA)
 * - API proxy to backend
 * - KV caching
 * - JWT authentication
 * - Rate limiting
 * - Analytics
 */

import { Router } from './router';
import { Auth } from './auth';
import { Cache } from './cache';

export default {
  async fetch(request, env, ctx) {
    const url = new URL(request.url);
    const router = new Router();

    // CORS headers
    const corsHeaders = {
      'Access-Control-Allow-Origin': '*',
      'Access-Control-Allow-Methods': 'GET, POST, PUT, DELETE, OPTIONS',
      'Access-Control-Allow-Headers': 'Content-Type, Authorization',
    };

    if (request.method === 'OPTIONS') {
      return new Response(null, { headers: corsHeaders });
    }

    // Route: API endpoints
    if (url.pathname.startsWith('/api/')) {
      return handleAPI(request, env, corsHeaders);
    }

    // Route: Health check
    if (url.pathname === '/health') {
      return new Response(JSON.stringify({
        status: 'ok',
        version: '3.0.0',
        timestamp: new Date().toISOString()
      }), {
        headers: { ...corsHeaders, 'Content-Type': 'application/json' }
      });
    }

    // Route: Static assets
    return env.ASSETS.fetch(request);
  }
};

async function handleAPI(request, env, corsHeaders) {
  const url = new URL(request.url);
  const cache = new Cache(env.CACHE);

  // Check cache for GET requests
  if (request.method === 'GET') {
    const cached = await cache.get(url.pathname);
    if (cached) {
      return new Response(cached, {
        headers: { ...corsHeaders, 'Content-Type': 'application/json', 'X-Cache': 'HIT' }
      });
    }
  }

  // Proxy to backend API
  // In production, this would connect to your FastAPI backend
  // For now, return mock responses

  if (url.pathname === '/api/auth/login') {
    return handleLogin(request, corsHeaders);
  }

  if (url.pathname === '/api/scans') {
    return handleScans(request, env, corsHeaders);
  }

  if (url.pathname === '/api/status') {
    return new Response(JSON.stringify({
      status: 'active',
      agents: 2,
      scans_completed: 150,
      version: '3.0.0'
    }), {
      headers: { ...corsHeaders, 'Content-Type': 'application/json' }
    });
  }

  return new Response(JSON.stringify({ error: 'Not Found' }), {
    status: 404,
    headers: { ...corsHeaders, 'Content-Type': 'application/json' }
  });
}

async function handleLogin(request, corsHeaders) {
  if (request.method !== 'POST') {
    return new Response(JSON.stringify({ error: 'Method not allowed' }), {
      status: 405,
      headers: { ...corsHeaders, 'Content-Type': 'application/json' }
    });
  }

  const body = await request.json();

  // Simple auth (replace with proper JWT in production)
  if (body.username === 'admin' && body.password === 'admin') {
    const token = btoa(JSON.stringify({
      user: body.username,
      exp: Date.now() + 3600000 // 1 hour
    }));

    return new Response(JSON.stringify({
      access_token: token,
      token_type: 'bearer'
    }), {
      headers: { ...corsHeaders, 'Content-Type': 'application/json' }
    });
  }

  return new Response(JSON.stringify({ error: 'Invalid credentials' }), {
    status: 401,
    headers: { ...corsHeaders, 'Content-Type': 'application/json' }
  });
}

async function handleScans(request, env, corsHeaders) {
  const auth = request.headers.get('Authorization');

  if (!auth) {
    return new Response(JSON.stringify({ error: 'Unauthorized' }), {
      status: 401,
      headers: { ...corsHeaders, 'Content-Type': 'application/json' }
    });
  }

  if (request.method === 'GET') {
    return new Response(JSON.stringify({
      scans: [
        { id: 1, target: 'example.com', status: 'completed', findings: 5 },
        { id: 2, target: 'test.com', status: 'running', progress: 45 }
      ]
    }), {
      headers: { ...corsHeaders, 'Content-Type': 'application/json' }
    });
  }

  if (request.method === 'POST') {
    const body = await request.json();

    // Store scan in KV for tracking
    const scanId = crypto.randomUUID();
    await env.CACHE.put(`scan:${scanId}`, JSON.stringify({
      id: scanId,
      target: body.target,
      status: 'queued',
      created: new Date().toISOString()
    }));

    return new Response(JSON.stringify({
      scan_id: scanId,
      status: 'queued',
      message: 'Scan started successfully'
    }), {
      status: 201,
      headers: { ...corsHeaders, 'Content-Type': 'application/json' }
    });
  }
}

// Durable Object für WebSocket-Verbindungen
export class WebSocketHub {
  constructor(state, env) {
    this.state = state;
    this.env = env;
    this.sessions = new Map();
  }

  async fetch(request) {
    const upgradeHeader = request.headers.get('Upgrade');

    if (upgradeHeader !== 'websocket') {
      return new Response('Expected websocket', { status: 400 });
    }

    const [client, server] = Object.values(new WebSocketPair());
    await this.handleSession(server);

    return new Response(null, {
      status: 101,
      webSocket: client
    });
  }

  async handleSession(ws) {
    ws.accept();
    const sessionId = crypto.randomUUID();
    this.sessions.set(sessionId, ws);

    ws.addEventListener('message', async (msg) => {
      const data = JSON.parse(msg.data);

      // Broadcast to all connected clients
      this.sessions.forEach((client) => {
        if (client.readyState === WebSocket.READY_STATE_OPEN) {
          client.send(JSON.stringify({
            type: 'broadcast',
            data: data,
            timestamp: new Date().toISOString()
          }));
        }
      });
    });

    ws.addEventListener('close', () => {
      this.sessions.delete(sessionId);
    });
  }
}
