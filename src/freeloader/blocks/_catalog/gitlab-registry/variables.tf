variable "name" {
  type = string
}

variable "description" {
  type    = string
  default = ""
}

variable "visibility" {
  type    = string
  default = "private"
}

variable "token_scopes" {
  type    = list(string)
  default = ["read_registry", "write_registry"]
}
