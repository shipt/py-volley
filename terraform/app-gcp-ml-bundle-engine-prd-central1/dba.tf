module "ml_bundle_engine_redis_queue_memory_store" {
  source         = "app.terraform.io/shipt/memorystore/google"
  version        = "1.0.4"
  memory_size_gb = "1"
  name           = "uc1-ml-bundle-engine-redis-queue"
  project        = "shipt-ds-prd-redis"
  redis_version  = "REDIS_5_0"
  region         = "us-central1"
  labels = {
    environment = "production"
    managed_by  = "terraform"
    name        = "redis-queue"
    repo        = "ml-bundle-engine"
  }
  config_var         = "REDIS_HOST"
  authorized_network = "projects/shipt-host/global/networks/host"
  redis_configs = {
    activedefrag     = "no"
    maxmemory-gb     = "1"
    maxmemory-policy = "volatile-lru"
  }
  connect_mode  = "PRIVATE_SERVICE_ACCESS"
  application   = "ml-bundle-engine"
  group         = "ds"
  environment   = "production"
  config_region = "us-central1"
}
module "ml_bundle_engine_ml_bundle_engine_cloudSql_module" {
  source      = "app.terraform.io/shipt/cloud-sql/google"
  version     = "0.1.3"
  application = "ml-bundle-engine"
  environment = "production"
  size = {
    ram     = "4 GB"
    storage = "10 GB"
  }
  group          = "ds"
  region         = "us-central1"
  config_var     = "CLOUDSQL_DATABASE_URL"
  repo_name      = "ml-bundle-engine"
  network        = "projects/shipt-core-prd-host/global/networks/core-prd-host"
  cloud_provider = "gcp"
  slack_channel  = ""
  team           = "machine-learning"
  project_id     = "shipt-ds-prd-psql"
  name           = "ml-bundle-engine"
}
