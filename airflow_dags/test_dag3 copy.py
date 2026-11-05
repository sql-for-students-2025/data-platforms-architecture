import logging


import pandas as pd
from airflow import DAG
from airflow.models import Variable
from airflow.utils.dates import days_ago
from airflow.operators.python_operator import PythonOperator
from airflow.providers.postgres.hooks.postgres import PostgresHook
from airflow.providers.http.hooks.http import HttpHook

import io
import datetime


default_args = {
    'owner': 'airflow',
    'depends_on_past': False,
    'start_date': datetime.datetime(2020, 7, 1, 0, 0),
    'email': ['galbinskiy_va@magnit.ru'],
    'email_on_failure': False,
    'email_on_retry': False,
    'retries': 0,
    'retry_delay': datetime.timedelta(minutes=1),
    'pool': 'default'
}

logger = logging.getLogger("airflow.task")

def test_python ():
    print('HELLO!!!')


with DAG(
    dag_id="test_dag_4",
    default_args=default_args,
    schedule=None,
    start_date=days_ago(0),
    catchup=False,
    tags=["test"],
) as dag:


    t4 = PythonOperator(
        task_id='test_python',
        python_callable=test_python,
        dag=dag
    )

    t4
