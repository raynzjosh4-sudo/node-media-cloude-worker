/**
 * NODE Media Pipeline Worker
 * Cloudflare Edge Worker for R2 media uploads and image serving.
 * 
 * Supports both:
 * 1. Direct mobile Flutter uploads via Supabase user JWT.
 * 2. FastAPI backend uploads via X-Backend-Secret.
 */

const MEDIA_API_PATH = "/_node/media";
const MAX_MEDIA_BYTES = 12 * 1024 * 1024; // 12 MB max

const corsHeaders = {
  "Access-Control-Allow-Origin": "*",
  "Access-Control-Allow-Headers": "authorization, apikey, content-type, x-node-folder, x-backend-secret, x-user-id",
  "Access-Control-Allow-Methods": "POST, DELETE, OPTIONS",
};

function jsonResponse(body, status = 200) {
  return Response.json(body, { status, headers: corsHeaders });
}

function requestError(status, message) {
  return Object.assign(new Error(message), { status });
}

async function getAuthenticatedUser(request, env) {
  // 1. Direct Backend Auth via shared secret
  const backendSecret = request.headers.get("X-Backend-Secret");
  if (env.BACKEND_SECRET && backendSecret && backendSecret === env.BACKEND_SECRET) {
    const userId = request.headers.get("X-User-Id") || "1a47f0fe-3f4d-487f-95b5-1f7cfe27b7b7";
    return {
      user: { id: userId },
      token: null,
      supabaseUrl: env.SUPABASE_URL,
      isBackend: true,
    };
  }

  // 2. Mobile App Supabase Session Auth
  const token = request.headers.get("Authorization")?.match(/^Bearer\s+(.+)$/i)?.[1];
  if (!token) throw requestError(401, "Authentication is required.");

  const supabaseUrl = env.SUPABASE_URL?.replace(/\/+$/, "");
  if (!supabaseUrl || !env.SUPABASE_ANON_KEY) {
    throw requestError(500, "Worker authentication is not configured.");
  }

  const response = await fetch(`${supabaseUrl}/auth/v1/user`, {
    headers: {
      apikey: env.SUPABASE_ANON_KEY,
      Authorization: `Bearer ${token}`,
    },
  });
  if (!response.ok) throw requestError(401, "The session is invalid or expired.");

  const user = await response.json();
  if (typeof user.id !== "string") throw requestError(401, "The session is invalid.");
  return { user, token, supabaseUrl, isBackend: false };
}

async function getUserRole(userId, token, supabaseUrl, env) {
  if (!token) return "supplier"; // Verified by backend secret
  const url = new URL(`${supabaseUrl}/rest/v1/users_table`);
  url.searchParams.set("id", `eq.${userId}`);
  url.searchParams.set("select", "role");
  const response = await fetch(url, {
    headers: {
      apikey: env.SUPABASE_ANON_KEY,
      Authorization: `Bearer ${token}`,
    },
  });
  if (!response.ok) throw requestError(403, "Could not verify the account role.");
  const rows = await response.json();
  return Array.isArray(rows) ? rows[0]?.role : null;
}

async function handleMediaRequest(request, env) {
  if (request.method === "OPTIONS") {
    return new Response(null, { status: 204, headers: corsHeaders });
  }
  if (request.method !== "POST" && request.method !== "DELETE") {
    return jsonResponse({ error: "Method not allowed." }, 405);
  }
  if (!env.MEDIA_BUCKET) {
    return jsonResponse({ error: "The media bucket binding is not configured." }, 503);
  }

  try {
    const { user, token, supabaseUrl } = await getAuthenticatedUser(request, env);

    if (request.method === "DELETE") {
      let payload;
      try {
        payload = await request.json();
      } catch {
        throw requestError(400, "Request body must be valid JSON.");
      }

      const key = payload?.key;
      if (
        typeof key !== "string" ||
        key.split("/").length < 4 ||
        key.split("/").some((part) => part === "..") ||
        !/^users\/[^/]+\/(products|pdfs)\//.test(key)
      ) {
        throw requestError(400, "Invalid media key.");
      }

      if (!key.startsWith(`users/${user.id}/`)) {
        const role = await getUserRole(user.id, token, supabaseUrl, env);
        if (role !== "admin" || !key.includes("/products/")) {
          throw requestError(403, "You cannot delete this media.");
        }
      }

      await env.MEDIA_BUCKET.delete(key);
      return jsonResponse({ success: true });
    }

    const folder = request.headers.get("x-node-folder") || "products";
    if (folder !== "products" && folder !== "pdfs") {
      throw requestError(400, "Unsupported media folder.");
    }

    if (folder === "products") {
      const role = await getUserRole(user.id, token, supabaseUrl, env);
      if (role !== "supplier" && role !== "admin") {
        throw requestError(403, "Only suppliers and admins can upload product media.");
      }
    }

    const contentType = request.headers.get("Content-Type")?.split(";")[0].trim().toLowerCase();
    const extensions = {
      "image/jpeg": ".jpg",
      "image/png": ".png",
      "image/webp": ".webp",
      "image/avif": ".avif",
      "application/pdf": ".pdf",
    };
    if (!contentType || !extensions[contentType]) {
      throw requestError(415, "Unsupported media type.");
    }

    const declaredLength = Number(request.headers.get("Content-Length"));
    if (!Number.isSafeInteger(declaredLength) || declaredLength <= 0) {
      throw requestError(411, "Content-Length is required.");
    }
    if (declaredLength > MAX_MEDIA_BYTES) {
      throw requestError(413, "Media must be 12 MB or smaller.");
    }

    const bytes = await request.arrayBuffer();
    if (bytes.byteLength !== declaredLength || bytes.byteLength > MAX_MEDIA_BYTES) {
      throw requestError(400, "Uploaded media size is invalid.");
    }

    const key = `users/${user.id}/${folder}/Chart_${Date.now()}${extensions[contentType]}`;
    await env.MEDIA_BUCKET.put(key, bytes, {
      httpMetadata: { contentType },
      customMetadata: { uploadedBy: user.id },
    });

    const publicBase = (env.R2_PUBLIC_URL || new URL(request.url).origin).replace(/\/+$/, "");
    return jsonResponse({ success: true, key, url: `${publicBase}/${key}` });
  } catch (error) {
    const status = Number.isInteger(error?.status) ? error.status : 500;
    if (status === 500) console.error("Media operation failed:", error);
    return jsonResponse(
      { error: status === 500 ? "Media service is temporarily unavailable." : error.message },
      status
    );
  }
}

export default {
  async fetch(request, env) {
    const url = new URL(request.url);

    if (url.pathname === MEDIA_API_PATH) {
      return handleMediaRequest(request, env);
    }

    // Direct passthrough to R2 bucket
    return fetch(request);
  },
};
