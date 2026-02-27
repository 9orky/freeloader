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
  default = "python"

  validation {
    condition = fileexists("${path.module}/templates/${var.language}.tftpl")
    error_message = "The language (${var.language}) is not supported."
  }
}

variable "target_folder" {
  type = string

  validation {
    condition     = length(var.target_folder) > 0
    error_message = "The target_folder must not be empty."
  }
}

locals {
  base_content         = templatefile("${path.module}/templates/base.tftpl", {})
  language_content     = templatefile("${path.module}/templates/${var.language}.tftpl", {})
  dockerignore_content = "${local.base_content}\n${local.language_content}"
}

resource "local_file" "dockerignore" {
  content  = local.dockerignore_content
  filename = "${var.target_folder}/.dockerignore"
}