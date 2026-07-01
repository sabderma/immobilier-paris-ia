CREATE UNIQUE INDEX IF NOT EXISTS users_email_unique
    ON users (LOWER(email));

CREATE INDEX IF NOT EXISTS idx_predictions_user_created_at
    ON predictions (user_id, created_at DESC);

CREATE INDEX IF NOT EXISTS idx_exact_address_user_created_at
    ON exact_address_history (user_id, created_at DESC);

CREATE INDEX IF NOT EXISTS idx_golden_scraping_localisation
    ON golden_data_scraping (localisation);

CREATE INDEX IF NOT EXISTS idx_golden_scraping_source
    ON golden_data_scraping (source);

CREATE INDEX IF NOT EXISTS idx_golden_scraping_surface
    ON golden_data_scraping (surface);

CREATE INDEX IF NOT EXISTS idx_golden_scraping_pieces
    ON golden_data_scraping (nb_pieces);

CREATE INDEX IF NOT EXISTS idx_dvf_arrondissement
    ON dvf_paris_appartements (arrondissement);

CREATE INDEX IF NOT EXISTS idx_dvf_annee_vente
    ON dvf_paris_appartements (annee_vente);

CREATE INDEX IF NOT EXISTS idx_dvf_mois_vente
    ON dvf_paris_appartements (mois_vente);

CREATE INDEX IF NOT EXISTS idx_dvf_code_postal
    ON dvf_paris_appartements (code_postal);

CREATE INDEX IF NOT EXISTS idx_dvf_nombre_pieces
    ON dvf_paris_appartements (nombre_pieces_principales);

CREATE INDEX IF NOT EXISTS idx_dvf_surface
    ON dvf_paris_appartements (surface_reelle_bati);

CREATE INDEX IF NOT EXISTS idx_dvf_prix
    ON dvf_paris_appartements (valeur_fonciere);

CREATE INDEX IF NOT EXISTS idx_dvf_prix_m2
    ON dvf_paris_appartements (prix_m2);

CREATE INDEX IF NOT EXISTS idx_dvf_date_mutation_id_mutation
    ON dvf_paris_appartements (date_mutation DESC, id_mutation DESC);

CREATE INDEX IF NOT EXISTS idx_dvf_arrondissement_date
    ON dvf_paris_appartements (arrondissement, date_mutation DESC, id_mutation DESC);

CREATE INDEX IF NOT EXISTS idx_dvf_annee_date
    ON dvf_paris_appartements (annee_vente, date_mutation DESC, id_mutation DESC);

CREATE INDEX IF NOT EXISTS idx_dvf_arrondissement_annee
    ON dvf_paris_appartements (arrondissement, annee_vente);

CREATE INDEX IF NOT EXISTS idx_dvf_latitude_longitude
    ON dvf_paris_appartements (latitude, longitude);
