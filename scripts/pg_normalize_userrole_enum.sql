-- Normalise les valeurs de l'ENUM Postgres "userrole" en minuscules et
-- aligne la valeur par défaut de users.role sur 'agent'.
-- Idempotent: chaque renommage est conditionnel, sans effet si déjà normalisé.

BEGIN;

-- Renommer conditionnellement les libellés ENUM en minuscules si nécessaire
DO $$
DECLARE
    t_oid oid;
BEGIN
    SELECT typ.oid INTO t_oid
    FROM pg_type typ
    WHERE typ.typname = 'userrole' AND typ.typtype = 'e';

    IF t_oid IS NULL THEN
        RAISE NOTICE 'Type "userrole" introuvable; opération ignorée.';
        RETURN;
    END IF;

    -- ADMIN -> admin
    PERFORM 1 FROM pg_enum e WHERE e.enumtypid = t_oid AND e.enumlabel = 'ADMIN';
    IF FOUND THEN
        IF NOT EXISTS (
            SELECT 1 FROM pg_enum e WHERE e.enumtypid = t_oid AND e.enumlabel = 'admin'
        ) THEN
            EXECUTE 'ALTER TYPE userrole RENAME VALUE ''ADMIN'' TO ''admin''';
        END IF;
    END IF;

    -- AGENT -> agent
    PERFORM 1 FROM pg_enum e WHERE e.enumtypid = t_oid AND e.enumlabel = 'AGENT';
    IF FOUND THEN
        IF NOT EXISTS (
            SELECT 1 FROM pg_enum e WHERE e.enumtypid = t_oid AND e.enumlabel = 'agent'
        ) THEN
            EXECUTE 'ALTER TYPE userrole RENAME VALUE ''AGENT'' TO ''agent''';
        END IF;
    END IF;

    -- MANAGER -> manager
    PERFORM 1 FROM pg_enum e WHERE e.enumtypid = t_oid AND e.enumlabel = 'MANAGER';
    IF FOUND THEN
        IF NOT EXISTS (
            SELECT 1 FROM pg_enum e WHERE e.enumtypid = t_oid AND e.enumlabel = 'manager'
        ) THEN
            EXECUTE 'ALTER TYPE userrole RENAME VALUE ''MANAGER'' TO ''manager''';
        END IF;
    END IF;
END $$;

-- Aligner le DEFAULT de users.role sur 'agent'::userrole si la colonne existe
DO $$
BEGIN
    IF EXISTS (
        SELECT 1 FROM information_schema.columns
        WHERE table_schema IN ('public')
          AND table_name = 'users'
          AND column_name = 'role'
    ) THEN
        BEGIN
            EXECUTE 'ALTER TABLE public.users ALTER COLUMN role SET DEFAULT ''agent''::userrole';
        EXCEPTION WHEN undefined_table THEN
            -- Ignorer si la table n'existe pas dans ce schéma
        END;
    END IF;
END $$;

COMMIT;

-- Utilisation (exemples):
--   psql "$DATABASE_URL" -f scripts/pg_normalize_userrole_enum.sql
--   PGPASSWORD=... psql -h <host> -U <user> -d <db> -f scripts/pg_normalize_userrole_enum.sql
