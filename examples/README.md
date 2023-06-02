# Chaostoolkit Terraform Example

This example uses `chaostoolkit-terraform` to automatically handle resource deployment before the experiment starts and tear down the stack after the experiment is finished.

## Running the experiment

Make sure `chaostoolkit` and `chaostoolkit-terraform` Python modules are installed in your system:

```shell
pip install -U chaostoolkit chaostoolkit-terraform
```

Then, to run the experiment:

```shell
chaos run experiment.yaml
```

## The infrastructure template

The **main.tf** template uses the Docker Terraform provider to run an Nginx container in the host system:

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

Application container name and exposed port are exported as Terraform output parameters and can be accessed
in the Chaos Toolkit experiment template using the `tf_out__` variable prefix.

## The Chaos Toolkit experiment

The experiment in **experiment.yaml** is a simple Chaos Toolkit template to check if the Nginx webserver can survive an abrupt termination.

The **chaosterraform control** is configured for this experiment:

```yaml
# ./experiment.yaml

configuration:
  tf__restart: "always"

controls:
  - name: chaosterraform
    provider:
      type: python
      module: chaosterraform.control
      arguments:
        retain: true
```

The `chaosterraform.control` will initialize and apply the Terraform template before the experiment.

For demonstration, the control is configured to retain the created resources after the experiment. To automatically destroy resources you can change control arguments to `retain: false`.

Using the experiment **configuration** section, we provide an override value for the `restart` variable in the **main.tf** using `tf__restart: "always"`. This is the same as running terraform apply with the `-var` option:

```shell
terraform apply -var restart=always -auto-approve
```

### Method and hypothesis

The experiment method uses a **process** probe to send the termination signal to the running Nginx container and hypothesise that the webserver will still be responding at http://localhost:8000 after a short pause.

```yaml
# ./experiment.yaml

steady-state-hypothesis:
  title: "check-service-online"
  probes:
    - name: "service-should-respond"
      type: probe
      tolerance: 200
      provider:
        type: http
        url: "http://localhost:${tf_out__container_port}/"
        method: GET
        timeout: 3

method:
  - name: "terminate-nginx-service"
    type: action
    provider:
      type: process
      path: "docker"
      arguments: "exec ${tf_out__container_name} nginx -s quit"
    pauses:
      after: 5
```

`container_name` and `container_port` are output variables exported by the Terraform template and accessible in the Chaos Toolkit experiment using variable replacement, respectively with `${tf_out__container_name}` and `${tf_out__container_port}`.
