from kubernetes import client, config
from kubernetes.client.rest import ApiException
from minio import Minio
from minio.error import S3Error
import os
import urllib3
import argparse
import re

def main():
    config.load_incluster_config()
    v1 = client.CoreV1Api()
    current_namespace = open("/var/run/secrets/kubernetes.io/serviceaccount/namespace").read()

    minio_client = Minio (
        "minio-service.kubeflow.svc.cluster.local:9000",
        access_key = 'minio',
        secret_key = 'minio123',
        secure = False
    )

    buckets = minio_client.list_buckets()
    for bucket in buckets:
        print(bucket.name, bucket.creation_date)

    parser = argparse.ArgumentParser(description='Find and delete run pods.')
    parser.add_argument('--workflow', type=str,
      help='Path of the local file containing the Workflow name.')
    args = parser.parse_args()
    workflow = args.workflow

    print("Workflow name: "+ str(workflow))

    try:
        pods = v1.list_namespaced_pod(namespace=current_namespace, label_selector="workflows.argoproj.io/completed=true")
    except ApiException as e:
        print("Exception when calling CoreV1Api->list_namespaced_pod: %s\n" % e)

    pod_names = [pod.metadata.name for pod in pods.items]

    pod_names = [pod for pod in pod_names if re.match(r"^"+str(workflow)+"-[.]*", pod)]
    print("Pods to be removed: "+str(pod_names)[1:-1] )
    for pod_name in pod_names:
        try:
            api_response = v1.delete_namespaced_pod(pod_name, current_namespace)
            print(api_response)
        except ApiException as e:
            print("Exception when calling CoreV1Api->delete_namespaced_pod: %s\n" % e)

if __name__ == "__main__":
    try:
        main()
    except S3Error as exc:
        print("error occurred.", exc)