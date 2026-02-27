variable "language" {
  type    = string
  default = "python"
}

variable "package_manager" {
  type    = string
  default = "pip"
}

variable "server" {
  type    = string
  default = "nginx"
}

variable "language_version" {
  type    = string
  default = "3"
}

variable "server_version" {
  type    = string
  default = "1"
}

variable "target_folder" {
  type    = string

  validation {
    condition = direxists(var.target_folder)
    error_message = "The target_folder (${var.target_folder}) must exist."
  }
}

locals {
    template_file = "${path.module}/templates/${var.language}-${var.package_manager}-${var.server}.Dockerfile.tftpl"
    target_path = "${var.target_folder}/Dockerfile"
    
    dockerfile_content = templatefile(local.template_file, {
        language_semver = "${var.language}:${var.language_version}",
        server_semver   = "${var.server}:${var.server_version}"
    })
}

resource "local_file" "dockerfile" {
  content  = local.dockerfile_content
  filename = local.target_path
}