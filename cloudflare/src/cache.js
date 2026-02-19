/**
 * KV Cache wrapper for Cloudflare Workers
 */

export class Cache {
  constructor(kv) {
    this.kv = kv;
    this.defaultTTL = 300; // 5 minutes
  }

  async get(key) {
    try {
      return await this.kv.get(key);
    } catch (e) {
      console.error('Cache get error:', e);
      return null;
    }
  }

  async set(key, value, ttl = this.defaultTTL) {
    try {
      await this.kv.put(key, value, { expirationTtl: ttl });
      return true;
    } catch (e) {
      console.error('Cache set error:', e);
      return false;
    }
  }

  async delete(key) {
    try {
      await this.kv.delete(key);
      return true;
    } catch (e) {
      console.error('Cache delete error:', e);
      return false;
    }
  }

  // Cache with automatic JSON serialization
  async getJSON(key) {
    const data = await this.get(key);
    return data ? JSON.parse(data) : null;
  }

  async setJSON(key, value, ttl) {
    return await this.set(key, JSON.stringify(value), ttl);
  }
}
