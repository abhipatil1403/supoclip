import { randomUUID } from "crypto";

import prisma from "@/lib/prisma";
import { buildBackendAuthHeaders } from "@/lib/backend-auth";

export const DEFAULT_FORWARDED_HEADERS = [
  "accept-ranges",
  "cache-control",
  "content-length",
  "content-range",
  "content-disposition",
  "content-type",
  "etag",
  "last-modified",
  "location",
  "x-trace-id",
] as const;

let memoryCachedUrl: string | null = null;
let memoryCacheExpiry = 0;

export async function getBackendApiBaseUrl(): Promise<string> {
  const now = Date.now();
  if (memoryCachedUrl && now < memoryCacheExpiry) {
    return memoryCachedUrl;
  }

  try {
    const setting = await prisma.appSetting.findUnique({
      where: { setting_key: "mobile_backend_url" },
    });
    if (setting?.encrypted_value?.trim()) {
      memoryCachedUrl = setting.encrypted_value.trim().replace(/\/$/, "");
      memoryCacheExpiry = now + 10000;
      return memoryCachedUrl;
    }
  } catch (err) {
    console.warn("Failed to fetch mobile_backend_url from DB:", err);
  }

  const fallback =
    process.env.BACKEND_INTERNAL_URL ||
    process.env.NEXT_PUBLIC_API_URL ||
    "https://chan-dna-engineering-earlier.trycloudflare.com";

  memoryCachedUrl = fallback.replace(/\/$/, "");
  memoryCacheExpiry = now + 10000;
  return memoryCachedUrl;
}

export function setMemoryCachedBackendUrl(url: string) {
  memoryCachedUrl = url.replace(/\/$/, "");
  memoryCacheExpiry = Date.now() + 60000;
}

export async function buildBackendUrl(path: string): Promise<string> {
  const baseUrl = await getBackendApiBaseUrl();
  return `${baseUrl}${path.startsWith("/") ? path : `/${path}`}`;
}

const TRACE_ID_PATTERN = /^[A-Za-z0-9._-]{8,128}$/;

/**
 * Forward the browser's `x-trace-id` (set per request in `lib/trace-fetch.ts`)
 * so backend logs and PostHog errors share an id. Outside a request, or when
 * the header is missing or malformed, a fresh id is used.
 */
export async function backendTraceHeaders(): Promise<Record<string, string>> {
  let incoming: string | null = null;
  try {
    const { headers } = await import("next/headers");
    incoming = (await headers()).get("x-trace-id");
  } catch {
    // Not inside a request scope (scripts, tests).
  }
  return { "x-trace-id": incoming && TRACE_ID_PATTERN.test(incoming) ? incoming : randomUUID() };
}

export async function fetchBackend(
  path: string,
  init: RequestInit & {
    userId?: string;
    extraHeaders?: HeadersInit;
  } = {},
) {
  const { userId, extraHeaders, headers, ...rest } = init;
  const targetUrl = await buildBackendUrl(path);

  return fetch(targetUrl, {
    redirect: "manual",
    ...rest,
    headers: {
      ...(await backendTraceHeaders()),
      ...(userId ? buildBackendAuthHeaders(userId) : {}),
      ...(headers ?? {}),
      ...(extraHeaders ?? {}),
    },
  });
}

export function createProxyResponse(
  upstream: Response,
  options: {
    cacheControl?: string;
    extraHeaders?: HeadersInit;
  } = {},
) {
  const headers = new Headers();

  for (const header of DEFAULT_FORWARDED_HEADERS) {
    const value = upstream.headers.get(header);
    if (value !== null) {
      headers.set(header, value);
    }
  }

  if (options.cacheControl) {
    headers.set("cache-control", options.cacheControl);
  }

  if (options.extraHeaders) {
    const extra = new Headers(options.extraHeaders);
    extra.forEach((value, key) => {
      headers.set(key, value);
    });
  }

  return new Response(upstream.body, {
    status: upstream.status,
    headers,
  });
}
