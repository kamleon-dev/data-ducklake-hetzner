from os import getenv

ssh_host = getenv("SSH_HOST")
if not ssh_host:
    raise ValueError(
        "SSH_HOST env var must be set to the target server's IP "
        "(from your .env.deploy-<workspace> file, matching the IP "
        "printed by 'tofu apply' / stored in data/<workspace>_server_ip.json)."
    )

postgres = [ssh_host]
