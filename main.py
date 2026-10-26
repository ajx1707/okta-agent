"""
Main entry point for External Supplier Agent A2A Server.
Wraps the ADK agent into an A2A-compliant ASGI application with Okta JWT security.
"""

import os
import uvicorn
from starlette.responses import JSONResponse
from google.adk.a2a.utils.agent_to_a2a import to_a2a

try:
    from external_supplier_agent.agent import create_supplier_agent
    from external_supplier_agent.auth import OktaAuthMiddleware
except ImportError:
    from agent import create_supplier_agent
    from auth import OktaAuthMiddleware

port = int(os.environ.get("PORT", 8080))
host = os.environ.get("HOST", "0.0.0.0")

# 1. Create the ADK Supplier Agent
supplier_agent = create_supplier_agent()

# 2. Wrap into A2A ASGI App (exposes GET /.well-known/agent-card.json and POST /)
raw_app = to_a2a(
    supplier_agent,
    host=host,
    port=port
)

# 3. Add health check endpoint using Starlette's add_route
async def health_check(request):
    return JSONResponse({
        "status": "HEALTHY",
        "service": "external-supplier-agent",
        "auth_provider": "Okta",
        "protocol": "A2A-1.0"
    })

raw_app.add_route("/health", health_check, methods=["GET"])

# 4. Wrap into Okta JWT Authentication Middleware (ASGI standard)
app = OktaAuthMiddleware(raw_app)

if __name__ == "__main__":
    print(f"Starting External Supplier A2A Server (Okta-Protected) on {host}:{port}")
    uvicorn.run(app, host=host, port=port)
