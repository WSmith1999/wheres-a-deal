from app import db, Users, Alerts, Price
from dotenv import load_dotenv
import os

def lambda_handler(event, context):
    print("Lambda test")

    return{
        "statusCode":200,
        "body": "Price check lambda"
    }