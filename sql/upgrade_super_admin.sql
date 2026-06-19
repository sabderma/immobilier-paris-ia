-- =========================================================
-- UPGRADE SUPER ADMIN
-- =========================================================
-- A executer une fois dans DBeaver ou psql sur la base utilisee
-- par l'application.
--
-- Objectif :
-- 1. Autoriser le role super_admin dans la table users.
-- 2. Donner ce role au compte admin@gmail.com.
--
-- Important : le backend bloque ensuite la suppression et le
-- changement de role de tout compte super_admin.
-- =========================================================

ALTER TABLE users
    DROP CONSTRAINT IF EXISTS chk_users_role;

ALTER TABLE users
    ADD CONSTRAINT chk_users_role
    CHECK (role IN ('user', 'admin', 'super_admin'));

UPDATE users
SET
    role = 'super_admin',
    updated_at = CURRENT_TIMESTAMP
WHERE LOWER(email) = LOWER('admin@gmail.com');
