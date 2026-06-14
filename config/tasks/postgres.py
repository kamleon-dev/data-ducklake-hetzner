from pyinfra.operations import server, apt, postgres, files, systemd


def setup_postgres(db_password: str = "changeme"):
    apt.update(name="Update packages", cache_time=3600)
    apt.upgrade(name="Upgrade packages")

    apt.packages(name="Install PostgreSQL", packages=["postgresql"])

    # Configure locale (needed for PostgreSQL)
    server.locale(
        name="Ensure en_US.UTF-8 locale is present",
        locale="en_US.UTF-8",
    )

    postgres.role(
        name="Create a role", role="ducklake", password=db_password, _su_user="postgres"
    )

    postgres.database(
        database="ducklake_catalog",
        owner="ducklake",
        template="template0",
        encoding="UTF8",
        lc_collate="en_US.UTF-8",
        lc_ctype="en_US.UTF-8",
        _su_user="postgres",
    )

    files.line(
        name="Allow all addresses (postgresql.conf) (insecure, see README)",
        path="/etc/postgresql/18/main/postgresql.conf",
        line=".*listen_addresses.*",
        replace="listen_addresses = 'localhost'",
        backup=True,
    )

    #files.line(
        #name="Allow all addresses (pg_hba.conf) (insecure, see README)",
        #path="/etc/postgresql/18/main/pg_hba.conf",
        #line="host    ducklake_catalog           ducklake         0.0.0.0/0          md5",
        #ensure_newline=True,
        #backup=True,
    #)

    files.line(
        name="Remove public pg_hba.conf rule",
        path="/etc/postgresql/18/main/pg_hba.conf",
        line=r"^host\s+ducklake_catalog\s+ducklake\s+0\.0\.0\.0/0\s+md5",
        present=False,
        backup=True,
    )

    files.line(
        name="Allow loopback only (pg_hba.conf)",
        path="/etc/postgresql/18/main/pg_hba.conf",
        line=r"^host\s+ducklake_catalog\s+ducklake\s+127\.0\.0\.1/32\s+md5",
        replace="host    ducklake_catalog    ducklake    127.0.0.1/32    md5",
        ensure_newline=True,
        backup=True,
    )
    systemd.service(
        name="Restart PostgreSQL to apply config changes",
        service="postgresql",
        restarted=True,
    )
