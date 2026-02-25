PROJECT_DIR := .
SRC_DIR     := $(PROJECT_DIR)/src
TESTS_DIR    := $(PROJECT_DIR)/tests

.PHONY: install


install:
	uv tool install -e ./$(PROJECT_DIR)
