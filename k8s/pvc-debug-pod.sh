#!/bin/bash

set -ex

# https://blog.scubbo.org/posts/pvc-debug-pod/

# This script assumes the existence and correct configuration of `kubectl` and `fzf`.
# TODO - cool feature would be to grab namespaces with `kubectl get ns` and pipe through `fzf` to select - but, 99% of the time, this'll just be for the current namespace anyway

PVC_TO_MOUNT=$(kubectl get pvc --no-headers | awk '{print $1}' | fzf)
POD_CREATE_OUTPUT=$(cat <<EOF | kubectl create -f -
apiVersion: v1
kind: Pod
metadata:
  generateName: debug-pod-
spec:
  volumes:
    - name: pvc
      persistentVolumeClaim:
        claimName: $PVC_TO_MOUNT
  containers:
    - name: debug-container
      image: ubuntu
      command: [ "/bin/bash", "-c", "--" ]
      args: [ "while true; do sleep 30; done;" ]
      volumeMounts:
        - mountPath: "/mnt/pvc"
          name: pvc
EOF
)
POD_NAME=$(echo $POD_CREATE_OUTPUT | awk '{print $1}')
kubectl wait --for=condition=Ready $POD_NAME
kubectl exec -it $POD_NAME -- /bin/bash
