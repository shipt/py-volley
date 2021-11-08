module "ml_bundle_engine_bundle_engine_input_bus_ds_marketplace_v1_bundle_engine_input_topic_module" {
  source         = "app.terraform.io/shipt/topic/kafka"
  version        = "0.4.1"
  application    = "ml-bundle-engine"
  group          = "ds"
  environment    = "production"
  config_var     = "INPUT_TOPIC"
  config_regions = ["us-central1"]
  name           = "prd.bus.ds-marketplace.v1.bundle_engine_input"
  config = {
    "cleanup.policy"  = "delete"
    "retention.bytes" = "-1"
    "retention.ms"    = "259200000"
  }
  partitions = 12
}
module "ml_bundle_engine_bundle_engine_dlq_bus_ds_marketplace_v1_bundle_engine_dlq_topic_module" {
  source         = "app.terraform.io/shipt/topic/kafka"
  version        = "0.4.1"
  application    = "ml-bundle-engine"
  group          = "ds"
  environment    = "production"
  config_var     = "INPUT_TOPIC"
  config_regions = ["us-central1"]
  name           = "prd.bus.ds-marketplace.v1.bundle_engine_dlq"
  config = {
    "cleanup.policy"  = "delete"
    "retention.bytes" = "-1"
    "retention.ms"    = "259200000"
  }
  partitions = 12
}
module "ml_bundle_engine_bundle_engine_output_bus_ds_marketplace_v1_bundle_engine_output_topic_module" {
  source         = "app.terraform.io/shipt/topic/kafka"
  version        = "0.4.1"
  application    = "ml-bundle-engine"
  group          = "ds"
  environment    = "production"
  config_var     = "OUTPUT_TOPIC"
  config_regions = ["us-central1"]
  name           = "prd.bus.ds-marketplace.v1.bundle_engine_output"
  config = {
    "cleanup.policy"  = "delete"
    "retention.bytes" = "-1"
    "retention.ms"    = "259200000"
  }
  partitions = 12
}

