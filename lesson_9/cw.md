IP - `111.88.243.32`
PORT - `8123`
DATABASE - `<your_login>_db`

```python 

import boto3
import urllib3
import datetime
from botocore.client import Config

urllib3.disable_warnings()


endpoint_url = 'https://storage.yandexcloud.net'
access = os.getenv('ACCESS_KEY')
secret = os.getenv('SECRET_KEY')
bucket = 'dad-ksu-datalab'

session = boto3.session.Session()
s3 = session.client(
    service_name='s3',
    #region_name=region,
    endpoint_url=endpoint_url,
    aws_access_key_id=access,
    aws_secret_access_key=secret,
    verify=False
)


start_after = ''
obj_lst = []
while True:
    objs = s3.list_objects_v2(Bucket=bucket, StartAfter=start_after)

    if objs['KeyCount'] > 0:
        start_after = objs['Contents'][-1]['Key']
    else:
        break

    obj_lst += [i['Key'] for i in objs['Contents']]

print(obj_lst)


for key in obj_lst:
    if key not in objs_prod:
        print(key, 'start', datetime.datetime.now())
        get_object_response = s3.get_object(Bucket=bucket,Key=key)
        data = get_object_response['Body'].read()
        with open('buffer.parquet', 'wb') as file:
            file.write(data)
        s3_prod.upload_file('buffer.csv', bucket_prod, key)
        print(key, 'complete', datetime.datetime.now())

for file in to_del:
    res = s3_prod.delete_object(Bucket=bucket_prod, Key=file)    
    print(file, res['ResponseMetadata']['HTTPStatusCode'])

```