from kubernetes import client, config
from kubernetes.client.rest import ApiException
from minio import Minio
from minio.error import S3Error
import os
import urllib3
import split
import argparse
import re


def delete_artefacts(pod_name):
    minio_client = Minio(
        "minio-service.kubeflow.svc.cluster.local:9000",
        access_key='minio',
        secret_key='minio123',
        secure=False
    )

    buckets = minio_client.list_buckets()
    object_names = []


    for bucket in buckets:
        objects = minio_client.list_objects(bucket.name, recursive=True, start_after=None, include_user_meta=True)

        for obj in objects:
            if re.match(r"[\w///-]*" + str(obj._object_name) + "[.]*", str(obj._object_name):
                print("Deleting artefact: " + str(pod_name) + " in bucket: "+ str(bucket.name))
                try:
                    minio_client.remove_object(str(bucket.name), str(obj._object_name)
                except S3Error as exc:
                    print("error occurred while deleting artefact.", exc)


def delete_pods(pod_name):
    workflow = pod_name.rsplit('-', 1)[0]

    print("Workflow name: " + str(workflow))
    print("Pod name: " + str(pod_name))
    config.load_incluster_config()
    v1 = client.CoreV1Api()
    current_namespace = open("/var/run/secrets/kubernetes.io/serviceaccount/namespace").read()

    try:
        pods = v1.list_namespaced_pod(namespace=current_namespace,
                                      label_selector="workflows.argoproj.io/completed=true")
    except ApiException as e:
        print("Exception when calling CoreV1Api->list_namespaced_pod: %s\n" % e)

    pod_names = [pod.metadata.name for pod in pods.items if re.match(r"^" + str(workflow) + "-[.]*", pod.metadata.name)]

    print("Pods to be removed: " + str(pod_names)[1:-1])
    for pod_name in pod_names:
        try:
            api_response = v1.delete_namespaced_pod(pod_name, current_namespace)
        except ApiException as e:
            print("Exception when calling CoreV1Api->delete_namespaced_pod: %s\n" % e)


def main():
    parser = argparse.ArgumentParser(description='Find and delete run pods.')
    parser.add_argument('--pod-path', type=str,
                        help='Path of the local file containing the Pod name.')
    args = parser.parse_args()
    pod_name = args.pod_path

    # delete artefact for download pod therefore delete dataset
    delete_artefacts(pod_name)
    # delete all pods used in experiment before
    delete_pods(pod_name)


if __name__ == "__main__":
    try:
        main()
    except S3Error as exc:
        print("error occurred.", exc)
