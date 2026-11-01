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
    const timeoutId = setTimeout(() => controller.abort(), 4000);
    const res = await fetch(`${currentUrl}/health`, { signal: controller.signal });
    clearTimeout(timeoutId);
    isHealthy = res.ok;
  } catch {
    isHealthy = false;
  }

  if (isHealthy) {
    try {
      const controller = new AbortController();
      const timeoutId = setTimeout(() => controller.abort(), 4000);
      const res = await fetch(`${currentUrl}/health/worker`, { signal: controller.signal });
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

  url = url.trim().replace(/\/$/, "");
  if (!url.startsWith("http://") && !url.startsWith("https://")) {
    return NextResponse.json({ error: "URL must start with http:// or https://" }, { status: 400 });
  }

  // Probe the new URL
  let isHealthy = false;
  let workerHealthy = false;
  try {
    const controller = new AbortController();
    const timeoutId = setTimeout(() => controller.abort(), 5000);
    const res = await fetch(`${url}/health`, { signal: controller.signal });
    clearTimeout(timeoutId);
    isHealthy = res.ok;
  } catch (e) {
    return NextResponse.json(
      {
        error: `Could not connect to ${url}/health. Make sure your phone backend (uvicorn) and cloudflared tunnel are running.`,
      },
      { status: 400 },
    );
  }

  try {
    const controller = new AbortController();
    const timeoutId = setTimeout(() => controller.abort(), 5000);
    const res = await fetch(`${url}/health/worker`, { signal: controller.signal });
    clearTimeout(timeoutId);
    workerHealthy = res.ok;
  } catch {
    workerHealthy = false;
  }

  // Save to Neon PostgreSQL app_settings
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

  return NextResponse.json({
    success: true,
    url,
    healthy: isHealthy,
    workerHealthy,
    message: workerHealthy
      ? "Connected successfully to phone backend & worker!"
      : "Connected to phone backend (Worker process is offline; start it with: python -m src.worker_main)",
  });
}
