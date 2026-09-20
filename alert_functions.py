from models import db, Alerts, Price
from api_functions import get_token, api_search, location_search, id_specific_search


def get_alert_status():
    alerts = Alerts.query.filter_by(active=True).all()
    for alert in alerts:
        check_alert(alert)
    print("got alerts")
    

def check_alert(alert):
    print("calling kroger")
    token = get_token()
    price_check = id_specific_search(token, alert.product.kroger_item_id, alert.store.locationid)
    print("Kroger item:", alert.product.kroger_item_id)
    print("Location:", alert.store.locationid)
    print("API result:", price_check)
    new_data = price_check["data"][0]
    new_price = new_data["items"][0]["price"]["regular"]
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
        print(message)
        return message
