# Connecting to the Urbanair database

This guide describes how to connect to the PostgreSQL database (DB) hosted by Azure for the London Air Quality project.

Before starting this guide, please make sure have completed the following tasks:

1. [Installing the cleanair package](installation.md)

The recommended way of accessing the database is via our cleanair package and the `urbanair_db` CLI.

```bash
urbanair_db init production
```
