from pyinfra.operations import apt
from os import getenv
from tasks.postgres import setup_postgres
from tasks.duckdb import setup_duckdb
from tasks.secure import setup_firewall, persist_firewall_config

# 'development' keeps its original role/database names (ducklake /
# ducklake_catalog) to avoid orphaning data already written under them.
# Every other environment gets a name derived from its environment name.
LEGACY_NAMES = {
    "development": {"role": "ducklake", "database": "ducklake_catalog"},
}


def environment_config(env_name: str) -> dict:
    names = LEGACY_NAMES.get(
        env_name,
        {"role": f"ducklake_{env_name}", "database": f"ducklake_catalog_{env_name}"},
    )
    password_var = f"POSTGRES_DB_PASSWORD_{env_name.upper()}"
    password = getenv(password_var)
    if not password:
        raise ValueError(
            f"Missing required env var: {password_var} "
            f"(needed because TARGET_ENVIRONMENTS includes '{env_name}')"
        )
    return {**names, "password": password}


def deploy():
    # Which environment(s) this specific server hosts, e.g.:
    #   "development,preproduction"  -> the shared dev/preproduction server
    #   "production"                 -> the dedicated production server
    target_environments = [
        e.strip()
        for e in getenv("TARGET_ENVIRONMENTS", "").split(",")
        if e.strip()
    ]
    if not target_environments:
        raise ValueError(
            "TARGET_ENVIRONMENTS env var must be set, e.g. "
            "'development,preproduction' or 'production'"
        )

    environments = [environment_config(e) for e in target_environments]

    setup_postgres(environments)
    setup_duckdb()
    # Note: Postgres is not exposed on the firewall. It listens on
    # localhost only (see tasks/postgres.py), so DuckDB runs on this
    # server itself (over SSH) rather than connecting in from a client.
    setup_firewall()
    persist_firewall_config()
    apt.packages(name="Install fail2ban for SSH", packages=["fail2ban"])


deploy()
