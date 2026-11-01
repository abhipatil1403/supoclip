from pathlib import Path

path = Path("frontend/src/app/tasks/[id]/page.tsx")
content = path.read_text(encoding="utf-8")

old_block = """      } catch (err) {
        console.error("Error fetching task data:", err);
        if (!background) setError(err instanceof Error ? err.message : t("errors.load"));
        return false;
      }"""

new_block = """      } catch (err) {
        if (!background) {
          console.error("Error fetching task data:", err);
          const message = err instanceof Error ? err.message : String(err);
          if (message.includes("Failed to fetch")) {
            setError(
              "Unable to reach the server. If you have a browser VPN or proxy extension active (e.g. Urban VPN), please pause it for localhost or use an Incognito window."
            );
          } else {
            setError(message || t("errors.load"));
          }
        }
        return false;
      }"""

if old_block in content:
    content = content.replace(old_block, new_block, 1)
    path.write_text(content, encoding="utf-8")
    print("Updated page.tsx successfully.")
else:
    print("Target block not found in page.tsx.")
