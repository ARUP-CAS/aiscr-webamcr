BEGIN;
--
-- Create model Group
--
CREATE TABLE "auth_group" ("id" serial NOT NULL PRIMARY KEY, "name" varchar(80) NOT NULL UNIQUE);
--
-- Create model User
--
CREATE TABLE "auth_user" ("id" serial NOT NULL PRIMARY KEY, "password" varchar(128) NOT NULL, "last_login" timestamp with time zone NOT NULL, "is_superuser" boolean NOT NULL, "username" varchar(30) NOT NULL UNIQUE, "first_name" varchar(30) NOT NULL, "last_name" varchar(30) NOT NULL, "email" varchar(75) NOT NULL, "is_staff" boolean NOT NULL, "is_active" boolean NOT NULL, "date_joined" timestamp with time zone NOT NULL);
CREATE TABLE "auth_user_groups" ("id" serial NOT NULL PRIMARY KEY, "user_id" integer NOT NULL, "group_id" integer NOT NULL);
CREATE INDEX "auth_group_name_a6ea08ec_like" ON "auth_group" ("name" varchar_pattern_ops);
CREATE INDEX "auth_user_username_6821ab7c_like" ON "auth_user" ("username" varchar_pattern_ops);
ALTER TABLE "auth_user_groups" ADD CONSTRAINT "auth_user_groups_user_id_group_id_94350c0c_uniq" UNIQUE ("user_id", "group_id");
ALTER TABLE "auth_user_groups" ADD CONSTRAINT "auth_user_groups_user_id_6a12ed8b_fk_auth_user_id" FOREIGN KEY ("user_id") REFERENCES "auth_user" ("id") DEFERRABLE INITIALLY DEFERRED;
ALTER TABLE "auth_user_groups" ADD CONSTRAINT "auth_user_groups_group_id_97559544_fk_auth_group_id" FOREIGN KEY ("group_id") REFERENCES "auth_group" ("id") DEFERRABLE INITIALLY DEFERRED;
CREATE INDEX "auth_user_groups_user_id_6a12ed8b" ON "auth_user_groups" ("user_id");
CREATE INDEX "auth_user_groups_group_id_97559544" ON "auth_user_groups" ("group_id");
COMMIT;
BEGIN;
--
-- Alter field email on user
--
ALTER TABLE "auth_user" ALTER COLUMN "email" TYPE varchar(254);
COMMIT;
BEGIN;
--
-- Alter field last_login on user
--
ALTER TABLE "auth_user" ALTER COLUMN "last_login" DROP NOT NULL;
COMMIT;
BEGIN;
--
-- Alter field username on user
--
ALTER TABLE "auth_user" ALTER COLUMN "username" TYPE varchar(150);
COMMIT;
BEGIN;
--
-- Alter field last_name on user
--
ALTER TABLE "auth_user" ALTER COLUMN "last_name" TYPE varchar(150);
COMMIT;
BEGIN;
--
-- Alter field name on group
--
ALTER TABLE "auth_group" ALTER COLUMN "name" TYPE varchar(150);
COMMIT;
BEGIN;
--
-- Alter field first_name on user
--
ALTER TABLE "auth_user" ALTER COLUMN "first_name" TYPE varchar(150);
COMMIT;
