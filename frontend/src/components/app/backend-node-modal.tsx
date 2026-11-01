"use client";

import { useState, useEffect } from "react";
import { Smartphone, CheckCircle2, AlertCircle, Loader2, RefreshCw } from "lucide-react";
import { toast } from "sonner";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
} from "@/components/ui/dialog";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";

export function MobileNodeModal({
  trigger,
  compact = false,
}: {
  trigger?: React.ReactNode;
  compact?: boolean;
}) {
  const [open, setOpen] = useState(false);
  const [url, setUrl] = useState("");
  const [loading, setLoading] = useState(false);
  const [saving, setSaving] = useState(false);
  const [status, setStatus] = useState<{
    healthy: boolean;
    workerHealthy: boolean;
    currentUrl: string;
  } | null>(null);

  const fetchStatus = async () => {
    setLoading(true);
    try {
      const res = await fetch("/api/backend-url");
      if (res.ok) {
        const data = await res.json();
        setUrl(data.url || "");
        setStatus({
          healthy: Boolean(data.healthy),
          workerHealthy: Boolean(data.workerHealthy),
          currentUrl: data.url || "",
        });
      }
    } catch {
      // ignore
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    if (open) {
      fetchStatus();
    }
  }, [open]);

  // Initial check on mount to get status badge state
  useEffect(() => {
    fetch("/api/backend-url")
      .then((res) => (res.ok ? res.json() : null))
      .then((data) => {
        if (data) {
          setStatus({
            healthy: Boolean(data.healthy),
            workerHealthy: Boolean(data.workerHealthy),
            currentUrl: data.url || "",
          });
        }
      })
      .catch(() => {});
  }, []);

  const handleSave = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!url.trim()) return;

    setSaving(true);
    try {
      const res = await fetch("/api/backend-url", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ url: url.trim() }),
      });
      const data = await res.json();
      if (!res.ok) {
        toast.error(data.error || "Failed to connect to phone tunnel");
        return;
      }

      setStatus({
        healthy: data.healthy,
        workerHealthy: data.workerHealthy,
        currentUrl: data.url,
      });

      if (data.workerHealthy) {
        toast.success(data.message || "Connected to phone backend & worker!");
        setOpen(false);
      } else {
        toast.warning(data.message || "Connected to phone backend, but worker is offline!");
      }
    } catch (err) {
      toast.error("Network error while connecting to phone tunnel");
    } finally {
      setSaving(false);
    }
  };

  const isOnline = status?.healthy;
  const isWorkerOnline = status?.workerHealthy;

  return (
    <Dialog open={open} onOpenChange={setOpen}>
      <DialogTrigger asChild>
        {trigger ? (
          trigger
        ) : (
          <button
            type="button"
            className={
              compact
                ? "flex size-8 items-center justify-center rounded-lg border border-sidebar-border bg-sidebar hover:bg-accent transition-colors"
                : "flex h-9 w-full items-center justify-between rounded-lg border border-sidebar-border bg-background px-2.5 text-xs font-medium text-muted-foreground hover:text-foreground transition-colors"
            }
            title="Mobile Processing Node"
          >
            <div className="flex items-center gap-2">
              <Smartphone className="size-4 shrink-0 text-brand" />
              {!compact && <span>Phone Engine</span>}
            </div>
            <div className="flex items-center gap-1.5">
              <span
                className={`size-2 rounded-full ${
                  isWorkerOnline ? "bg-emerald-500 animate-pulse" : isOnline ? "bg-amber-500" : "bg-zinc-400"
                }`}
              />
              {!compact && (
                <span className="text-[10px] uppercase tracking-wider text-muted-foreground">
                  {isWorkerOnline ? "24GB Ready" : isOnline ? "Worker Off" : "Connect"}
                </span>
              )}
            </div>
          </button>
        )}
      </DialogTrigger>

      <DialogContent className="sm:max-w-md">
        <DialogHeader>
          <DialogTitle className="flex items-center gap-2 text-lg">
            <Smartphone className="size-5 text-brand" />
            Snapdragon Hardware Node
          </DialogTitle>
          <DialogDescription>
            Connect your 24GB RAM Android phone running Termux. Enter your Cloudflare Tunnel URL below to process videos directly on your phone hardware.
          </DialogDescription>
        </DialogHeader>

        <div className="space-y-4 py-2">
          {/* Status block */}
          <div className="flex flex-col gap-2 rounded-lg border bg-muted/40 p-3 text-xs">
            <div className="flex items-center justify-between">
              <span className="font-semibold text-foreground">Backend Service:</span>
              <div className="flex items-center gap-1.5">
                {isOnline ? (
                  <>
                    <CheckCircle2 className="size-3.5 text-emerald-500" />
                    <span className="font-medium text-emerald-600 dark:text-emerald-400">Online</span>
                  </>
                ) : (
                  <>
                    <AlertCircle className="size-3.5 text-rose-500" />
                    <span className="font-medium text-rose-600 dark:text-rose-400">Offline / Unreachable</span>
                  </>
                )}
              </div>
            </div>

            <div className="flex items-center justify-between">
              <span className="font-semibold text-foreground">Arq Worker (Rendering):</span>
              <div className="flex items-center gap-1.5">
                {isWorkerOnline ? (
                  <>
                    <CheckCircle2 className="size-3.5 text-emerald-500" />
                    <span className="font-medium text-emerald-600 dark:text-emerald-400">Active</span>
                  </>
                ) : (
                  <>
                    <AlertCircle className="size-3.5 text-amber-500" />
                    <span className="font-medium text-amber-600 dark:text-amber-400">
                      {isOnline ? "Stopped (.venv/bin/python -m src.worker_main)" : "Waiting for backend"}
                    </span>
                  </>
                )}
              </div>
            </div>

            {status?.currentUrl && (
              <div className="mt-1 border-t pt-1.5 text-[11px] text-muted-foreground break-all">
                <span className="font-mono text-foreground/80">{status.currentUrl}</span>
              </div>
            )}
          </div>

          <form onSubmit={handleSave} className="space-y-3">
            <div className="space-y-1.5">
              <label htmlFor="tunnel-url" className="text-xs font-semibold text-foreground">
                Cloudflare Tunnel URL
              </label>
              <Input
                id="tunnel-url"
                type="url"
                value={url}
                onChange={(e) => setUrl(e.target.value)}
                placeholder="https://xxxx-xxxx.trycloudflare.com"
                required
                className="font-mono text-xs"
              />
              <p className="text-[11px] text-muted-foreground">
                Run <code className="rounded bg-muted px-1 py-0.5 font-mono text-[10px]">cloudflared tunnel --url http://localhost:8000</code> in Termux and paste the generated link here.
              </p>
            </div>

            <div className="flex items-center justify-between pt-2">
              <Button
                type="button"
                variant="outline"
                size="sm"
                onClick={fetchStatus}
                disabled={loading}
                className="text-xs"
              >
                <RefreshCw className={`size-3.5 mr-1 ${loading ? "animate-spin" : ""}`} />
                Test Probe
              </Button>

              <Button type="submit" size="sm" disabled={saving || !url.trim()} className="text-xs">
                {saving ? (
                  <>
                    <Loader2 className="size-3.5 mr-1 animate-spin" />
                    Connecting...
                  </>
                ) : (
                  "Save & Connect"
                )}
              </Button>
            </div>
          </form>
        </div>
      </DialogContent>
    </Dialog>
  );
}

