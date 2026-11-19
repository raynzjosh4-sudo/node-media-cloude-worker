# N.O.D.E. FastAPI authentication API

This service exposes the app's email/password auth flow through FastAPI. Supabase
Auth remains the identity/session provider, while this API generates verification
and password-reset messages and delivers them through the configured SMTP server.
Google sign-in remains in the Flutter app.

## Configure and run

1. Copy `.env.example` to `.env` and configure the Supabase URL, anon key,
   server-only service-role key, and SMTP settings. Never put
   `SUPABASE_SERVICE_ROLE_KEY` or SMTP credentials in the mobile app. Set
   `APP_ENV` to `production` in production and configure explicit
   `CORS_ALLOWED_ORIGINS` and `ALLOWED_HOSTS` values for the deployed app.
2. From this directory, install dependencies and start the API:

   ```powershell
   $env:PYTHONPATH=".."
   .\..\venv\Scripts\python.exe -m pip install -r requirements.txt
   .\..\venv\Scripts\python.exe -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
   ```

3. Set `AUTH_API_BASE_URL` in the Flutter app's `.env`:
   - Android emulator: `http://10.0.2.2:8000`
   - Web or iOS simulator: `http://localhost:8000`
   - Physical device: use the computer's LAN IP for local testing, or the
     deployed HTTPS API URL.

`CORS_ALLOWED_ORIGINS` and `ALLOWED_HOSTS` are comma-separated. Production
startup requires explicit values and an HTTPS Supabase URL; interactive API
documentation is disabled in production. `/health` is a liveness check and
`/health/ready` returns ready only when Supabase configuration is present.

## Email auth endpoints

- `POST /api/v1/auth/email/sign-in`
- `POST /api/v1/auth/email/sign-up`
- `POST /api/v1/auth/email/otp/verify`
- `POST /api/v1/auth/email/otp/resend`
- `POST /api/v1/auth/email/password-reset`
- `PUT /api/v1/auth/email/password` (requires the current Supabase bearer token)
- `DELETE /api/v1/auth/email/pending-account`
- `DELETE /api/v1/auth/account` (requires the current Supabase bearer token)

The API uses Supabase's admin link-generation endpoint to create signup OTPs and
password-reset links, then sends them itself through SMTP. OTP verification and
password changes still use Supabase Auth, so the existing identity provider and
session format remain in place. Configure the mail sender's verified domain,
SPF, DKIM, and DMARC records before production use.

## API structure

Authentication is organized by feature under `authentication/email_auth`:

- `models/` contains one request model per file.
- `endpoints/` contains one endpoint function per file.
- `dependencies/` contains shared authentication dependencies.
- `supabase_auth.py` contains the Supabase Auth integration.
- `router.py` gathers the email-auth endpoints under `/api/v1/auth`.
- `email_delivery.py` sends email through the configured SMTP server.
- `auth_templates/` contains the verification-code and password-reset templates
  rendered and sent by this API.

Use the same feature structure for additional API areas and auth flows.

The API reuses one bounded `httpx` connection pool per application process.
For deployment, terminate TLS at a trusted ingress, configure trusted proxy
headers for that ingress, and apply request-rate limits at the ingress and in
Supabase Auth (especially for OTP resend and password-reset routes).

Run the API with multiple workers only behind a production ASGI server or
managed platform, and keep the Supabase anon key in server environment
configuration rather than source control.

API-generated errors use an `error` object containing a stable `code` and
user-safe `message`, plus a `request_id` that is also returned in the
`X-Request-ID` header. Validation errors omit submitted values. Supabase
4xx responses (including rate limits) retain their original status and body
for client compatibility; Supabase 5xx responses are logged and returned as a
generic 502.

Run backend tests with:

```powershell
$env:PYTHONPATH=".."
.\..\venv\Scripts\python.exe -m pytest
```
