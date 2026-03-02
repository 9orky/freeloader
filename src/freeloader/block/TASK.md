# Coding Task

## Rules:
- Follow the coding rules outlined in AGENT.md in the project root.

## Context
Block feature grew big, can do a lot and requires maintanance, bug fixing, and architecture review.

## Task Description
Find and fix issues:

- blocks must be markable as required_tech_stack, since many of the blocks relies heavily on this knowledge (dockerfile, etc.)
- since tech stack is properly detected during project manifest generation, tech stack must be passed as a variables, so all blocks relying on tech stack will have consistent data
- there is a special class needed, that orchestrates final config values (manifest configs, secrets, etc.)

## Acceptance Criteria
Hardened, checked and audited block feature.
