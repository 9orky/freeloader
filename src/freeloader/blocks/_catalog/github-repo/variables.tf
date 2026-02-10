variable "name" {
  type = string
}

variable "org" {
  type    = string
  default = ""
}

variable "description" {
  type    = string
  default = ""
}

variable "visibility" {
  type    = string
  default = "private"
}

variable "protect_main" {
  type    = bool
  default = false
}

variable "registry_user" {
  type    = string
  default = ""
}

variable "registry_token" {
  type      = string
  default   = ""
  sensitive = true
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
