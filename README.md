# chaostoolkit-terraform

A [Chaos Toolkit](https://chaostoolkit.org/) driver to extend chaos experiments with [Terraform](https://www.terraform.io/)

## Package Installation

To install the *edge* version of the `chaostoolkit-terraform` package directly from the repository source code:

```shell
pip install -U "git+https://github.com/mcastellin/chaostoolkit-terraform.git#egg=chaostoolkit-terraform"
```

## Usage

**chaostoolkit-terraform** provides a control to deploy terraform modules. To activate the `chaostf.control` for your experiments
you need to define it in your experiment files (or settings):

```yaml
title: My experiment
description: ...

controls:
  - name: "Deploy Terraform module"
    provider:
      type: python
      module: chaostf.control

steady-state-hypothesis: {...}

method: []
```

By default the `chaostf.control` will reference the Terraform module found in the current working directory.

The control will execute Terraform command in the following phases of the experiment execution:

| Phase                 | Actions |
| --------------------- | ------- |
| **Configure control** | Initialize the Terraform driver |
| **Before experiment** | Initialize and apply the selected Terraform module |
| **After experiment**  | Run terraform destroy unless specifically asked to retain the created resources |

## Configuration

You can configure the Terraform control either via *control arguments* or using Chaos Toolkit parameters with the `tf_conf__` prefix:

**Configuration with control arguments**
```yaml
controls:
  - name: "Deploy Terraform module"
    provider:
      type: python
      module: chaostf.control
      arguments:
        silent: false
        retain: true
```

**Configuration using Ctk parameters**
```yaml
configuration:
# parameters prefixed with `tf_conf__` will configure chaostf driver
  tf_conf__silent: false
  tf_conf__retain: true

controls:
  - name: "Deploy Terraform module"
    provider:
      type: python
      module: chaostf.control
```

> When both options are supplied **configuration parameters supplied via the experiment configuration will
> be used**.


| Parameter Name        | Usage |
| --------------------- | ------- |
| **silent** | Suppress Terraform console output to avoid verbose experiment logs, defaults to `true`|
| **retain** | Do not run `terraform destroy` at the end of the experiment to retain resources, defaults to `false` |
| **chdir** | Instruct Terraform to change its working directory before running subcommands |

## Set Terraform Input Variables

You can override input variables defined in the Terraform module from within the experiment using
Chaos Toolkit configuration parameters prefixed by `tf__`:

```yaml
configuration:
# parameters prefixed with `tf__` will set terraform input variables for the module
  tf__vpc_id: "vpc-0000000000"
  tf__number_of_azs: 2
  ...

controls:
  - name: "Deploy Terraform module"
    provider:
      type: python
      module: chaostf.control
```


## Use Terraform Outputs In Chaos Experiments

If your Terraform module exports some output variables you can use them in the Chaos Toolkit experiments
as regular experiment parameters. Such variables are added to the configuration context with the `tf_out__` prefix.

For example, this Terraform module exports a load balancer DNS name:

```terraform
terraform {
    ...
}

output "alb_dns_name" {
    value = aws_lb.application_lb.dns_name
}
```

We can use the exported DNS name in our chaos experiment like so:

```yaml
controls:
  - name: "Deploy Terraform module"
    provider:
      type: python
      module: chaostf.control

steady-state-hypothesis:
  title: "Application is available"
  probes:
    - type: probe
      name: "should-respond-200"
      tolerance: 200
      provider:
        type: http
        url: "http://${tf_out__alb_dns_name}"
        method: "GET"
        timeout: 3
```
