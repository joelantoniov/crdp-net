from airflow import DAG
from airflow.operators.python import PythonOperator
from airflow.providers.amazon.operators.emr import EmrAddStepsOperator, EmrCreateJobFlowOperator
from airflow.providers.amazon.sensors.emr import EmrStepSensor
from datetime import datetime, timedelta
import boto3

# Default arguments for the DAG
default_args = {
    'owner': 'crdp_net_team',
    'depends_on_past': False,
    'email_on_failure': True,
    'email': ['alerts@crdp-net.org'],
    'retries': 3,
    'retry_delay': timedelta(minutes=5),
}

# Initialize the DAG
dag = DAG(
    'crdp_pipeline',
    default_args=default_args,
    description='CRDP-Net Data Pipeline',
    schedule_interval='*/5 * * * *',  # Run every 5 minutes
    start_date=datetime(2025, 4, 25),
    catchup=False,
)

# Define regions and their assigned EMR clusters
REGIONS = {
    'Asia': ['Jakarta', 'Bali', 'Tokyo'],
    'NorthAmerica': ['NewYork', 'LosAngeles'],
    'Europe': ['London', 'Paris']
}
EMR_CLUSTERS = {
    'Asia': 'emr-cluster-asia',
    'NorthAmerica': 'emr-cluster-na',
    'Europe': 'emr-cluster-eu'
}

# Task 1: Run streaming_job.py for each region
def submit_streaming_job(region, cluster_id, **kwargs):
    emr_client = boto3.client('emr')
    step = {
        'Name': f'StreamingJob_{region}',
        'ActionOnFailure': 'CONTINUE',
        'HadoopJarStep': {
            'Jar': 'command-runner.jar',
            'Args': [
                'spark-submit',
                '--deploy-mode', 'cluster',
                '--master', 'yarn',
                f's3://crdp-net/scripts/streaming_job.py',
                '--region', region
            ]
        }
    }
    response = emr_client.add_job_flow_steps(JobFlowId=cluster_id, Steps=[step])
    return response['StepIds'][0]

streaming_tasks = {}
for cluster_name, regions in REGIONS.items():
    cluster_id = EMR_CLUSTERS[cluster_name]
    for region in regions:
        task_id = f'streaming_job_{region}'
        streaming_task = EmrAddStepsOperator(
            task_id=task_id,
            job_flow_id=cluster_id,
            steps=[],
            python_callable=submit_streaming_job,
            python_args=[region, cluster_id],
            dag=dag
        )
        streaming_sensor = EmrStepSensor(
            task_id=f'monitor_{task_id}',
            job_flow_id=cluster_id,
            step_id="{{ task_instance.xcom_pull(task_ids='" + task_id + "') }}",
            dag=dag
        )
        streaming_task >> streaming_sensor
        streaming_tasks[region] = streaming_sensor

# Task 2: Run watermark analysis daily
def submit_watermark_analysis(**kwargs):
    emr_client = boto3.client('emr')
    step = {
        'Name': 'WatermarkAnalysis',
        'ActionOnFailure': 'CONTINUE',
        'HadoopJarStep': {
            'Jar': 'command-runner.jar',
            'Args': [
                'spark-submit',
                '--deploy-mode', 'cluster',
                '--master', 'yarn',
                's3://crdp-net/scripts/analyze_watermark.py'
            ]
        }
    }
    response = emr_client.add_job_flow_steps(JobFlowId=EMR_CLUSTERS['Asia'], Steps=[step])
    return response['StepIds'][0]

watermark_task = EmrAddStepsOperator(
    task_id='watermark_analysis',
    job_flow_id=EMR_CLUSTERS['Asia'],
    steps=[],
    python_callable=submit_watermark_analysis,
    dag=dag
)
watermark_sensor = EmrStepSensor(
    task_id='monitor_watermark_analysis',
    job_flow_id=EMR_CLUSTERS['Asia'],
    step_id="{{ task_instance.xcom_pull(task_ids='watermark_analysis') }}",
    dag=dag
)
watermark_task >> watermark_sensor

# Dependencies
for region, task in streaming_tasks.items():
    task >> watermark_task
