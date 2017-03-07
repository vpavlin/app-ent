apiVersion: v1
kind: Service
metadata:
  name: $app_name
  labels:
    name: $app_name
spec:
  ports:
    - port: 80
      targetPort: 80
  selector:
    name: $app_name
