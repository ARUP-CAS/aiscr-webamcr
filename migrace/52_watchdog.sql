--
-- Create model Watchdog
--
CREATE TABLE "watchdog_watchdog" ("id" bigserial NOT NULL PRIMARY KEY, "user_id" integer NOT NULL, "object_id" integer NOT NULL CHECK ("object_id" >= 0), "content_type_id" integer, "created_at" timestamp with time zone NOT NULL);
--
-- Create index watchdog_wa_content_62491d_idx on field(s) content_type, object_id of model watchdog
--
CREATE INDEX "watchdog_wa_content_62491d_idx" ON "watchdog_watchdog" ("content_type_id", "object_id");
ALTER TABLE "watchdog_watchdog" ADD CONSTRAINT "watchdog_watchdog_user_id_c1145180_fk_auth_user_id" FOREIGN KEY ("user_id") REFERENCES "auth_user" ("id") DEFERRABLE INITIALLY DEFERRED;
CREATE INDEX "watchdog_watchdog_user_id_c1145180" ON "watchdog_watchdog" ("user_id");
