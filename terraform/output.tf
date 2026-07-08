output "server_ip" {
  value       = hcloud_server.this.ipv4_address
  description = "Public IP of this DuckLake server"
}

output "bucket_names" {
  value       = [for b in minio_s3_bucket.this : b.bucket]
  description = "S3 buckets created on this server"
}
