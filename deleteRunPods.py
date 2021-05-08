from kubernetes import client, config
from kubernetes.client.rest import ApiException
from minio import Minio
from minio.error import S3Error
import os
import urllib3
import split
import argparse
import re

def dump(obj):
   for attr in dir(obj):
       if hasattr( obj, attr ):
           print( "obj.%s = %s" % (attr, getattr(obj, attr)))

def main():
    config.load_incluster_config()
    v1 = client.CoreV1Api()
    current_namespace = open("/var/run/secrets/kubernetes.io/serviceaccount/namespace").read()

    parser = argparse.ArgumentParser(description='Find and delete run pods.')
    parser.add_argument('--pod-path', type=str,
      help='Path of the local file containing the Pod name.')
    args = parser.parse_args()
    pod_name = args.pod_path
    workflow = pod_name.rsplit('-', 1)[0]

    print("Workflow name: "+ str(workflow))
    print("Pod name: "+ str(pod_name))

    minio_client = Minio (
        "minio-service.kubeflow.svc.cluster.local:9000",
        access_key = 'minio',
        secret_key = 'minio123',
        secure = False
    )

    buckets = minio_client.list_buckets()
    for bucket in buckets:
        print(bucket.name, bucket.creation_date)
        objects = minio_client.list_objects(bucket.name, recursive=True,start_after=None, include_user_meta=True)
        object_names = []
        for obj in objects:
            object_names.append(obj._object_name)

    object_names = [obj for obj in object_names if re.match(r"[.]*"+str(pod_name)+"[.]*", obj)]
#     minio_client.remove_object(bucket.name, obj._object_name)
    print("stop")
    print(object_names)
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