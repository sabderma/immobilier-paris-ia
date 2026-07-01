#!/bin/sh
set -eu

: "${DB_HOST:?DB_HOST est obligatoire}"
: "${DB_PORT:?DB_PORT est obligatoire}"
: "${DB_USER:?DB_USER est obligatoire}"
: "${DB_PASSWORD:?DB_PASSWORD est obligatoire}"
: "${DB_NAME:?DB_NAME est obligatoire}"

MIGRATIONS_DIR="${MIGRATIONS_DIR:-/migrations}"
export PGPASSWORD="$DB_PASSWORD"

echo "Attente de PostgreSQL sur ${DB_HOST}:${DB_PORT}..."
until pg_isready -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER" -d "$DB_NAME" >/dev/null 2>&1; do
    sleep 2
done

echo "PostgreSQL est pret. Verification des migrations SQL..."
psql -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER" -d "$DB_NAME" -v ON_ERROR_STOP=1 <<'SQL'
CREATE TABLE IF NOT EXISTS public.schema_migrations (
    filename TEXT PRIMARY KEY,
    applied_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP
);
SQL

found_migration=0

for migration_file in "$MIGRATIONS_DIR"/*.sql; do
    if [ ! -f "$migration_file" ]; then
        continue
    fi

    found_migration=1
    migration_name="$(basename "$migration_file")"
    migration_name_sql="$(printf "%s" "$migration_name" | sed "s/'/''/g")"
    already_applied="$(
        psql -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER" -d "$DB_NAME" \
            -tAc "SELECT EXISTS (SELECT 1 FROM public.schema_migrations WHERE filename = '$migration_name_sql');"
    )"

    if [ "$already_applied" = "t" ]; then
        echo "Migration deja appliquee : $migration_name"
        continue
    fi

    echo "Application de la migration : $migration_name"
    psql -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER" -d "$DB_NAME" \
        -v ON_ERROR_STOP=1 \
        --single-transaction \
        -f "$migration_file" \
        -c "INSERT INTO public.schema_migrations (filename) VALUES ('$migration_name_sql');"
done

if [ "$found_migration" -eq 0 ]; then
    echo "Aucune migration SQL trouvee dans $MIGRATIONS_DIR."
fi

echo "Migrations SQL terminees."
