# Dedicated server hosting only the production environment.
server_name     = "ducklake-production"
server_type     = "cpx22"
server_location = "nbg1"

bucket_names = [
  "data-palantir-production-measurements",
]

team_ssh_key_names = [
  "pablo.gallego@kamleon.com",
  "valentino.asole@kamleon.com",
  "sergi.consul@kamleon.com",
]
