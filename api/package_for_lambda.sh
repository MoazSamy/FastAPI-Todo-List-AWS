#!/bin/bash

# Exit if command fails
set -eux pipefail

pip install -t lib -r requirements.txt
(cd lib; zip ../lambda_function.zip -r .)
# Adds the todo.py to the zip file
zip lambda_function.zip -u todo.py

# Clean up
rm -rf lib