# Coding Task

## Rules:
- Follow the coding rules outlined in AGENT.md in the project root.

## Context
Service Providers must be convenient, that's why we need the Obtain Token action / procedure. In order not to be enigmatic, and printing only url with short info, we need a small subsystem, that will allow compose different actions. 

Look for these examples:

- coolify requires installation url, so user can be redirected
- in aws case, only url is required, and than it waits for credentials (user input from cli)
- maybe some other step / action would be necessary in some block providers
- we don't need framework, just easily define steps

## Task Description
Design architecture for implementing "Obtain Token" feature, which is simple yet easily extendable. You must also decide if create another abstract base or plugin into current auth - i think that second option is ok, you wil only add one property to protocol (ObtainToken)

## Acceptance Criteria
Module / package architecture design in DESIGN.md file in this folder.
