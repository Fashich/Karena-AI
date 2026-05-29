# Karena AI — Greenfield infrastructure (reference)
terraform {
  required_version = ">= 1.5"
  required_providers {
    azurerm = {
      source  = "hashicorp/azurerm"
      version = "~> 4.0"
    }
  }
}

variable "environment" {
  type    = string
  default = "staging"
}

variable "region" {
  type    = string
  default = "southeastasia"
}

# Extend with AKS cluster, managed Qdrant/Redis, API Management gateway
# per enterprise deployment exemplars in docs/ARCHITECTURE.md

output "environment" {
  value = var.environment
}

output "region" {
  value = var.region
}
