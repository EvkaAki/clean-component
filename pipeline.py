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


@component(
    base_image='python:3.10',  # Specify the base image
    packages_to_install=['pandas']  # List any required packages
)
def mock_model(data_path: InputPath(), model_path: OutputPath()):
    import pandas as pd
    import pickle

    df = pd.read_csv(data_path)
    with open(model_path, 'wb') as f:
        pickle.dump(df, f)
    f.close()
    print(df.head(3))


@dsl.pipeline(name='clean_experiment')
def pipeline(url: str):
    data_job = web_downloader_op(url=url)
    mock_model_task = mock_model(data_path=data_job.outputs['data_path'])

    sign_task = sign_data_op(artefact_path=mock_model_task.outputs['model_path']).after(mock_model_task)
    clean_data_op(pod_path = data_job.outputs['pod_path']).after(sign_task)


if __name__ == '__main__':
    kfp.compiler.Compiler().compile(pipeline, 'pipeline.yaml')

