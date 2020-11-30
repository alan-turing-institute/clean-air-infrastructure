# Backfill Camera Kubernetes Jobs
Based on [this](https://kubernetes.io/docs/tasks/job/parallel-processing-expansion/) technique

Uses nodepool 'jamcambackfill' to process historical footage requests from generated job specs.

Running `generate.sh` will create a `jobs` directory with jobs for 01-Jan to 30-June 0400-2059hrs, skipping Feb (we have no data there)

From there we can run `kubectl create -f ./jobs` with a linked Azure CLI in this directory to dispatch the jobs to the cluster!