from pyinfra.operations import apt, iptables
from os import getenv
from tasks.postgres import setup_postgres
from tasks.secure import setup_firewall, persist_firewall_config


def deploy():
    setup_postgres(db_password=getenv("POSTGRES_DB_PASSWORD"))
    iptables.rule(
        name="Allow PostgreSQL traffic",
        chain="INPUT",
        jump="ACCEPT",
        protocol="tcp",
        destination_port=5432,
    )
    setup_firewall()
    persist_firewall_config()
    apt.packages(name="Install fail2ban for SSH", packages=["fail2ban"])


deploy()
