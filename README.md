# N.O.D.E. Wholesale Backend API

FastAPI backend powering the N.O.D.E. wholesale ordering and supplier ecosystem.

## 🚀 Features

- **Authentication & Security:** Email OTP signup, password recovery, JWT sessions, role guards (`customer`, `supplier`, `admin`).
- **Catalog & Products:** Full CRUD with pricing tiers, variants, stock, search, and **Cloudflare R2 image upload pipeline**.
- **Wholesale Orders:** Order placement, supplier incoming queue, lifecycle status updates, draft synchronization.
- **Spec Sheet & PDF Engine:** ReportLab-based N.O.D.E. invoice & spec sheet generation matching the Flutter app design, with dynamic QR code verification.
- **Automated Notifications:** Email dispatcher via Resend with PDF attachments + Supabase in-app notifications.
- **Admin Suite:** Supplier verification workflow (review, approve, revoke), category management, and user privilege control.

---

## 📚 API Reference

Detailed endpoints, request bodies, query parameters, and response schemas are documented in:
👉 **[API_REFERENCE.md](API_REFERENCE.md)**

---

## ☁️ Deployment on Render.com

This repository includes a [`render.yaml`](render.yaml) Blueprint configured for zero-friction deployment.

1. Connect this repo to **[Render.com](https://render.com)**.
2. Render will automatically detect `render.yaml` and configure the Python web service.
3. In the Render Dashboard under **Environment**, set your production secrets:
   - `JWT_SECRET_KEY`
   - `RESEND_API_KEY`
   - `SUPABASE_ANON_KEY`
   - `SUPABASE_SERVICE_ROLE_KEY`
4. Deploy will start and pass health check at `/health`.
