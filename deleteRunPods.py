from kubernetes import client, config
import argparse
import re

config.load_incluster_config()

v1 = client.CoreV1Api()
current_namespace = open("/var/run/secrets/kubernetes.io/serviceaccount/namespace").read()
parser = argparse.ArgumentParser(description='Find and delete run pods.')
parser.add_argument('--workflow', type=str,
  help='Path of the local file containing the Workflow name.')
args = parser.parse_args()
print(args)

workflow = args
pods = v1.list_namespaced_pod(current_namespace).items
for pod in pods:
    pod_names.append(pod.metadata.name)
print(pod_names)
r = re.compile(".*"+workflow)
pods = list(filter(r.match, pods))
pod_names = [[pod for pod in pods if re.match(r"+workflow_name+", pod)]]
for pod_name in pod_names:
    try:
        api_response = v1.delete_namespaced_pod(pod_name, current_namespace)
        print(api_response)
    except ApiException as e:
        print("Exception when calling CoreV1Api->delete_namespaced_pod: %s\n" % e)

