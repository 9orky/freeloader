# Coding Task

## Rules:
- Follow the coding rules outlined in AGENT.md in the project root.

## Context
Freeloader is about free deployments, so it must evolve around costs awareness. We can have many types of blocks, from always free, through free tier (with time or cost limits) up to paid. We need costs module in service_providers, that will let us fetch our current billing amount for a given provider. Remember, that some providers may charge for such checks.

## Task Description
Design architecture for implementing costs feature. Feature allow:

- check total billing with warning before check if provider charges for it
- include costs structure in blocks, that will always inform user about possible costs
- if possible, billing should include free tiers usage
- generally user must know if he ever pays and how much he owes to provider

## Acceptance Criteria
Module / package architecture design in DESIGN.md file in this folder. Design have in minds other providers like gcp, hetzner or vercel.
