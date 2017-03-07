apiVersion: v1
kind: Pod
metadata:
  name: $app_name
  labels:
    name: $app_name

spec:
  containers:
    - name: $app_name
      image: $image
