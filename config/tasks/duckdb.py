from pyinfra import host
from pyinfra.operations import server
from pyinfra.facts.server import Command

DUCKDB_VERSION = "1.5.3"
DUCKDB_INSTALL_PATH = "/usr/local/bin/duckdb"


def setup_duckdb(version: str = DUCKDB_VERSION) -> None:
    """Install the DuckDB CLI on the server so it can be run over SSH.

    Uses the official install script, pinned to a specific version for
    reproducibility across environments. Skips reinstalling if the pinned
    version is already present.
    """
    installed_version = host.get_fact(
        Command,
        command=f"{DUCKDB_INSTALL_PATH} --version 2>/dev/null || echo none",
    )

    if version not in (installed_version or ""):
        server.shell(
            name=f"Install DuckDB {version}",
            commands=[
                f"curl -fsSL https://install.duckdb.org | sh -s -- --version {version}",
            ],
        )
