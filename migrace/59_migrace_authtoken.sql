-- Create model Token
--
CREATE TABLE "authtoken_token" ("key" varchar(40) NOT NULL PRIMARY KEY, "created" timestamp with time zone NOT NULL, "user_id" integer NOT NULL UNIQUE);
ALTER TABLE "authtoken_token"
ADD CONSTRAINT "authtoken_token_user_id_35299eff_fk_auth_user_id" FOREIGN KEY ("user_id") REFERENCES "auth_user" ("id") DEFERRABLE INITIALLY DEFERRED;
CREATE INDEX "authtoken_token_key_10f0b77e_like" ON "authtoken_token" ("key" varchar_pattern_ops);