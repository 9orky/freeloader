terraform {
  required_providers {
    local = {
      source  = "hashicorp/local"
      version = "~> 2.5"
    }
  }
}

variable "language" {
  type    = string
  default = "node"
}

variable "package_manager" {
  type    = string
  default = "npm"
}

variable "language_version" {
  type    = string
  default = ""
}

variable "test_command" {
  type    = string
  default = "npm test"
}

variable "build_platforms" {
  type    = string
  default = "linux/amd64"
}

variable "target_folder" {
  type = string

  validation {
    condition     = length(var.target_folder) > 0
    error_message = "The target_folder must not be empty."
  }
}

variable "registry_host" {
  type    = string
  default = ""
}

variable "registry_image_path" {
  type    = string
  default = ""
}

variable "deploy_webhook_url" {
  type      = string
  default   = ""
  sensitive = true
}

locals {
  setup_steps = templatefile(
    "${path.module}/templates/setup/${var.language}-${var.package_manager}.steps.tftpl",
    { version = var.language_version }
  )

  ci_content = templatefile("${path.module}/templates/ci.yml.tftpl", {
    setup_steps         = local.setup_steps
    test_command        = var.test_command
    enable_test         = var.test_command != "skip"
    enable_build        = var.registry_host != ""
    enable_deploy       = var.deploy_webhook_url != ""
    build_platforms     = var.build_platforms
    registry_host       = var.registry_host
    registry_image_path = var.registry_image_path
  })
}

resource "local_file" "ci_workflow" {
  content              = local.ci_content
  filename             = "${var.target_folder}/.github/workflows/ci.yml"
  directory_permission = "0755"
}
