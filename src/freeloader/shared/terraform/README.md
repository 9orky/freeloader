# terraform

Terraform CLI facade — prepare, apply, output, destroy.

## Responsibilities

- Copies a `main.tf` template into a working directory and generates a `.tfvars.json` file
- Runs `terraform init`, `plan`, `apply`, `output`, and `destroy` via subprocess
- Parses HCL2 Terraform files to expose typed variable and output metadata

## Public interface

```python
from freeloader.shared.terraform import Terraform, TerraformVariable

tf = Terraform(work_dir)
tf.prepare(template_path, {"var_name": "value"})
tf.apply()
outputs: dict = tf.output()
tf.destroy()

variables: list[TerraformVariable] = tf.variables(template_path)
```