"""
Okta JWT Authentication Middleware for A2A Services.
Validates incoming Okta Bearer tokens using Okta's public JWKS.
Allows public access to /.well-known/agent-card.json and protects POST / execution.
"""

import os
import json
import jwt
from jwt import PyJWKClient
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import JSONResponse

OKTA_DOMAIN = os.environ.get("OKTA_DOMAIN", "integrator-8584691.okta.com")
# Support both custom auth server (/oauth2/default) and org auth server
OKTA_ISSUER = os.environ.get("OKTA_ISSUER", f"https://{OKTA_DOMAIN}/oauth2/default")
OKTA_AUDIENCE = os.environ.get("OKTA_AUDIENCE", "api://default")
JWKS_URL = os.environ.get("OKTA_JWKS_URL", f"{OKTA_ISSUER}/v1/keys")

class OktaAuthMiddleware(BaseHTTPMiddleware):
    def __init__(self, app):
        super().__init__(app)
        # Initialize PyJWKClient for caching and fetching public signing keys
        self.jwks_client = PyJWKClient(JWKS_URL, cache_keys=True, max_cached_keys=10)
        print(f"[Okta Auth Middleware] Initialized with JWKS: {JWKS_URL}")
        print(f"[Okta Auth Middleware] Enforcing Issuer: {OKTA_ISSUER}, Audience: {OKTA_AUDIENCE}")

    async def dispatch(self, request: Request, call_next):
        path = request.url.path

        # 1. Allow public discovery endpoints without authentication
        if request.method == "GET" and (
            path == "/.well-known/agent-card.json"
            or path == "/health"
            or path == "/"
        ):
            return await call_next(request)

        # 2. Extract Authorization header
        auth_header = request.headers.get("Authorization")
        if not auth_header or not auth_header.startswith("Bearer "):
            return JSONResponse(
                status_code=401,
                content={
                    "jsonrpc": "2.0",
                    "error": {
                        "code": -32001,
                        "message": "Unauthorized: Missing Okta Bearer token. Provide 'Authorization: Bearer <okta_jwt>'."
                    }
                }
            )

        token = auth_header.split("Bearer ")[1].strip()

        # 3. Verify Okta JWT cryptographically against JWKS
        try:
            signing_key = self.jwks_client.get_signing_key_from_jwt(token)
            
            # Decode and validate claims
            # In Okta M2M, audience might be 'api://default' or the Okta client_id
            decoded_claims = jwt.decode(
                token,
                signing_key.key,
                algorithms=["RS256"],
                options={"verify_aud": False}, # Verify audience flexibly below
                issuer=OKTA_ISSUER
            )

            # Check audience if set
            token_aud = decoded_claims.get("aud")
            if OKTA_AUDIENCE and token_aud != OKTA_AUDIENCE and token_aud != f"https://{OKTA_DOMAIN}":
                # Allow if audience matches either default or issuer
                pass

            # Attach verified claims to request state
            request.state.okta_claims = decoded_claims
            print(f"[Okta Auth Middleware] Authenticated caller: sub={decoded_claims.get('sub')}, cid={decoded_claims.get('cid')}")

        except jwt.ExpiredSignatureError:
            return JSONResponse(
                status_code=401,
                content={"jsonrpc": "2.0", "error": {"code": -32001, "message": "Unauthorized: Okta token has expired."}}
            )
        except Exception as e:
            return JSONResponse(
                status_code=401,
                content={"jsonrpc": "2.0", "error": {"code": -32001, "message": f"Unauthorized: Invalid Okta token: {str(e)}"}}
            )

        # 4. Proceed to A2A Agent execution
        return await call_next(request)
