variable "name" {
  type = string
}

variable "server_uuid" {
  type = string
}

variable "coolify_endpoint" {
  type = string
}

variable "coolify_project_uuid" {
  type = string
}

variable "destination_uuid" {
  type        = string
  description = "UUID of the Docker network/destination on the server"
}

variable "environment_name" {
  type    = string
  default = "production"
}

variable "compose" {
  type    = string
  default = ""
}

variable "registry_image_path" {
  type    = string
  default = ""
}

variable "domain" {
  type    = string
  default = ""
}
