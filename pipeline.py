import kfp
from kfp import dsl
from kfp.dsl import InputPath, OutputPath, component
from kubernetes.client.models import V1EnvVar, V1SecretKeySelector

web_downloader_op = kfp.components.load_component_from_url(
    'https://raw.githubusercontent.com/EvkaAki/download-component/master/component.yaml'
    )

clean_data_op = kfp.components.load_component_from_url(
    'https://raw.githubusercontent.com/EvkaAki/clean-component/master/component.yaml'
    )


sign_data_op = kfp.components.load_component_from_url(
    'https://raw.githubusercontent.com/EvkaAki/sign-artefact/master/component.yaml'
    )

secret_env = V1EnvVar(
    name='PRIVATE_KEY',
    value_from=V1SecretKeySelector(
        name='my-private-key',
        key='private_key.pem',
        optional=False
    )
)
@component(
    base_image='python:3.10',  # Specify the base image
    packages_to_install=['pandas']  # List any required packages
)
def print_csv(data_path: InputPath(), model_path: OutputPath()):
    import pandas as pd
    df = pd.read_csv(data_path)
    index = df.index
    number_of_rows = len(index)
    f = open(model_path, "w")
    f.write('Number of lines in dataset: ' + str(number_of_rows))
    f.close()
    print(df.head(3))


@dsl.pipeline(name='clean_experiment')
def pipeline(url: str):
    data_job = web_downloader_op(url=url)

    print_csv_task = print_csv(data_path=data_job.outputs['data_path'])
#     sign_task = sign_data_op(artefact_name=str(print_csv_task.outputs['model_path'])).after(print_csv_task)
    # sign_task.container.add_env_variable(secret_env)
    clean_data_op(pod_path=str(data_job.outputs['pod_path'])).after(print_csv_task)


if __name__ == '__main__':
    kfp.compiler.Compiler().compile(pipeline, 'pipeline.yaml')

