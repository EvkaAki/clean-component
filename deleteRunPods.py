from kubernetes import client, config
import argparse
import re

config.load_incluster_config()

v1 = client.CoreV1Api()
current_namespace = open("/var/run/secrets/kubernetes.io/serviceaccount/namespace").read()
parser = argparse.ArgumentParser(description='Find and delete run pods.')
parser.add_argument('--workflow_name', type=str,
  help='Path of the local file containing the Workflow name.')
args = parser.parse_args()

workflow_name = args.workflow_name
pods = v1.list_namespaced_pod(current_namespace).items
print(workflow_name)
print(workflow_name)
r = re.compile(".*"+workflow_name)
pods = list(filter(r.match, pods))

# ret = v1.list_pod_for_all_namespaces(watch=False)
# try:
#     api_response = v1.delete_namespaced_pod(name, namespace)
#     print(api_response)
# except ApiException as e:
#     print("Exception when calling CoreV1Api->delete_namespaced_pod: %s\n" % e)
for i in pods:
    print("%s\t%s\t%s" % (i.status.pod_ip, i.metadata.namespace, i.metadata.name))

