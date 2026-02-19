# Coding Task

## Rules:
- Follow the coding rules outlined in CODING_RULES.md in the project root.

## Context
I had this stupid idea, to bind managed project aggregate id to hash from absolute path. This causes huge problem - you cannot delete project and create one with the same name. To fix this, ProjectIndex was created but it causes the same problem elsewhere. The idea is to let user name projects as he wants yet still keep the managed projects under aggregate uuid (to avoid unique id problem)

## Task Description
Figure out simplest and most elegant solution ,how to unbind aggregate ids from filesystem, yet to have a list of projects actively managed by Freeloader. Focus only on project feature, because it is the one which will be an example for others.
