from pathlib import Path

p = Path("frontend/src/components/auth/sign-in.tsx")
content = p.read_text(encoding="utf-8")

old_p = 'type="password"\n            placeholder={t("signIn.password")}'
new_p = 'type="password"\n            autoComplete="current-password"\n            placeholder={t("signIn.password")}'

old_e = 'type="email"\n            placeholder={t("signIn.email")}'
new_e = 'type="email"\n            autoComplete="email"\n            placeholder={t("signIn.email")}'

content = content.replace(old_p, new_p).replace(old_e, new_e)
p.write_text(content, encoding="utf-8")
print("Updated sign-in.tsx autocomplete attributes.")

