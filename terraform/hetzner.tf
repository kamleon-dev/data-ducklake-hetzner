# Set variable values via a *.tfvars file (see terraform/environments/*.tfvars)
# or using -var="hcloud_token=..." CLI options.

variable "hcloud_token" {
  description = "Hetzner Cloud API token"
  type        = string
  sensitive   = true
}

variable "server_name" {
  description = "Name for this DuckLake server (e.g. 'ducklake-dev-preprod', 'ducklake-production')"
  type        = string
}

variable "server_type" {
  description = "Hetzner server type"
  type        = string
  default     = "cpx22"
}

variable "server_location" {
  description = "Hetzner datacenter location"
  type        = string
  default     = "nbg1"
}

variable "team_ssh_key_names" {
  description = <<-EOT
    Names of SSH keys already registered in the Hetzner project (as shown
    under Security > SSH keys in the console) to authorize on this server.
    Using existing named keys (rather than creating a new key resource per
    server from a single local public-key path) avoids ending up with a
    server whose authorized key doesn't match any team member's actual
    local private key.
  EOT
  type        = list(string)
}

# Configure the Hetzner Cloud Provider
provider "hcloud" {
  token = var.hcloud_token
}

# Look up each team member's already-registered SSH key by name, rather
# than creating a new hcloud_ssh_key resource (which would either collide
# on name across multiple servers in the same project, or require a
# separate name per server for no real benefit).
data "hcloud_ssh_key" "team" {
  for_each = toset(var.team_ssh_key_names)
  name     = each.value
}

resource "hcloud_primary_ip" "this" {
  name          = "${var.server_name}-ip"
  location      = var.server_location
  type          = "ipv4"
  assignee_type = "server"
  auto_delete   = true
}

resource "hcloud_server" "this" {
  name        = var.server_name
  image       = "ubuntu-26.04"
  server_type = var.server_type
  location    = var.server_location
  ssh_keys    = [for k in data.hcloud_ssh_key.team : k.id]

  public_net {
    ipv4_enabled = true
    ipv4         = hcloud_primary_ip.this.id
    ipv6_enabled = false
  }
}
