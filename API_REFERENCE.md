# N.O.D.E. Wholesale Platform — Complete API Reference

> **Base URL (Production):** `https://node-wholesale-api.onrender.com`  
> **Base URL (Local):** `http://localhost:8000`  
> **Auth Header:** `Authorization: Bearer <JWT_TOKEN>` (required on all 🔐 endpoints)

---

## 🔑 Authentication — `/api/v1/auth`

All auth endpoints use a **local SQLite database** (not Supabase). No auth header required unless noted.

### `POST /api/v1/auth/email/sign-up`
Register a new account. Sends an OTP code to the email.

**Request body:**
```json
{
  "email": "user@example.com",
  "password": "StrongPassword123",
  "full_name": "Jane Merchant"
}
```
**Response `200`:**
```json
{ "message": "OTP sent to your email. Please verify to activate your account." }
```
**Errors:** `409` email already exists

---

### `POST /api/v1/auth/email/otp/verify`
Verify the signup OTP to activate the account and receive a JWT.

**Request body:**
```json
{ "email": "user@example.com", "token": "482910" }
```
**Response `200`:**
```json
{ "access_token": "eyJ...", "token_type": "bearer", "user": { "id": "...", "email": "...", "full_name": "...", "role": "customer" } }
```
**Errors:** `400` invalid/expired OTP

---

### `POST /api/v1/auth/email/otp/resend`
Re-send OTP to an unverified account.

**Request body:**
```json
{ "email": "user@example.com" }
```
**Response `200`:**
```json
{ "message": "OTP resent successfully." }
```

---

### `POST /api/v1/auth/email/sign-in`
Login with email and password.

**Request body:**
```json
{ "email": "user@example.com", "password": "StrongPassword123" }
```
**Response `200`:**
```json
{ "access_token": "eyJ...", "token_type": "bearer", "user": { ... } }
```
**Errors:** `401` invalid credentials, `403` account not verified

---

### `POST /api/v1/auth/email/password-reset`
Request a password reset link/token (sent to email).

**Request body:**
```json
{ "email": "user@example.com" }
```
**Response `200`:**
```json
{ "message": "If this email is registered, a reset link has been sent." }
```

---

### `PUT /api/v1/auth/email/password`
Update password. Works in two modes:
- **Logged in:** pass `Authorization: Bearer <token>` header
- **Reset link:** pass `?token=<reset_token>` query param

**Request body:**
```json
{ "new_password": "NewSecurePass123" }
```
**Response `200`:**
```json
{ "message": "Password updated successfully." }
```

---

### `GET /api/v1/auth/me` 🔐
Return current authenticated user from local DB.

**Response `200`:**
```json
{ "user": { "id": "...", "email": "...", "full_name": "...", "role": "customer", "is_verified": true } }
```

---

### `DELETE /api/v1/auth/account` 🔐
Permanently delete the authenticated user's account from local DB.

**Response `200`:**
```json
{ "message": "Your account has been successfully deleted." }
```

---

### `DELETE /api/v1/auth/email/pending-account`
Delete an **unverified** (pending) account.

**Request body:**
```json
{ "user_id": "uuid-of-unverified-user" }
```
**Response `200`:**
```json
{ "message": "Pending account removed." }
```

---

## 👤 Profile — `/api/v1/profile`

Profile data lives in **Supabase** (`users_table`, `business_profiles_table`).

### `GET /api/v1/profile` 🔐
Get current user's profile and business info.

**Response `200`:**
```json
{
  "user": {
    "id": "uuid",
    "full_name": "Jane Merchant",
    "email": "jane@example.com",
    "role": "customer",
    "profile_pic_url": "https://..."
  },
  "business": {
    "user_id": "uuid",
    "legal_name": "Jane Merchants Ltd",
    "phone_number": "+256700000000",
    "latitude": 0.347,
    "longitude": 32.582,
    "region": "Central",
    "city": "Kampala",
    "physical_address": "Plot 12, Nakivubo Road"
  }
}
```

---

### `PUT /api/v1/profile` 🔐
Update basic user info. Send only the fields you want to change.

