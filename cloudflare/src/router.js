/**
 * Simple Router for Cloudflare Workers
 */

export class Router {
  constructor() {
    this.routes = new Map();
  }

  get(path, handler) {
    this.addRoute('GET', path, handler);
  }

  post(path, handler) {
    this.addRoute('POST', path, handler);
  }

  put(path, handler) {
    this.addRoute('PUT', path, handler);
  }

  delete(path, handler) {
    this.addRoute('DELETE', path, handler);
  }

  addRoute(method, path, handler) {
    const key = `${method}:${path}`;
    this.routes.set(key, handler);
  }

  match(request) {
    const url = new URL(request.url);
    const key = `${request.method}:${url.pathname}`;
    return this.routes.get(key);
  }
}
