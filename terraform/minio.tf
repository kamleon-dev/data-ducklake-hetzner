variable "hetzner_storage_access_key" {
  description = "Hetzner Object Storage Access Key"
  type        = string
  sensitive   = true
}

variable "hetzner_storage_secret_key" {
  description = "Hetzner Object Storage Secret Key"
  type        = string
  sensitive   = true
}

variable "bucket_names" {
  description = <<-EOT
    S3 bucket names to create (must be globally unique). One bucket per
    environment hosted by this server, e.g.:
      ["ducklake-development", "ducklake-preproduction"]  for the shared server
      ["ducklake-production"]                             for the production server
  EOT
  type        = list(string)
}

provider "minio" {
  # nbg1: Nuremberg (DE)
  minio_server   = "nbg1.your-objectstorage.com"
  minio_user     = var.hetzner_storage_access_key
  minio_password = var.hetzner_storage_secret_key
  minio_region   = "nbg1"
  minio_ssl      = true
}

resource "minio_s3_bucket" "this" {
  for_each       = toset(var.bucket_names)
  bucket         = each.value
  acl            = "private"
  object_locking = false
}
