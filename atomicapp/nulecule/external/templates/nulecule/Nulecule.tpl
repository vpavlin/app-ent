---
specversion: ${nulecule_spec_version}
id: ${app_name}

metadata:
  name: ${app_name}
  appversion: ${app_version}
  description: ${app_desc}

graph:
  - name: ${app_name}
    params:
      - name: image
        description: Container image to use
        default: centos/httpd
    artifacts:
      kubernetes:
        - file://artifacts/kubernetes/${app_name}_pod.yaml
        - file://artifacts/kubernetes/${app_name}_service.yaml
      docker:
        - file://artifacts/docker/${app_name}_run
