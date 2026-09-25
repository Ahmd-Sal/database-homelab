-- 1. Create a Group Role
CREATE ROLE app_users;
GRANT CONNECT ON DATABASE app_db TO app_users;
GRANT USAGE ON SCHEMA public TO app_users;

-- Table privileges 
GRANT SELECT, INSERT, UPDATE, DELETE
  ON ALL TABLES IN SCHEMA public TO app_users;

ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT SELECT, INSERT, UPDATE, DELETE
  ON TABLES TO app_users;

-- Sequence privileges for schema public
GRANT USAGE, SELECT
  ON ALL SEQUENCES IN SCHEMA public TO app_users;

ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT USAGE, SELECT
  ON SEQUENCES TO app_users;

-- 2. Create a user and assign the role
CREATE USER app_user;
GRANT app_users TO app_user;

