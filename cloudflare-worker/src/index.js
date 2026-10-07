/**
 * JobPortal ERP - Cloudflare Worker Edge Gateway
 * Account: varundigitaluiux@gmail.com
 */
export default {
  async fetch(request, env, ctx) {
    const url = new URL(request.url);

    // Edge health check
    if (url.pathname === '/cloudflare-status') {
      return new Response(JSON.stringify({
        status: 'healthy',
        service: 'JobPortal ERP Cloudflare Worker',
        account: 'varundigitaluiux@gmail.com',
        edge_datacenter: request.cf?.colo || 'global',
        timestamp: new Date().toISOString()
      }, null, 2), {
        headers: { 'Content-Type': 'application/json' }
      });
    }

    const backendUrl = env.BACKEND_URL || 'https://definition-gotten-garlic-takes.trycloudflare.com';
    const targetUrl = new URL(url.pathname + url.search, backendUrl);

    // Forward request to backend
    const modifiedRequest = new Request(targetUrl.toString(), {
      method: request.method,
      headers: request.headers,
      body: request.method !== 'GET' && request.method !== 'HEAD' ? request.body : undefined,
      redirect: 'manual'
    });

    try {
      const response = await fetch(modifiedRequest);
      const newHeaders = new Headers(response.headers);
      newHeaders.set('X-Edge-Powered-By', 'Cloudflare Workers (varundigitaluiux)');
      newHeaders.set('X-Colo', request.cf?.colo || 'edge');

      return new Response(response.body, {
        status: response.status,
        statusText: response.statusText,
        headers: newHeaders
      });
    } catch (err) {
      return new Response('<h3>JobPortal ERP Edge Gateway</h3><p>Connecting to backend instance... ' + err.message + '</p>', {
        status: 502,
        headers: { 'Content-Type': 'text/html' }
      });
    }
  }
};