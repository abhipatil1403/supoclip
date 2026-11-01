import { headers } from "next/headers";
import { NextResponse } from "next/server";

import { auth } from "@/lib/auth";
import prisma from "@/lib/prisma";
import { getBackendApiBaseUrl, setMemoryCachedBackendUrl } from "@/server/backend-api";

export async function GET() {
  const session = await auth.api.getSession({ headers: await headers() });
  if (!session?.user?.id) {
    return NextResponse.json({ error: "Unauthorized" }, { status: 401 });
  }

  const currentUrl = await getBackendApiBaseUrl();
  let isHealthy = false;
  let workerHealthy = false;

  try {
    const controller = new AbortController();
    const timeoutId = setTimeout(() => controller.abort(), 6000);
    const res = await fetch(`${currentUrl}/health`, {
      signal: controller.signal,
      cache: "no-store",
    });
    clearTimeout(timeoutId);
    isHealthy = res.ok;
  } catch {
    isHealthy = false;
  }

  if (isHealthy) {
    try {
      const controller = new AbortController();
      const timeoutId = setTimeout(() => controller.abort(), 6000);
      const res = await fetch(`${currentUrl}/health/worker`, {
        signal: controller.signal,
        cache: "no-store",
      });
      clearTimeout(timeoutId);
      workerHealthy = res.ok;
    } catch {
      workerHealthy = false;
    }
  }

  return NextResponse.json({
    url: currentUrl,
    healthy: isHealthy,
    workerHealthy,
  });
}

export async function POST(request: Request) {
  const session = await auth.api.getSession({ headers: await headers() });
  if (!session?.user?.id) {
    return NextResponse.json({ error: "Unauthorized" }, { status: 401 });
  }

  const body = await request.json().catch(() => ({}));
  let { url } = body;
  if (!url || typeof url !== "string") {
    return NextResponse.json({ error: "A valid URL string is required" }, { status: 400 });
  }

  // Clean and normalize URL
  url = url.trim();
  url = url.replace(/\/health\/?$/, "").replace(/\/$/, "");

  // Auto-prepend https:// if omitted by user
  if (!url.startsWith("http://") && !url.startsWith("https://")) {
    url = `https://${url}`;
  }

  // Probe the URL with a 12-second timeout for international round-trips
  let isHealthy = false;
  let workerHealthy = false;
  let probeError: string | null = null;

  try {
    const controller = new AbortController();
    const timeoutId = setTimeout(() => controller.abort(), 12000);
    const res = await fetch(`${url}/health`, {
      signal: controller.signal,
      headers: { "User-Agent": "SupoClip-HealthCheck/1.0" },
      cache: "no-store",
    });
    clearTimeout(timeoutId);
    isHealthy = res.ok;
    if (!res.ok) {
      probeError = `Health endpoint returned status ${res.status}`;
    }
  } catch (e: unknown) {
    const err = e as { name?: string; message?: string };
    probeError = err?.name === "AbortError" ? "Connection probe timed out after 12s" : (err?.message || "Connection refused");
  }

  if (isHealthy) {
    try {
      const controller = new AbortController();
      const timeoutId = setTimeout(() => controller.abort(), 6000);
      const res = await fetch(`${url}/health/worker`, {
        signal: controller.signal,
        cache: "no-store",
      });
      clearTimeout(timeoutId);
      workerHealthy = res.ok;
    } catch {
      workerHealthy = false;
    }
  }

  // Save to Neon PostgreSQL app_settings (regardless of transient probe status so user isn't blocked)
  await prisma.appSetting.upsert({
    where: { setting_key: "mobile_backend_url" },
    create: {
      setting_key: "mobile_backend_url",
      encrypted_value: url,
      updated_by: session.user.id,
    },
    update: {
      encrypted_value: url,
      updated_by: session.user.id,
    },
  });

  setMemoryCachedBackendUrl(url);

  if (!isHealthy) {
    return NextResponse.json({
      success: true,
      url,
      healthy: false,
      workerHealthy: false,
      warning: `Saved ${url}, but probe could not verify: ${probeError}. Ensure your phone uvicorn & cloudflared are running.`,
    });
  }

  return NextResponse.json({
    success: true,
    url,
    healthy: isHealthy,
    workerHealthy,
    message: workerHealthy
      ? "Connected successfully to phone backend & 24GB worker!"
      : "Connected to phone backend (Worker process is offline; start it with: python -m src.worker_main)",
  });
}
