from kubernetes import client, config
from kubernetes.client.rest import ApiException
from minio import Minio
from minio.error import S3Error
import os
import urllib3
import split
import argparse
import re
import base64
import json
import urllib3
from kubernetes import client, config


def delete_artifacts(pod_name):
    print("Deleting artifacts")

    minio_client = Minio(
        "minio.kubeflow.svc.cluster.local:9000",
        access_key='minio',
        secret_key='FY2YHUU7A4ITWS2FTSAR6VKBBH3AFL',
        secure=False
    )

    # buckets = minio_client.list_buckets()

    # for bucket in buckets:
    objects = minio_client.list_objects('mlpipeline', recursive=True, start_after=None, include_user_meta=True)

    for obj in objects:

        if re.match(r"[\w///-]*" + str(pod_name) + "[.]*", str(obj._object_name)):

            try:
                print("Artefact to delete: " + str(obj._object_name) + " in bucket: "+ str('mlpipeline'))
                minio_client.remove_object('mlpipeline', str(obj._object_name))
            except S3Error as exc:
                print("error occurred while deleting artefact.", exc)


def delete_pods(pod_name):
    print("Deleting pods")
    workflow = pod_name.rsplit('-', 1)[0]

    configuration = client.Configuration()
    config.load_incluster_config(client_configuration=configuration)

    configuration.verify_ssl = False

    v1 = client.CoreV1Api(client.ApiClient(configuration))

    current_namespace = open("/var/run/secrets/kubernetes.io/serviceaccount/namespace").read()

    print("Workflow name: " + str(workflow))
    print("Pod name: " + str(pod_name))

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
            print('Pod: ' + pod_name + ' removed.')
        except ApiException as e:
            print("Exception when calling CoreV1Api->delete_namespaced_pod: %s\n" % e)


def main():
    parser = argparse.ArgumentParser(description='Find and delete run pods.')
    parser.add_argument('--pod-path', type=str,
                        help='Path of the local file containing the Pod name.')
    args = parser.parse_args()
    with open(args.pod_path, 'r') as f:
        pod_name = f.read().strip()

    # delete artifact for download pod therefore delete dataset
    delete_artifacts(pod_name)
    # delete all pods used in experiment before
    delete_pods(pod_name)


if __name__ == "__main__":
    try:
        main()
    except S3Error as exc:
        print("error occurred.", exc)
