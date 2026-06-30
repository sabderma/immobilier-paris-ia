-- =========================================================
-- UPGRADE SUPER ADMIN
-- =========================================================
-- A executer une fois dans DBeaver ou psql sur la base utilisee
-- par l'application.
--
-- Objectif :
-- 1. Autoriser le role super_admin dans la table users.
-- 2. Laisser le backend creer ou reparer le compte super admin
--    depuis un compte deja present en base et SUPER_ADMIN_EMAIL.
--
-- Important : le backend bloque ensuite la suppression et le
-- changement de role de tout compte super_admin.
-- =========================================================

ALTER TABLE users
    DROP CONSTRAINT IF EXISTS chk_users_role;

ALTER TABLE users
    ADD CONSTRAINT chk_users_role
    CHECK (role IN ('user', 'admin', 'super_admin'));

-- Le compte super admin n'est pas fixe ici avec un email ecrit en dur.
-- Le compte doit exister dans la table users avec son mot de passe hache.
-- Au demarrage, l'API peut lui donner le role super_admin avec SUPER_ADMIN_EMAIL.
