# 🍕 freeloader

**You have better things to do than deploy the same app for the 100th time.**

Pipeline composer for indie developers who'd rather ship code than babysit infrastructure.

[![Python 3.12+](https://img.shields.io/badge/python-3.12+-blue.svg)](https://www.python.org)
[![License: MIT](https://img.shields.io/badge/license-MIT-green.svg)](LICENSE)

---

## The Problem

You just vibe-coded something brilliant over the weekend. Now you need to deploy it. Here's what that looks like:

> 1. Create a GitHub repo
> 2. Create a GitLab project for the container registry (because free tier)
> 3. Generate a production Dockerfile for your stack
> 4. Write the GitHub Actions CI pipeline
> 5. Wire GitLab registry credentials as GitHub secrets
> 6. Write the docker-compose for the target
> 7. Set up the deployment target (Coolify? Render? A VPS you forgot about?)
> 8. Register the app in Coolify
> 9. Copy the deploy webhook URL
> 10. Paste it back into GitHub secrets
> 11. Push, wait, pray
> 12. Debug why the Dockerfile doesn't build
> 13. Fix the CI, push again
> 14. Realize you forgot to set `GITLAB_TOKEN`
> 15. Mass-copy `.env` values you already entered somewhere last month

And next weekend? **You'll do it all over again.**

## General Idea

Freeloading often requires composing your infrastructure at Service Providers, who give some of its component for free. For free and with generous limits. Example:

- you host your code in github repository
- github actions do the heavy lifting: handle tests, builds (multi-arch docker images) and deployments
- since github is not generous when it comes to image registry capacity, you need a gotlab project, with gives you much more freedom
- then you need to call a deployment hook, so your production environment pulls latest image from registry and deploys it

Every mentioned component maps to terraform resource. It has source terraform file, yaml config or other required by main.tf assets.
Terraform source file has variables as input(requires) and output(exposes) as output. There is a concept of a Block, that resolve order of creating resources and coordinate passing inputs or inputs from other resource's outputs.

