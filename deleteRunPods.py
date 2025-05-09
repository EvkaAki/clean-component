from kubernetes import client, config
from kubernetes.client.rest import ApiException
from minio import Minio
from minio.error import S3Error
import os
import urllib3
import split
import argparse
import re
import ssl
from urllib3.util import ssl_ as urllib3_ssl


import base64
import json
import urllib3
from kubernetes import client, config


def get_api_server_ca_from_k8s():
    # Use serviceaccount token to auth to /configz
    token_path = "/var/run/secrets/kubernetes.io/serviceaccount/token"
    with open(token_path, "r") as f:
        token = f.read()

    http = urllib3.PoolManager()
    headers = {
        "Authorization": f"Bearer {token}"
    }

    try:
        # This is available on all K8s clusters: gives API server config with the real CA
        resp = http.request(
            "GET",
            "https://kubernetes.default.svc:443/configz",
            headers=headers,
            cert=None,
            timeout=3.0,
            retries=False,
            preload_content=True
        )
    except urllib3.exceptions.SSLError as e:
        raise RuntimeError("Cannot connect to API server, SSL issue: " + str(e))

    if resp.status != 200:
        raise RuntimeError("Cannot read /configz: " + resp.data.decode())

    data = json.loads(resp.data.decode())
    # CA cert is base64 encoded
    ca_pem = base64.b64decode(data["config"]["authentication"]["x509"]["clientCAFile"])
    return ca_pem


# Now dynamically write the CA to a file and use it
def load_verified_api():
    ca_pem = get_api_server_ca_from_k8s()

    ca_path = "/tmp/k8s-dynamic-ca.crt"
    with open(ca_path, "wb") as f:
        f.write(ca_pem)

    configuration = client.Configuration()
    config.load_incluster_config(client_configuration=configuration)
    configuration.ssl_ca_cert = ca_path
    configuration.verify_ssl = True

    return client.CoreV1Api(client.ApiClient(configuration))


def delete_artifacts(pod_name):
    print("Deleting artifacts")

    minio_client = Minio(
        "minio.kubeflow.svc.cluster.local:9000",
        access_key='minio',
        secret_key='FY2YHUU7A4ITWS2FTSAR6VKBBH3AFL',
        secure=False
    )

    buckets = minio_client.list_buckets()

    for bucket in buckets:
        objects = minio_client.list_objects(bucket.name, recursive=True, start_after=None, include_user_meta=True)

        for obj in objects:

            if re.match(r"[\w///-]*" + str(pod_name) + "[.]*", str(obj._object_name)):

                try:
                    print("Artefact to delete: " + str(obj._object_name) + " in bucket: "+ str(bucket.name))
                    minio_client.remove_object(str(bucket.name), str(obj._object_name))
                except S3Error as exc:
                    print("error occurred while deleting artefact.", exc)


def delete_pods(pod_name):
    print("Deleting pods")
    workflow = pod_name.rsplit('-', 1)[0]

    # configuration = client.Configuration()
    # config.load_incluster_config(client_configuration=configuration)

    v1 = load_verified_api()

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
