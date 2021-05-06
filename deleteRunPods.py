from kubernetes import client, config
from kubernetes.client.rest import ApiException

import argparse
import re


config.load_incluster_config()

v1 = client.CoreV1Api()
current_namespace = open("/var/run/secrets/kubernetes.io/serviceaccount/namespace").read()
parser = argparse.ArgumentParser(description='Find and delete run pods.')
parser.add_argument('--workflow', type=str,
  help='Path of the local file containing the Workflow name.')
args = parser.parse_args()
workflow = args

try:
    pods = v1.list_namespaced_pod(namespace=current_namespace, label_selector="workflows.argoproj.io/completed=true")
except ApiException as e:
    print("Exception when calling CoreV1Api->list_namespaced_pod: %s\n" % e)

pod_names = []
for pod in pods.items:
    pod_names.append(pod.metadata.name)

print(pod_names)
pod_names = [pod for pod in pod_names if re.match(r"^"+str(workflow)+"-[.]*", pod)]
print(pod_names)
for pod_name in pod_names:
    try:
        api_response = v1.delete_namespaced_pod(pod_name, current_namespace)
        print(api_response)
    except ApiException as e:
        print("Exception when calling CoreV1Api->delete_namespaced_pod: %s\n" % e)

