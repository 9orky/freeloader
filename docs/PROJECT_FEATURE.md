# Project

User's project which will be managed by Freeloader.

## Use cases

### Manage Project
Starts user journey. First checks are made, to make sure that project is not already managed by FL:

In the project root (cwd):
- freeloader.yml does not exist
- .freeloader folder does not exist

### Initiation steps

#### 1. Detect what tech stack is in the project. 
Language, language_version and package_manager are enough data to generate useful files from templates. 

If there is no clue what tech stack will be used, a lot of files would be generated with no reason.