**Request body** *(all optional)*:
```json
{
  "full_name": "Updated Name",
  "profile_pic_url": "https://..."
}
```
**Response `200`:** Updated `UserProfile` object.

---

### `PUT /api/v1/profile/business` 🔐
Upsert the user's business profile.

**Request body** *(all optional)*:
```json
{
  "legal_name": "My Business Ltd",
  "phone_number": "+256700000000",
  "latitude": 0.347,
  "longitude": 32.582,
  "region": "Central",
  "city": "Kampala",
  "physical_address": "Plot 12, Nakivubo Road"
}
```
**Response `200`:** Updated `BusinessProfile` object.

---

### `PUT /api/v1/profile/trading-terms` 🔐
Store wholesale trading terms on the user's profile (JSONB).

**Request body:**
```json
{
  "content": "Standard wholesale terms apply.",
  "moq": "50 units minimum",
  "warranty": "6 months",
  "paymentTerms": "50% upfront, 50% on delivery",
  "deliveryTerms": "CIF Kampala"
}
```
**Response `200`:**
```json
{ "trading_terms": { ... } }
```

---

### `POST /api/v1/profile/apply-supplier` 🔐
Submit a supplier application. The user **must have a complete business profile** first (legal_name, phone_number, physical_address, latitude/longitude).

**Request body:** None — uses the authenticated user's existing business profile.

**Response `200`:**
```json
{
  "status": "pending_approval",
  "message": "Your supplier application has been submitted...",
  "business": { "legal_name": "...", "phone_number": "...", ... }
}
```
**Errors:**
- `400` Already a supplier
- `400` Missing business profile fields

---

## 📦 Products — `/api/v1/products`

### `GET /api/v1/products`
List all products (paginated). Public — no auth required.

**Query params:**
| Param | Type | Default | Description |
|-------|------|---------|-------------|
| `supplier_id` | UUID | — | Filter by supplier |
| `category_id` | UUID | — | Filter by category |
| `search` | string | — | Search by name or SKU |
| `page` | int | 1 | Page number |
| `limit` | int | 20 | Items per page (max 100) |
| `sort_by` | string | `created_at` | Sort column |
| `ascending` | bool | false | Sort direction |

**Response `200`:**
```json
{
  "data": [ { "id": "...", "name": "...", "image_url": "...", "price_tiers": [...] } ],
  "total": 150,
  "page": 1,
  "limit": 20,
  "has_more": true
}
```

---

