import boto3
import json
import os 
from sqlalchemy import URL

def get_secret(secret_arn):
    if not secret_arn:
        raise ValueError("Secret name must be provided")
        
    client = boto3.client("secretsmanager")

    response = client.get_secret_value(SecretId=secret_arn)
    secret = json.loads(response["SecretString"])

    return secret

def get_db_url():
    secret_arn = os.getenv("DB_SECRET_ARN")
    if not secret_arn:
        return "sqlite:///test.db"
    host = os.getenv("DB_HOST")
    port = os.getenv("DB_PORT")
    database = os.getenv("DB_NAME")

    secret = get_secret(secret_arn)
    username = secret["username"]
    password = secret["password"]

    db_url = URL.create(
        drivername="postgresql+psycopg2",
        username=username,
        password=password,
        host=host,
        port=int(port),
        database=database
    )

    return db_url

