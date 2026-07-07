from pyinfra.operations import apt
from os import getenv
from tasks.postgres import setup_postgres
from tasks.duckdb import setup_duckdb
from tasks.secure import setup_firewall, persist_firewall_config


def deploy():
    setup_postgres(db_password=getenv("POSTGRES_DB_PASSWORD"))
    setup_duckdb()
    # Note: Postgres is not exposed on the firewall. It listens on
    # localhost only (see tasks/postgres.py), so DuckDB runs on this
    # server itself (over SSH) rather than connecting in from a client.
    setup_firewall()
    persist_firewall_config()
    apt.packages(name="Install fail2ban for SSH", packages=["fail2ban"])


deploy()
