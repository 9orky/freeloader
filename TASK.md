# Coding Task

## Rules:
- Follow the coding rules outlined in CODING_RULES.md in the project root.

## Context
Terraform runner is to complex and buggy.

## Task Description
The whole terraform processing must be refactored.

### Stage 0 - block renaming
All blocks and all assets inside blocks must be named using underscoresinstead of hyphens - to avoid naming issues.
Block name (a folder name) is now SSOT for block name / id.

### Stage 1 Terraform files
Every block with terraform runner includes for *.tf files. From now on, terraform files become self contained, single asset with:

- variables defined with sane defaults
- basically what is now scattered into 4 files - becomes one
- every terraform file must contain variable called "name" which serves both freeloader's inner name for the resource and name for the remote resource if file requires it
- as a consequence, block definition (folder) holds two files: yaml definition and main.tf

#### Terraform refactor:
We need to introduce new abstractions to make terraform handling simpler and 

### Stage 2 - blocks and their (terraform's) resource directory
Let's unify how "instantiating" a block looks like:

- we copy source tf file to target resource folder
- all variables are defined in main.tf, so we read them and check which are required (you create TerraformFile class that knows how to read hcl with all required methods)
- when creating project manifest, you always include this required variables by default (--full dumps all variables to manifest)
- now very important part: terraform may read variables from json files (file must be properly named), so you take dictionary with all values from file and you overwrite it with values from project manifest and finally you dump it to json file in resource folder in dotfolder
- now resource folder has everything it needs - file and variables all in one place, so now you can:
    - run terraform commands in the clean form, without extra params (-input=false and other automation friendly settings still apply)
    - have one, self contained and emphemeral resource folder
- generally our aim is to have a resource folder that doesn't require any extra parameters or context - it has everything it needs to manage the resource
- you should propose new Terraform abstractions to make a code more readable:
    - TerraformFile (already mentioned, knows how to read config in hcl)
    - TerraformResource - this where everything mentioned earlier lives, also this class handles mentioned ops
    - anything else you come up with and might be usefull

### Stage 3 - pipeline logic
Now pipeline and runner instead of run every block in isolation (at the time) they incllude a loop inside that runs them all - this is very rigid and must be improved:

- blocks are executed in the calculated order, but one after another:
    - first is init + plan stage (we call it just plan), terraform plan always produced standard named plan file
    - next is apply which first produces json variables (mentioned in Stage 2)
    - destroy comes somewhere in the future but also one block after another

- we introduce a pipeline progress file, that is stored in home dotfolder, file is generated on pipeline first run, it keeps the list of blocks to run and tracks which ones are finished and if any block failed, it must contain last error - thanks to this user can pipeline up multiple times and it will start from the last failed block
- tracking the pipeline progress belongs to orchestrator, blocks should not be aware of this - boundaries

## Acceptance Criteria
Running pipeline is safe, predictable and traceable. Manging terraform has now new abstarctions that make code simpler, more organized and respecting boundaries
