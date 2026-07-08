from pyinfra.operations import server, apt, postgres, files, systemd

PG_HBA_PATH = "/etc/postgresql/18/main/pg_hba.conf"
PG_CONF_PATH = "/etc/postgresql/18/main/postgresql.conf"


def setup_postgres(environments: list[dict]) -> None:
    """Provision PostgreSQL and one role+database per DuckLake environment
    sharing this server.

    `environments` is a list of dicts, each with:
      - role: Postgres role name for this environment
      - database: Postgres database name for this environment
      - password: password for the role

    Each environment's role is restricted (via pg_hba.conf) to loopback
    access on its own database only, so environments sharing this server
    cannot authenticate into a different environment's catalog even with
    a valid password for that other environment's role.
    """
    apt.update(name="Update packages", cache_time=3600)
    apt.upgrade(name="Upgrade packages")

    apt.packages(name="Install PostgreSQL", packages=["postgresql"])

    server.locale(
        name="Ensure en_US.UTF-8 locale is present",
        locale="en_US.UTF-8",
    )

    files.line(
        name="Restrict Postgres to loopback only (postgresql.conf)",
        path=PG_CONF_PATH,
        line=".*listen_addresses.*",
        replace="listen_addresses = 'localhost'",
        backup=True,
    )

    # Cleanup: remove any legacy fully-open rule from earlier versions of
    # this repo. Safe no-op if it was never present on this server.
    files.line(
        name="Remove any legacy open (0.0.0.0/0) pg_hba.conf rules",
        path=PG_HBA_PATH,
        line=r"^host\s+\S+\s+\S+\s+0\.0\.0\.0/0\s+md5",
        present=False,
        backup=True,
    )

    for env in environments:
        role = env["role"]
        database = env["database"]
        password = env["password"]

        postgres.role(
            name=f"Create role: {role}",
            role=role,
            password=password,
            _su_user="postgres",
        )

        postgres.database(
            name=f"Create database: {database}",
            database=database,
            owner=role,
            template="template0",
            encoding="UTF8",
            lc_collate="en_US.UTF-8",
            lc_ctype="en_US.UTF-8",
            _su_user="postgres",
        )

        files.line(
            name=f"Allow loopback only for {role} on {database} (pg_hba.conf)",
            path=PG_HBA_PATH,
            line=rf"^host\s+{database}\s+{role}\s+127\.0\.0\.1/32\s+md5",
            replace=f"host    {database}    {role}    127.0.0.1/32    md5",
            ensure_newline=True,
            backup=True,
        )

    systemd.service(
        name="Restart PostgreSQL to apply config changes",
        service="postgresql",
        restarted=True,
    )
