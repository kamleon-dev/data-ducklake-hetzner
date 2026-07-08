from pyinfra import host
from pyinfra.operations import server
from pyinfra.facts.server import Command

DUCKDB_VERSION = "1.5.3"
DUCKDB_SYMLINK_PATH = "/usr/local/bin/duckdb"


def setup_duckdb(version: str = DUCKDB_VERSION) -> None:
    """Install the DuckDB CLI on the server so it can be run over SSH.

    Uses the official install script (which installs to
    ~/.duckdb/cli/<version>/duckdb, NOT /usr/local/bin — see
    https://duckdb.org/docs/installation), pinned to a specific version
    via the DUCKDB_VERSION env var for reproducibility. A symlink is
    created at /usr/local/bin/duckdb so the binary is found on PATH in
    non-interactive SSH sessions (e.g. `ssh host "duckdb ..."`), which
    don't source .bashrc/.profile the way the installer's own hint
    assumes.
    """
    installed_version = host.get_fact(
        Command,
        command=f"{DUCKDB_SYMLINK_PATH} --version 2>/dev/null || echo none",
    )

    if version not in (installed_version or ""):
        server.shell(
            name=f"Install DuckDB {version}",
            commands=[
                f"DUCKDB_VERSION={version} sh -c \"$(curl -fsSL https://install.duckdb.org)\"",
            ],
        )

    server.shell(
        name="Symlink DuckDB into /usr/local/bin",
        commands=[
            f"ln -sf /root/.duckdb/cli/{version}/duckdb {DUCKDB_SYMLINK_PATH}",
        ],
    )