ALTER TABLE "users" DROP CONSTRAINT IF EXISTS "users_default_clip_length_check";
ALTER TABLE "users" ADD CONSTRAINT "users_default_clip_length_check"
CHECK ("default_clip_length" IN ('auto', 'short', 'medium', 'long', 'extended', 'deep_dive'));

