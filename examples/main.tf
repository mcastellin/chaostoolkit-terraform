terraform {
  required_providers {
    docker = {
      source  = "kreuzwerker/docker"
      version = "~> 3.0"
    }
  }
}

variable "local_port" {
  type    = number
  default = 8000
}
variable "restart" {
  type    = string
  default = "no"
}

provider "docker" {
  host = "unix:///var/run/docker.sock"
}

resource "docker_image" "nginx" {
  name = "nginx:latest"
}

resource "docker_container" "nginx" {
  image = docker_image.nginx.image_id
  name  = "nginx_webserver"

  restart = var.restart

  ports {
    internal = 80
    external = var.local_port
  }
}

output "container_name" {
  value = docker_container.nginx.name
}

output "container_port" {
  value = var.local_port
}
