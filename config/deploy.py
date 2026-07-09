from pyinfra.operations import apt
from os import getenv
from tasks.postgres import setup_postgres
from tasks.duckdb import setup_duckdb
from tasks.secure import setup_firewall, persist_firewall_config


def catalog_config(environment: str, dataset: str) -> dict:
    """Build the role/database/password for one (environment, dataset)
    catalog, e.g. (development, measurements) or (preproduction, calibration).

    The Postgres ROLE is shared across every dataset within an environment
    (by design -- see project decision on calibration vs measurements
    isolation): 'development' uses its legacy role/database names, other
    environments use 'ducklake_<environment>'. Only the DATABASE name
    varies by dataset, with 'measurements' kept as the bare/legacy name
    (no suffix) so existing deployments are unaffected, and every other
    dataset getting a '_<dataset>' suffix.
    """
    if environment == "development":
        role = "ducklake"
        base_database = "ducklake_catalog"
    else:
        role = f"ducklake_{environment}"
        base_database = f"ducklake_catalog_{environment}"

    database = (
        base_database if dataset == "measurements" else f"{base_database}_{dataset}"
    )

    # Password is per-environment only (shared across datasets in that
    # environment), matching the shared-role decision above.
    password_var = f"POSTGRES_DB_PASSWORD_{environment.upper()}"
    password = getenv(password_var)
    if not password:
        raise ValueError(
            f"Missing required env var: {password_var} "
            f"(needed for environment '{environment}', dataset '{dataset}')"
        )

    return {"role": role, "database": database, "password": password}


def deploy():
    # Which (environment, dataset) catalogs this server hosts, e.g.:
    #   "development:measurements,development:calibration,preproduction:measurements,preproduction:calibration"
    #   "production:measurements,production:calibration"
    target_catalogs_raw = getenv("TARGET_CATALOGS", "")
    pairs = [p.strip() for p in target_catalogs_raw.split(",") if p.strip()]
    if not pairs:
        raise ValueError(
            "TARGET_CATALOGS env var must be set, e.g. "
            "'development:measurements,development:calibration'"
        )

    catalogs = []
    for pair in pairs:
        if ":" not in pair:
            raise ValueError(
                f"Invalid TARGET_CATALOGS entry '{pair}', expected 'environment:dataset'"
            )
        environment, dataset = (part.strip() for part in pair.split(":", 1))
        catalogs.append(catalog_config(environment, dataset))

    setup_postgres(catalogs)
    setup_duckdb()
    # Note: Postgres is not exposed on the firewall. It listens on
    # localhost only (see tasks/postgres.py), so DuckDB runs on this
    # server itself (over SSH) rather than connecting in from a client.
    setup_firewall()
    persist_firewall_config()
    apt.packages(name="Install fail2ban for SSH", packages=["fail2ban"])


deploy()
