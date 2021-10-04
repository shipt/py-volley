provider "google" {
  credentials = base64decode(var.gcp_credentials)
  project     = "shipt-root"
  region      = "us-central1"
}

provider "google-beta" {
  credentials = base64decode(var.gcp_credentials)
  project     = "shipt-root"
  region      = "us-central1"
}

provider "kafka" {
  bootstrap_servers = var.bootstrap_servers
  sasl_mechanism = "plain"
  sasl_username = var.confluent_key
  sasl_password = var.confluent_secret
  skip_tls_verify = true
}
