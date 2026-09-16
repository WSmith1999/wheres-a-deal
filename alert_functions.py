from models import db, Alerts, Price
    
def get_alert_status():
    alerts = Alerts.query.filter_by(active=True).all()
    for alert in alerts:
        check_alert(alert)
    

def check_alert(alert):
    price = Price.query.filter_by(product_id = alert.product_id, store_id = alert.store_id).first()
    if price is None:
        return
    
    product= alert.product.name
    current_price = price.price
    
    
    if current_price <= alert.target_price:
        alert.active = False
        db.session.commit()
        alert_message(alert, product, price)


def alert_message(alert, product, price):
        message = f"Price Alert! {product} is on sale for ${price.price}!"
        print(message)
        return message
