# Shared server hosting both the development and preproduction environments.
server_name     = "ducklake-development-preproduction"
server_type     = "cpx22"
server_location = "nbg1"

bucket_names = [
  "data-palantir-development-measurements",
  "data-palantir-preproduction-measurements",
  "data-palantir-development-calibration",
  "data-palantir-preproduction-calibration",
]

team_ssh_key_names = [
  "pablo.gallego@kamleon.com",
  "valentino.asole@kamleon.com",
  "sergi.consul@kamleon.com",
]
