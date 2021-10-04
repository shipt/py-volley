terraform {
    backend "remote" {
        hostname     = "app.terraform.io"
        organization = "shipt"

        workspaces {
            name = "app-gcp-ml-bundle-engine-stg-central1"
        }
    }
}
