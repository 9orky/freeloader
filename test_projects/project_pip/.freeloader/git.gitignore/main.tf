variable "language" {
  type    = string
  default = "python"

  validation {
    condition = fileexists("${path.module}/templates/${var.language}.tftpl")
    error_message = "The language (${var.language}) is not supported."
  }
}

variable "target_folder" {
  type    = string

  validation {
    condition = direxists(var.target_folder)
    error_message = "The target_folder (${var.target_folder}) must exist."
  }
}

locals {
    base_content = templatefile("${path.module}/templates/base.tftpl")
    language_content = templatefile("${path.module}/templates/${var.language}.tftpl")
    gitignore_content = "${local.base_content}\n${local.language_content}"
}

resource "local_file" "gitignore" {
  content  = local.gitignore_content
  filename = "${var.target_folder}/.gitignore"
}