INSTALL ducklake;
INSTALL postgres;

CREATE OR REPLACE SECRET s3_secret (
    TYPE s3,
    PROVIDER config,
    ENDPOINT getenv('S3_ENDPOINT'),
    KEY_ID getenv('S3_ACCESS_KEY'),
    SECRET getenv('S3_SECRET_KEY'),
    REGION getenv('S3_REGION'),
    URL_STYLE 'path',
    USE_SSL CAST(getenv('S3_USE_SSL') AS BOOLEAN)
);

CREATE OR REPLACE SECRET postgres_secret (
    TYPE postgres,
    HOST getenv('POSTGRES_HOST'),
    PORT 5432,
    DATABASE getenv('POSTGRES_DATABASE'),
    USER getenv('POSTGRES_USER'),
    PASSWORD getenv('POSTGRES_DB_PASSWORD')
);

-- OVERRIDE_DATA_PATH: DuckLake stores DATA_PATH in the catalog metadata at
-- creation time and errors if it doesn't match the current connection's
-- path (e.g. after a bucket rename). Since this script runs fresh on every
-- connection, always overriding is the correct behavior here -- it does
-- NOT change the value stored in the catalog, only the current session.
CREATE SECRET ducklake_secret (
    TYPE ducklake,
    METADATA_PATH '',
    DATA_PATH getenv('S3_DATA_PATH'),
    METADATA_PARAMETERS MAP {'TYPE': 'postgres', 'SECRET': 'postgres_secret'}
);

ATTACH 'ducklake:ducklake_secret' AS ducklake (OVERRIDE_DATA_PATH true);
USE ducklake;
SELECT 'DuckLake is ready for environment: ' || getenv('POSTGRES_DATABASE') as status;
