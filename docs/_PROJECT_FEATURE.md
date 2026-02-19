# Project

Project is the vibe-coded slop. 

Whenever:

```shell
fl project init
```

is called, Freeloader does its best to discover facts about the Project.

## Initialize Project
Order of checks:
- manifest file: freeloader.yml exists and contains valid content
    - if no, check if folder is empty
        - if folder is empty > start creator
        - if folder is not empty > run tech stack discovery pipeline
    - if yes:
        - check project provisioning progress and resume if needed
        - if project is provisioned, scan all resources with terraform status to see their state

## Tech Stack
Contains info about how to run deployments and build images. Includes:

- package_manager: most reliable way to find package manager and deduct programming language
- language: programming language, mayb be detected by presence of a specifi file, mostly from package manager
- 