#!/bin/bash

# Expects:
# * Name of the Cronjob from which to create as $1
#   * If we wanted, we could scan the namespace and pick the cronjob if only one exists, but that seems dangerous if in
#       wrong namespace
# * For `namespace` to be set correctly


JOB_ID=$(kubectl create job --from="cronjob/$1" "manual-run-"$(date +%s) | awk '{print $1}')
echo "Executing job as $JOB_ID"
kubectl wait --for=condition=ready --timeout=60s $JOB_ID
echo "Job is ready - logs follow:"
kubectl logs --follow $JOB_ID
