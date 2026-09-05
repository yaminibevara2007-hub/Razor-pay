def apply_security_headers(response):
    """
    Attach standard defensive HTTP security headers to all Flask responses.
    Compatible with Chart.js, Google Fonts, and fintech UI requirements.
    """
    response.headers['X-Content-Type-Options'] = 'nosniff'
    response.headers['X-Frame-Options'] = 'SAMEORIGIN'
    response.headers['X-XSS-Protection'] = '1; mode=block'
    response.headers['Referrer-Policy'] = 'strict-origin-when-cross-origin'
    response.headers['Permissions-Policy'] = 'camera=(), microphone=(), geolocation=()'
    
    # Content Security Policy (allows local assets, Google Fonts, Chart.js CDN)
    csp_directives = [
        "default-src 'self'",
        "script-src 'self' 'unsafe-inline' https://cdn.jsdelivr.net",
        "style-src 'self' 'unsafe-inline' https://fonts.googleapis.com",
        "font-src 'self' https://fonts.gstatic.com data:",
        "img-src 'self' data: https:",
        "connect-src 'self' http://localhost:5005 http://127.0.0.1:5005 http://localhost:8000 http://127.0.0.1:8000",
        "frame-ancestors 'self'"
    ]
    response.headers['Content-Security-Policy'] = '; '.join(csp_directives)
    
    return response
