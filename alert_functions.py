from models import db, Alerts, Price
from api_functions import get_token, id_specific_search, promo_or_regular
import os
import boto3

sns = boto3.client('sns')


def get_alert_status():
    alerts = Alerts.query.filter_by(active=True).all()
    for alert in alerts:
        check_alert(alert)
    print("got alerts")
    

def check_alert(alert):
    token = get_token()

    price_check = id_specific_search(token, alert.product.kroger_item_id, alert.store.locationid)

    if not price_check or not price_check.get("data"):
         print(f"Could not retrieve data for {alert.product.name}")
         return
    
    new_data = price_check["data"][0]
    new_price = promo_or_regular(new_data)
    price = Price.query.filter_by(product_id = alert.product_id, store_id = alert.store_id).first()

    if price is None:
        return
    
    price.price =  new_price
    product= alert.product.name
    
    if new_price <= alert.target_price:
        alert.active = False
        alert_message(alert, product, price)

    db.session.commit()


def alert_message(alert, product, price):
        message = f"Price Alert! {product} is on sale for ${price.price}!"

        sns.publish(
             TopicArn= os.getenv("SNS_TOPIC_ARN"),
             Subject = "Price Alert",
             Message = message

        )