/**
 * JWT Authentication for Cloudflare Workers
 */

export class Auth {
  constructor(secret) {
    this.secret = secret;
  }

  async verify(token) {
    try {
      const [header, payload, signature] = token.split('.');

      // Decode payload
      const decoded = JSON.parse(atob(payload));

      // Check expiration
      if (decoded.exp && decoded.exp < Date.now() / 1000) {
        return null;
      }

      return decoded;
    } catch (e) {
      return null;
    }
  }

  async createToken(payload, expiresIn = 3600) {
    const header = btoa(JSON.stringify({ alg: 'HS256', typ: 'JWT' }));
    const body = btoa(JSON.stringify({
      ...payload,
      iat: Math.floor(Date.now() / 1000),
      exp: Math.floor(Date.now() / 1000) + expiresIn
    }));

    // Simple signature (use proper crypto in production)
    const signature = btoa(await this.sign(`${header}.${body}`));

    return `${header}.${body}.${signature}`;
  }

  async sign(data) {
    const encoder = new TextEncoder();
    const key = await crypto.subtle.importKey(
      'raw',
      encoder.encode(this.secret),
      { name: 'HMAC', hash: 'SHA-256' },
      false,
      ['sign']
    );

    const signature = await crypto.subtle.sign(
      'HMAC',
      key,
      encoder.encode(data)
    );

    return signature;
  }
}
