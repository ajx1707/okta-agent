# External Supplier Agent (Okta-Protected A2A Service)

An autonomous A2A Logistics & Warehouse Supplier Agent designed to run outside Google Cloud (on Render, AWS, or on-prem) and protected by **Okta OAuth2 / OIDC**.

## Render Web Service Settings

When deploying this service on Render (render.com):

1. **Environment:** `Python 3` (or `Docker`)
2. **Build Command:** `pip install -r requirements.txt`
3. **Start Command:** `uvicorn main:app --host 0.0.0.0 --port $PORT`
4. **Environment Variables:**
   * `OKTA_DOMAIN`: `integrator-8584691.okta.com`
   * `OKTA_ISSUER`: `https://integrator-8584691.okta.com/oauth2/default`
   * `OKTA_AUDIENCE`: `api://default`
   * `GEMINI_API_KEY`: `<Your Gemini API Key>` (for LLM reasoning)

## How Security Works
* **Public Endpoints (Zero Auth):**
  * `GET /.well-known/agent-card.json`: Allows discovery engines to read identity and declared skills.
  * `GET /health`: Health check for Render load balancers.
* **Protected Endpoints (Okta Auth Required):**
  * `POST /`: Standard A2A JSON-RPC 2.0 message execution endpoint.
  * Every request MUST have `Authorization: Bearer <okta_jwt>`.
  * The middleware cryptographically validates the token against Okta's public JWKS (`.../oauth2/default/v1/keys`).
  * Any unauthenticated or unauthorized caller receives `HTTP 401 Unauthorized`.
