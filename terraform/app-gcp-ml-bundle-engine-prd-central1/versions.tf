terraform {
  required_version = "~> 0.14"

  required_providers {
    google = {
      source  = "hashicorp/google"
      version = "~> 3.49.0"
    }
    null = {
      source  = "hashicorp/null"
      version = "~> 2.1.2"
    }
    template = {
      source  = "hashicorp/template"
      version = "~> 2.1.2"
    }
    kafka = {
      source = "mongey/kafka"
      version = "~> 0.2.10"
    }
  }
}
