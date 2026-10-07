/**
 * JobPortal ERP - Cloudflare Worker Edge Gateway
 * Account: varundigitaluiux@gmail.com
 */
export default {
  async fetch(request, env, ctx) {
    const url = new URL(request.url);

    // Edge health check endpoint
    if (url.pathname === '/cloudflare-status') {
      return new Response(JSON.stringify({
        status: 'healthy',
        service: 'JobPortal ERP Cloudflare Worker',
        account: 'varundigitaluiux@gmail.com',
        edge_datacenter: request.cf?.colo || 'global',
        edge_ip: request.headers.get('CF-Connecting-IP') || 'unknown',
        backend_target: env.BACKEND_URL || 'configured',
        timestamp: new Date().toISOString()
      }, null, 2), {
        headers: {
          'Content-Type': 'application/json',
          'Access-Control-Allow-Origin': '*'
        }
      });
    }

    const backendUrl = env.BACKEND_URL || 'https://definition-gotten-garlic-takes.trycloudflare.com';
    const targetUrl = new URL(url.pathname + url.search, backendUrl);

    // Prepare headers for proxying
    const forwardHeaders = new Headers(request.headers);
    forwardHeaders.set('X-Forwarded-Host', url.host);
    forwardHeaders.set('X-Forwarded-Proto', url.protocol.replace(':', ''));
    if (request.headers.has('CF-Connecting-IP')) {
      forwardHeaders.set('X-Forwarded-For', request.headers.get('CF-Connecting-IP'));
      forwardHeaders.set('X-Real-IP', request.headers.get('CF-Connecting-IP'));
    }

    // Forward request to backend instance
    const modifiedRequest = new Request(targetUrl.toString(), {
      method: request.method,
      headers: forwardHeaders,
      body: request.method !== 'GET' && request.method !== 'HEAD' ? request.body : undefined,
      redirect: 'manual'
    });

    try {
      const response = await fetch(modifiedRequest);
      const newHeaders = new Headers(response.headers);
      newHeaders.set('X-Edge-Powered-By', 'Cloudflare Workers (varundigitaluiux)');
      newHeaders.set('X-Colo', request.cf?.colo || 'edge');

      // Ensure redirects remain on the Cloudflare Worker domain
      if (newHeaders.has('Location')) {
        const rawLoc = newHeaders.get('Location');
        try {
          const locUrl = new URL(rawLoc, backendUrl);
          const backendHost = new URL(backendUrl).host;
          if (locUrl.host === backendHost) {
            newHeaders.set('Location', locUrl.pathname + locUrl.search + locUrl.hash);
          }
        } catch (_) {
          // relative path redirect - left as-is
        }
      }

      return new Response(response.body, {
        status: response.status,
        statusText: response.statusText,
        headers: newHeaders
      });
    } catch (err) {
      return new Response(`<!DOCTYPE html>
<html>
<head>
  <meta charset="utf-8">
  <title>JobPortal ERP — Edge Gateway</title>
  <style>
    body { font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif; background: #0f172a; color: #f8fafc; display: flex; align-items: center; justify-content: center; min-height: 100vh; margin: 0; padding: 20px; }
    .card { background: #1e293b; border: 1px solid #334155; border-radius: 16px; max-width: 540px; padding: 32px; box-shadow: 0 10px 25px rgba(0,0,0,0.5); }
    h2 { margin-top: 0; color: #38bdf8; font-size: 22px; }
    p { color: #94a3b8; font-size: 14px; line-height: 1.6; }
    code { background: #0f172a; padding: 3px 8px; border-radius: 6px; font-family: monospace; color: #f43f5e; font-size: 13px; }
    .btn { display: inline-block; background: #2563eb; color: #fff; text-decoration: none; padding: 10px 18px; border-radius: 8px; font-size: 13px; font-weight: 600; margin-top: 12px; }
  </style>
</head>
<body>
  <div class="card">
    <h2>JobPortal ERP Edge Gateway</h2>
    <p>The Cloudflare Worker edge node (<code>${request.cf?.colo || 'Global'}</code>) is active, but the backend instance is temporarily unreachable.</p>
    <p><strong>Error details:</strong> <code>${err.message}</code></p>
    <p>Ensure the local application tunnel is running via <code>run_tunnel.ps1</code> or check your backend URL configuration.</p>
    <a href="/cloudflare-status" class="btn">Check Edge Status</a>
  </div>
</body>
</html>`, {
        status: 502,
        headers: { 'Content-Type': 'text/html; charset=utf-8' }
      });
    }
  }
};