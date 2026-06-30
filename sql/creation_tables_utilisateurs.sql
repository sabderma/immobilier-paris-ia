-- =========================================================
-- TABLES UTILISATEURS ET HISTORIQUES
-- =========================================================
-- Ce script peut etre execute dans DBeaver sans supprimer les
-- donnees deja presentes dans les tables DVF et scraping.
-- Il sert aussi de support pour le document RGPD du bloc 1.
--
-- Important : password_hash doit contenir un mot de passe hache
-- par le backend avec Argon2 ou bcrypt, jamais le mot de passe brut.
-- =========================================================


-- Comptes pouvant se connecter a l'application.
CREATE TABLE IF NOT EXISTS users (
    id BIGSERIAL PRIMARY KEY,
    email VARCHAR(255) NOT NULL,
    password_hash TEXT NOT NULL,
    first_name VARCHAR(100),
    last_name VARCHAR(100),
    role VARCHAR(20) NOT NULL DEFAULT 'user',
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT chk_users_email_not_empty
        CHECK (BTRIM(email) <> ''),
    CONSTRAINT chk_users_password_hash_not_empty
        CHECK (BTRIM(password_hash) <> ''),
    CONSTRAINT chk_users_role
        CHECK (role IN ('user', 'admin', 'super_admin'))
);

-- Deux variantes de casse d'une meme adresse email ne peuvent pas
-- creer deux comptes differents.
CREATE UNIQUE INDEX IF NOT EXISTS users_email_unique
    ON users (LOWER(email));

-- Mise a jour utile si la table users existait deja avec seulement user/admin.
ALTER TABLE users
    DROP CONSTRAINT IF EXISTS chk_users_role;

ALTER TABLE users
    ADD CONSTRAINT chk_users_role
    CHECK (role IN ('user', 'admin', 'super_admin'));


-- Historique des predictions lancees depuis le formulaire :
-- surface, nombre de pieces, arrondissement et prix predit.
CREATE TABLE IF NOT EXISTS predictions (
    id BIGSERIAL PRIMARY KEY,
    user_id BIGINT NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    surface NUMERIC(10,2) NOT NULL,
    nb_pieces INTEGER NOT NULL,
    arrondissement INTEGER NOT NULL,
    predicted_price NUMERIC(14,2) NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT chk_predictions_surface
        CHECK (surface > 0),
    CONSTRAINT chk_predictions_nb_pieces
        CHECK (nb_pieces > 0),
    CONSTRAINT chk_predictions_arrondissement
        CHECK (arrondissement BETWEEN 1 AND 20),
    CONSTRAINT chk_predictions_price
        CHECK (predicted_price >= 0)
);

-- Index pour retrouver rapidement les predictions d'un utilisateur.
CREATE INDEX IF NOT EXISTS idx_predictions_user_created_at
    ON predictions (user_id, created_at DESC);


-- Historique des adresses validees dans "Localiser votre adresse exacte".
CREATE TABLE IF NOT EXISTS exact_address_history (
    id BIGSERIAL PRIMARY KEY,
    user_id BIGINT NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    address TEXT NOT NULL,
    latitude NUMERIC(9,6) NOT NULL,
    longitude NUMERIC(9,6) NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT chk_exact_address_not_empty
        CHECK (BTRIM(address) <> ''),
    CONSTRAINT chk_exact_address_latitude
        CHECK (latitude BETWEEN -90 AND 90),
    CONSTRAINT chk_exact_address_longitude
        CHECK (longitude BETWEEN -180 AND 180)
);

-- Index pour retrouver rapidement les adresses recentes d'un utilisateur.
CREATE INDEX IF NOT EXISTS idx_exact_address_user_created_at
    ON exact_address_history (user_id, created_at DESC);


-- Le super admin n'est pas fixe ici avec un email ecrit en dur.
-- Le compte doit exister dans la table users avec son mot de passe hache.
-- Au demarrage, l'API peut lui donner le role super_admin avec SUPER_ADMIN_EMAIL.
