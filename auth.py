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
JWKS_URL = os.environ.get("OKTA_JWKS_URL", f"https://{OKTA_DOMAIN}/oauth2/v1/keys")

class OktaAuthMiddleware(BaseHTTPMiddleware):
    def __init__(self, app):
        super().__init__(app)
        # Initialize PyJWKClient pointing to the tenant's primary JWKS keys endpoint
        self.jwks_client = PyJWKClient(JWKS_URL, cache_keys=True, max_cached_keys=10)
        self.fallback_jwks_client = PyJWKClient(f"https://{OKTA_DOMAIN}/oauth2/default/v1/keys", cache_keys=True)
        print(f"[Okta Auth Middleware] Initialized with primary JWKS: {JWKS_URL}")

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
            try:
                signing_key = self.jwks_client.get_signing_key_from_jwt(token)
            except Exception:
                signing_key = self.fallback_jwks_client.get_signing_key_from_jwt(token)
            
            # Decode and validate claims
            decoded_claims = jwt.decode(
                token,
                signing_key.key,
                algorithms=["RS256"],
                options={"verify_aud": False, "verify_iss": False}
            )

            # Verify that issuer belongs to our Okta tenant
            token_iss = decoded_claims.get("iss", "")
            if not token_iss.startswith(f"https://{OKTA_DOMAIN}"):
                raise ValueError(f"Invalid token issuer: {token_iss}")

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
