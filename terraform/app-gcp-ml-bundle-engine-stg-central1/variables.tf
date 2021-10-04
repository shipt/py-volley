variable "bootstrap_servers" {
  description = "The comma-separated list of servers used to initialize a connection to a cluster"
}
variable "confluent_key" {
  description = "Key from Confluent to be used for SASL auth (username)"
}
variable "confluent_secret" {
  description = "Secret from Confluent to be used for SASL auth (password)"
}
variable "gcp_credentials" {
  description = "account.json file for gcp authentication"
  type      = string
}
