module "ml_bundle_engine_redis_queue_memory_store" {
  source         = "app.terraform.io/shipt/memorystore/google"
  version        = "1.0.3"
  memory_size_gb = "1"
  name           = "uc1-ml-bundle-engine-redis-queue"
  project        = "shipt-core-stg-redis"
  redis_version  = "REDIS_5_0"
  region         = "us-central1"
  labels = {
    environment = "staging"
    managed_by  = "terraform"
    name        = "redis-queue"
    repo        = "ml-bundle-engine"
  }
  config_var         = "ML_BUNDLE_QUEUE_URL"
  authorized_network = "projects/shipt-host/global/networks/host"
  redis_configs = {
    activedefrag     = "no"
    maxmemory-policy = "volatile-lru"
  }
  connect_mode  = "PRIVATE_SERVICE_ACCESS"
  application   = "ml-bundle-engine"
  group         = "ds"
  environment   = "staging"
  config_region = "us-central1"
}