### `GET /api/v1/products/popular`
Get popular and trending products for the home screen explore section (matching Flutter's `popularProductsProvider` and `PopularSection`). Public.

**Query params:**
| Param | Type | Default | Description |
|---|---|---|---|
| `category_id` | UUID | — | Optional category filter when user taps category chips |
| `limit` | int | 15 | Number of products to return (default 15) |
| `offset` | int | 0 | Offset for pagination |

**Response `200`:** `list[ProductResponse]` with full pricing tiers and enriched supplier details.

---

### `GET /api/v1/products/categories`
List all product categories. Public.

**Response `200`:** `[ { "id": "cat_1a2b3c", "name": "Textiles", "parent_id": null, "level": 0, "image_url": "https://..." } ]`

---

### `POST /api/v1/products/categories` 🔐 *(Supplier/Admin)*
Create a new category or subcategory with an optional image uploaded to Cloudflare R2 via JSON.

**Request body:**
```json
{
  "name": "Cotton Fabrics",
  "parent_id": "cat_textiles",
  "level": 1,
  "image_base64": "data:image/png;base64,iVBORw0KGgo...",
  "image_url": "https://..."
}
```
- **Root Category:** `parent_id: null`, `level: 0`
- **Subcategory:** `parent_id: "cat_parent_id"`, `level: 1`
- **Image upload:** Pass `image_base64` and the backend will automatically upload it to **Cloudflare R2** under `categories/` and set `image_url`!

**Response `201`:**
```json
{
  "id": "cat_7f8a9b1c",
  "name": "Cotton Fabrics",
  "parent_id": "cat_textiles",
  "image_url": "https://nodemediafiles.crimchart.com/...",
  "level": 1,
  "item_count": 0
}
```

---

### `POST /api/v1/products/categories/with-image` 🔐 *(Supplier/Admin)*
Create a new category or subcategory with a direct multipart image file upload (matching Flutter's `AdminCreateCategoryPage`).

**Content-Type:** `multipart/form-data`  
**Form fields:**
- `name` (string, required): Category or subcategory name
- `parent_id` (string, optional): Parent category ID (omit for root level)
- `level` (int, default 0): Hierarchy level (`0` for root, `1` for subcategory)
- `file` (binary file, optional): Category cover image from gallery/camera

**What the backend does:**
1. Uploads the image file directly to **Cloudflare R2** under `categories/`.
2. Stores the public CDN URL in `categories_table`.
3. Returns the newly created category with its `id` (`cat_xxxxxxxx`).

**Response `201`:** Category object with `id`, `name`, `parent_id`, `image_url`, `level`.

---

### `POST /api/v1/products/categories/{category_id}/image` & `PUT /api/v1/products/categories/{category_id}/image` 🔐 *(Supplier/Admin)*
Upload or replace the cover image for an existing category or subcategory.

**Content-Type:** `multipart/form-data`  
**Body:** Form field `file` (image file)

**Response `200`:**
```json
{
  "id": "cat_7f8a9b1c",
  "image_url": "https://nodemediafiles.crimchart.com/...",
  "category": { "id": "cat_7f8a9b1c", "name": "Cotton Fabrics", "image_url": "..." }
}
```



---

### `GET /api/v1/products/suppliers`
List all verified supplier users. Public.

**Response `200`:** Array of supplier objects with business info.

---

### `GET /api/v1/products/{product_id}`
Get full product details by UUID. Public.

**Path param:** `product_id` — UUID

**Response `200`:** Full `ProductResponse` (see schema below).

---

### `GET /api/v1/products/slug/{slug}`
Get full product by URL slug. Public.

**Path param:** `slug` — e.g. `blue-cotton-shirt-a3f2b1`

**Response `200`:** Full `ProductResponse`.

---

### `GET /api/v1/products/my-products` 🔐 *(Supplier/Admin)*
List only the products posted by the currently authenticated supplier.

**Query params:** Same as `GET /products` (page, limit, search, sort_by, ascending)

**Response `200`:** `PaginatedProducts` — same shape as list.

---

### `POST /api/v1/products` 🔐 *(Supplier/Admin)*
Publish a new product to the catalog.

**Request body:**
```json
{
  "sku": "SKU-001",
  "name": "Cotton Shirt",
  "brand": "BrandCo",
  "image_url": "https://...",
  "image_base64": "data:image/png;base64,...",
  "category_id": "cat_textiles",
  "new_category": {
    "name": "Organic Cotton Yarns",
    "parent_id": "cat_textiles",
    "level": 1,
    "image_base64": "data:image/png;base64,..."
  },
  "srp": 25000,
  "price_tiers": [
    { "minQuantity": 1, "price": 25000, "label": "Retail" },
    { "minQuantity": 50, "price": 20000, "label": "Wholesale" }
  ],
  "current_stock": 500,
  "lead_time_days": 3,
  "weight_kg": 0.3,
  "volume_cbm": 0.001,
  "origin_country": "Uganda",
  "material": "100% Cotton",
  "warehouse_loc": "Nakivubo, Kampala",
  "available_colors": [ { "name": "Blue", "hexCode": "#0000FF" } ],
  "available_sizes": [ { "name": "Large", "abbreviation": "L" } ],
  "available_materials": [ { "name": "Cotton", "imageUrl": "https://..." } ],
  "support_info": { "whatsapp": "+256700000000", "phone": "+256700000000", "email": "support@brand.com" },
  "trading_terms": { "moq": "50 units", "paymentTerms": "50% upfront", "deliveryTerms": "CIF" }
}
```
> **Inline Category & Subcategory Creation:** If `new_category` is provided, the backend automatically creates the new category or subcategory in `categories_table`, uploads its image to Cloudflare R2, and links it to this product!

**Response `201`:** Full `ProductResponse`

> [!NOTE]
> `slug` is auto-generated from name if omitted. `supplier_id` is always set to the caller's ID (admins can override it).

---

### `PUT /api/v1/products/{product_id}` 🔐 *(Supplier/Admin)*
Update a product. Suppliers can only edit their **own** products.

**Request body:** Any subset of product fields (all optional).
- **Supports `image_base64`**: Pass a base64 string or Data URI (`data:image/png;base64,...`) and the backend will automatically upload it to **Cloudflare R2**, get the public CDN URL, and save it in the database!

**Response `200`:** Updated `ProductResponse`.

**Errors:** `403` if supplier tries to edit another supplier's product.

---

### `POST /api/v1/products/{product_id}/image` & `PUT /api/v1/products/{product_id}/image` 🔐 *(Supplier/Admin)*
Direct multipart image upload: receives an image file from the client, uploads it to **Cloudflare R2**, and saves the resulting public CDN URL into `products_table` in Supabase DB.

**Content-Type:** `multipart/form-data`  
**Body:** Form field `file` (image file)

**Response `200`:** Updated `ProductResponse` with the new `image_url` and updated `media_urls`.

---

### `POST /api/v1/products/upload-image` 🔐 *(Supplier/Admin)*
Standalone image upload: uploads any image to Cloudflare R2 and returns its public CDN URL.

**Content-Type:** `multipart/form-data`  
**Body:** Form field `file` (image file)

**Response `200`:**
```json
{
  "url": "https://nodemediafiles.crimchart.com/...",
  "filename": "shirt.png",
  "content_type": "image/png"
}
```

---

### `DELETE /api/v1/products/{product_id}` 🔐 *(Supplier/Admin)*
Delete a product. Suppliers can only delete their **own** products.

**Response `204`** No Content.

**Errors:** `403` unauthorized, `404` not found.

---

## 🛒 Orders — `/api/v1/orders`

### Draft Sync

#### `GET /api/v1/orders/drafts` 🔐
Get all saved order drafts for the current user.

**Response `200`:** Array of `OrderResponse` objects.

---

#### `POST /api/v1/orders/drafts` 🔐
Save or update a local draft (synced from Flutter SQLite/Drift).

**Request body:**
```json
{
  "order_id": "local-uuid",
  "supplier_id": "supplier-uuid",
  "business_name": "My Business",
  "business_phone": "+256700000000",
  "business_city": "Kampala",
  "business_address": "Plot 12",
  "latitude": 0.347,
  "longitude": 32.582,
  "total_amount": 1500000,
  "entries_json": [ { "product_id": "...", "quantity": 10, "unit_price": 25000 } ]
}
```
**Response `200`:** `OrderResponse`

---

#### `DELETE /api/v1/orders/drafts/{id}` 🔐
Delete a draft by ID.

**Response `200`:**
```json
{ "success": true, "message": "Draft deleted successfully" }
```

---

### Supplier View

#### `GET /api/v1/orders/supplier/incoming` 🔐
Get paginated incoming orders where the current user is the **supplier**.

**Query params:**
| Param | Type | Default | Description |
|-------|------|---------|-------------|
| `page` | int | 1 | Page number |
| `limit` | int | 20 | Items per page |
| `status` | string | — | Filter: `new`, `processing`, `confirmed`, `completed`, `cancelled` |

**Response `200`:** `PaginatedOrders`

---

### Buyer View

#### `POST /api/v1/orders` 🔐
Send a wholesale order to a supplier.

**Request body:** Same as `POST /orders/drafts`

**Response `201`:** `OrderResponse`

> [!NOTE]
> Automatically sends an **order confirmation email + PDF** to both buyer and supplier in the background.

---

#### `GET /api/v1/orders` 🔐
Get paginated orders placed by the current user (buyer view).

**Query params:** `page`, `limit`

**Response `200`:** `PaginatedOrders`

---

#### `GET /api/v1/orders/{order_id}` 🔐
Get a single order's full details.

**Response `200`:** `OrderResponse`

---

#### `GET /api/v1/orders/{order_id}/pdf` 🔐
Download the official N.O.D.E. Order Spec Sheet PDF.

**Response `200`:** `application/pdf` stream

> Accessible by buyer, supplier, or admin. Streams the PDF inline in browser.

---

#### `PATCH /api/v1/orders/{order_id}/status` 🔐
Update order status (supplier updates buyer's order).

**Request body:**
```json
{ "status": "processing" }
```
**Valid statuses:** `new` · `processing` · `submitted` · `completed` · `cancelled` · `pending` · `draft`

**Response `200`:** Updated `OrderResponse`

> [!NOTE]
> Triggers background email + PDF to both parties and in-app notifications.

---

#### `DELETE /api/v1/orders/{order_id}` 🔐
Delete or cancel an order. Must be the order's owner.

**Response `200`:**
```json
{ "success": true, "message": "Order deleted successfully" }
```

---

## 🔔 Notifications — `/api/v1/notifications`

### `GET /api/v1/notifications` 🔐
Get paginated in-app notifications for the current user.

**Query params:**
| Param | Type | Default | Description |
|-------|------|---------|-------------|
| `limit` | int | 10 | Max items (1–50) |
| `offset` | int | 0 | Pagination offset |
| `category` | string | — | `all`, `order`, `account`, `inventory`, `system` |

**Response `200`:**
```json
{
  "data": [ { "id": "...", "title": "...", "body": "...", "category": "order", "is_unread": true, "created_at": "..." } ],
  "total": 5,
  "limit": 10,
  "offset": 0,
  "has_more": false
}
```

---

### `PATCH /api/v1/notifications/{notification_id}/read` 🔐
Mark a single notification as read.

**Response `204`** No Content.

---

### `PATCH /api/v1/notifications/read-all` 🔐
Mark all notifications as read.

**Response `200`:**
```json
{ "message": "All notifications marked as read", "updated_count": 5 }
```

---

### `DELETE /api/v1/notifications/{notification_id}` 🔐
Delete a notification.

**Response `204`** No Content.

---

### `POST /api/v1/notifications/device-token` 🔐
Register a Firebase Cloud Messaging (FCM) push token for a device.

**Request body:**
```json
{ "token": "fcm-token-string", "device_type": "android" }
```
**Response `201`:**
```json
{ "message": "Device token registered successfully", "token": "..." }
```

---

### `DELETE /api/v1/notifications/device-token` 🔐
Unregister an FCM push token.

**Query param:** `token=<fcm-token>`

**Response `204`** No Content.

---

## 🏷️ Saved Items — `/api/v1/saved-items`

### `GET /api/v1/saved-items` 🔐
List all saved/wishlisted items for the current user.

**Response `200`:** Array of `SavedItemResponse`.

---

### `POST /api/v1/saved-items` 🔐
Save a product to wishlist.

**Request body:**
```json
{
  "product_id": "uuid",
  "quantity": 10,
  "selected_color": "Blue",
  "selected_size": "L",
  "product_snapshot": { }
}
```
**Response `200`:** `SavedItemResponse`

---

### `GET /api/v1/saved-items/{product_id}/check` 🔐
Check if a product is saved by the current user.

**Response `200`:**
```json
{ "is_saved": true, "saved_item_id": "uuid" }
```

---

### `DELETE /api/v1/saved-items/{saved_item_id}` 🔐
Remove a saved item.

**Response `204`** No Content.

---

## 📊 Records (Financial) — `/api/v1/records`

### `GET /api/v1/records` 🔐
List user's financial records (paginated).

**Query params:** `limit`, `offset`, `is_archived` (bool)

**Response `200`:** `PaginatedRecords`

---

### `GET /api/v1/records/{record_id}` 🔐
Get a single financial record.

**Response `200`:** `RecordResponse`

---

### `POST /api/v1/records` 🔐
Create a new financial record.

**Request body:** `RecordCreate` schema (amount, type, description, etc.)

**Response `201`:** `RecordResponse`

---

### `PUT /api/v1/records/{record_id}` 🔐
Update an existing record.

**Response `200`:** Updated `RecordResponse`

---

### `DELETE /api/v1/records/{record_id}` 🔐
Delete a record.

**Response `204`** No Content.

---

## 🎯 Promotions — `/api/v1/promotions`

### `GET /api/v1/promotions`
List all active promotional campaigns. Public.

**Response `200`:** Array of `PromotionResponse`

---

### `GET /api/v1/promotions/{promo_id}`
Get a single promotion by ID. Public.

**Response `200`:** `PromotionResponse`

---

## 🛡️ Admin — `/api/v1/admin`

> [!CAUTION]
> All admin endpoints require a valid JWT from an account with `role = "admin"`. Any other role gets `403 Forbidden`.

### `GET /api/v1/admin/supplier-applications` 🔐 *(Admin)*
List users with `role='customer'` who have submitted business profiles (pending supplier review).

**Response `200`:** Array of `PotentialSupplierItem`
```json
[
  { "user_id": "uuid", "email": "...", "full_name": "...", "legal_name": "...", "phone_number": "...", "physical_address": "..." }
]
```

---

### `POST /api/v1/admin/suppliers/{user_id}/approve` 🔐 *(Admin)*
Approve a user as a verified supplier (sets `role = "supplier"`).

**Path param:** `user_id` — UUID of the user to approve

**Response `200`:**
```json
{ "user_id": "uuid", "role": "supplier", "message": "User successfully approved..." }
```

> Sends approval email + in-app notification to the user in the background.

---

### `POST /api/v1/admin/suppliers/{user_id}/revoke` 🔐 *(Admin)*
Revoke supplier status (sets `role = "customer"`).

**Response `200`:**
```json
{ "user_id": "uuid", "role": "customer", "message": "Supplier privileges revoked..." }
```

> Sends revocation email + in-app notification to the user.

---

### `POST /api/v1/admin/categories` 🔐 *(Admin)*
Create a new product category.

**Request body:**
```json
{
  "name": "Fabrics",
  "parent_id": null,
  "image_url": "https://...",
  "level": 0
}
```
**Response `201`:** Created category object.

---

### `GET /api/v1/admin/users` 🔐 *(Admin)*
List all registered platform users.

**Query params:**
| Param | Type | Default | Description |
|-------|------|---------|-------------|
| `role` | string | — | Filter: `customer`, `supplier`, `admin` |
| `limit` | int | 50 | Max results (1–100) |
| `offset` | int | 0 | Pagination offset |

**Response `200`:** Array of user objects.

---

### `PATCH /api/v1/admin/users/{user_id}/role` 🔐 *(Admin)*
Directly change any user's role.

**Request body:**
```json
{ "role": "supplier" }
```
**Valid roles:** `customer` · `supplier` · `admin`

**Response `200`:** Updated user object.

---

## ❤️ Health Checks

| Endpoint | Description |
|----------|-------------|
| `GET /health` | Returns `{"status": "ok"}` — always healthy |
| `GET /health/ready` | Checks DB connection — `{"status": "ready"}` or `500` |

---

## 🗂️ Background Tasks (Auto-Triggered)

These run automatically — not called directly by the client.

| Trigger | What Happens |
|---------|-------------|
| `POST /orders` | Email (buyer + supplier) + PDF attachment + in-app notification |
| `PATCH /orders/{id}/status` | Email (buyer + supplier) + PDF attachment + in-app notification to both |
| `POST /admin/suppliers/{id}/approve` | Approval email + in-app notification to user |
| `POST /admin/suppliers/{id}/revoke` | Revocation email + in-app notification to user |

---

## 🔐 Role Permission Matrix

| Endpoint Group | customer | supplier | admin |
|----------------|----------|---------- |-------|
| Auth | ✅ | ✅ | ✅ |
| Profile (read/write own) | ✅ | ✅ | ✅ |
| Apply supplier | ✅ | ❌ | ❌ |
| Products (read) | ✅ | ✅ | ✅ |
| Products (create/edit/delete) | ❌ | ✅ (own only) | ✅ |
| Orders (place) | ✅ | ✅ | ✅ |
| Orders (update status) | ✅ | ✅ | ✅ |
| Supplier incoming orders | ❌ | ✅ | ✅ |
| Notifications / Saved / Records | ✅ | ✅ | ✅ |
| Admin endpoints | ❌ | ❌ | ✅ |
