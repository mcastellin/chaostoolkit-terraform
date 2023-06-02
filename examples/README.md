# Chaostoolkit Terraform Example

This example uses `chaostoolkit-terraform` to automatically handle resource deployment before the experiments tarts and tear down the stack after the experiment is finished.

The **main.tf** template uses the Docker Terraform provider to run an Nginx container in the host system.

```terraform
# ./main.tf

variable "local_port" {
  type    = number
  default = 8000
}
variable "restart" {
  type    = string
  default = "no"
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
```
