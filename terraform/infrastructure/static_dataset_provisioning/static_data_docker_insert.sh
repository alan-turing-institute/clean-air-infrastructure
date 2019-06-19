#!/bin/bash

# This file was generated automatically by terraform. It will insert GDB files to a postgreSQL database 

# Login to ACR. Will prompt for details
docker login ${acr_login_server}

# Pull docker image
docker pull ${acr_login_server}/insert_static_datasource:latest

# Run docker image

# docker run -v 