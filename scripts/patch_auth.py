from pathlib import Path

p = Path("frontend/src/lib/auth.ts")
t = p.read_text(encoding="utf-8")

old = "export const auth = betterAuth({"
new = """export const auth = betterAuth({
  baseURL: process.env.BETTER_AUTH_URL || "http://localhost:3107",
  basePath: "/api/auth","""

if old in t and "baseURL:" not in t:
    t = t.replace(old, new, 1)
    p.write_text(t, encoding="utf-8")
    print("Added baseURL and basePath to auth.ts successfully.")
else:
    print("Already present or pattern not found.")

