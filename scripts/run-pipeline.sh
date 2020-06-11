#!/bin/bash

set -e
cd "$(dirname "${BASH_SOURCE[0]}")/.."
sudo docker-compose up -d
