#Imports
from flask import Flask , render_template, redirect, request, session, flash
from flask_scss import Scss
from datetime import datetime
from sqlalchemy import or_
import requests
from apipractice import get_token, api_search, location_search, id_specific_search
from models import db, Product, Store, Price, Users, Alerts
from alert_functions import get_alert_status
from dotenv import load_dotenv
import os
import secrets


load_dotenv()
client_id = os.getenv("CLIENT_ID")
client_secret = os.getenv("CLIENT_SECRET")
token = get_token()

#app setup
app = Flask(__name__)
app.secret_key = os.getenv("app_secret_key")
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///grocery.db"
db.init_app(app)
Scss(app)

##admin page, THIS WAS HOME
@app.route("/admin",methods=["POST","GET"])
def admin():
    if "user_id" not in session:
        return redirect("/adminlogin")

    user = db.session.get(Users, session["user_id"])

    if not user.admin:
        return redirect("/adminlogin")
    
    product = Product.query.all()
    store = Store.query.all()
    price = Price.query.all()
    users = Users.query.all()
    alerts = Alerts.query.all()
    return render_template("admin.html", product=product, store=store, price=price, users=users, alerts=alerts)

@app.route("/adminlogin", methods=["POST","GET"])
def adlogin():
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]
        user = Users.query.filter_by(username=username).first()
        if user and user.password_check(password) and user.admin:
            session["user_id"]=user.id
            return redirect("/admin")
        
    return render_template("adminlogin.html", message="please login to view admin page")

@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]
        user = Users.query.filter_by(username=username).first()
        if user and user.password_check(password):
            session["user_id"] = user.id
            return redirect("/")
    return render_template("login.html")

@app.route("/logout")
def logout():
    session.pop("user_id", None)
    return redirect("/")

@app.route("/register", methods=["GET", "POST"])
def register():
     if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]
        email = request.form["email"]
        existing_username = Users.query.filter_by(username=username).first()
        existing_email = Users.query.filter_by(email=email).first()

        if existing_username:
            return render_template("register.html", message="Username already exists")
        
        if existing_email:
            return render_template("register.html", message="Email already exists")
        
        user = Users(
            username = username,
            password = password,
            email = email
        )

        db.session.add(user)
        db.session.commit()
        session["user_id"] = user.id
        return render_template("index.html", message = "Account created")
     return render_template("register.html")

## delete an item
@app.route("/delete/<int:id>")
def delete(id:int):
    delete_price = Price.query.get_or_404(id)
    try:
        db.session.delete(delete_price)
        db.session.commit()
        return redirect("/admin")
    except Exception as e:
        return f"ERROR {e}"

@app.route("/delete-user/<int:id>")
def delete_user(id:int):   
    delete_user = Users.query.get_or_404(id)
    try:
        db.session.delete(delete_user)
        db.session.commit()
        return redirect("/admin")
    except Exception as e:
        return f"ERROR {e}"

@app.route("/delete-alert/<int:id>")
def delete_alert(id:int):   
    delete_alert = Alerts.query.get_or_404(id)
    try:
        db.session.delete(delete_alert)
        db.session.commit()
        return redirect(request.referrer or "/alerts")
    except Exception as e:
        return f"ERROR {e}"

## edit an item , make sure the route matches the route in HTML and the method
@app.route("/update/<int:id>", methods=["GET", "POST"])
def update(id:int):
    price = Price.query.get_or_404(id)
    if request.method == "POST":
        price.price = request.form["price"]
        try:
            db.session.commit()
            return redirect("/admin")
        except Exception as e:
            return f"ERROR {e}"
    else:
        return render_template("edit.html", price=price)
    
##New home page
@app.route("/", methods=["GET"])
def home():
    search_term = request.args.get("search")
   
    if not search_term or not search_term.strip():
       return render_template("index.html", message="Please enter a search term")

    search_term = search_term.lower().strip()
    searched_price = search(search_term)

    if searched_price:
        return render_template("index.html", searched_price=searched_price)
    
    zipcode = request.args.get("zipcode")
    api_data = fetch_product(token, search_term, zipcode)
    if not api_data:
        return render_template("index.html", message="enter a valid search term")
    
        
    return render_template("index.html", products=api_data, search_term=search_term)

##select product to retrieve price and store to db
@app.route("/select-product", methods=["GET"])
def select_price():
    item_id= request.args.get("item_id")
    locationid= request.args.get("locationid")
    chain_name= request.args.get("chain_name")
    search_term = request.args.get("search_term")
    city= request.args.get("city")
    api_data = id_specific_search(token, item_id, locationid)
    api_product = api_data["data"][0]


    product_name = api_product["description"]
    price = api_product["items"][0]["price"]["regular"]
    #determine unit of measurment u_o_m
    size = api_product["items"][0]["size"]
    sold_by = api_product["items"][0]["soldBy"]
    if sold_by == "WEIGHT":
        u_o_m = "Per LB"
    else:
        u_o_m = "Per Unit"
    
    selected_data = {
        "locationid": locationid,
        "chain_name": chain_name,
        "product_name": product_name,
        "price": price,
        "city": city,
        "size": size,
        "u_o_m": u_o_m
    }

    searched_price = save_to_db(selected_data, search_term)
    return render_template("index.html", searched_price = searched_price )

## homemade search function
def search(search_term):
    results = Price.query.join(Product).join(Store).filter(
        or_(
            Product.search_term == search_term
        )
    ).all()
    print(results)
    return results
    

def fetch_product(token, product, zipcode):

    loc_search = location_search(token, zipcode)
    ##if an invalid search occurs data will return empty
    if not loc_search or not loc_search["data"]:
        return None
    location = loc_search["data"][0]
    locationid = location["locationId"]

    chain_name = location["chain"]
    city = location["address"]["city"]

    api_results = api_search(token,product,locationid)
    ##if an invalid search occurs data will return empty
    if not api_results["data"]:
        return None
    api_product = api_results["data"][:4]
    
    for product in api_product:
        product["locationId"] = locationid
        product["chain_name"] = chain_name
        product["city"] = city
    return api_product

    
def save_to_db(api_data,search_term):
        try:
            product = Product.query.filter_by(search_term=search_term).first()
            
            if product:
                return Price.query.filter_by(product_id=product.id).all()

            product = Product(
                name=api_data["product_name"],
                search_term = search_term
            )
            db.session.add(product)
            db.session.flush()

            store = Store.query.filter_by(locationid=api_data["locationid"]).first()
            if store is None:
                store = Store(
                    chain = api_data["chain_name"],
                    locationid = api_data["locationid"],
                    city = api_data["city"]
                )
            db.session.add(store)
            db.session.flush()

            new_price = Price(
                price = api_data["price"],
                product_id = product.id,
                store_id = store.id,
                size = api_data["size"],
                u_o_m = api_data["u_o_m"]

            )
            db.session.add(new_price)

            db.session.commit()
            return [new_price]
            
        except Exception as e:
            print(f"ERROR {e}")
            raise

@app.route("/create-alert", methods=["GET", "POST"])
def create_alert():
    user_id = session.get("user_id")
    user = db.session.get(Users, user_id)

    if user is None:
        session.clear()
        flash("Please login to create alerts")
        return redirect("/login")

    
    
    if request.method == "POST":
        product_id = request.form["product_id"]
        store_id = request.form["store_id"]
        target_price = request.form["target_price"]
        email = request.form["email"]
        alert = Alerts(
            product_id = product_id,
            user_id = user_id,
            store_id = store_id,
            target_price = target_price,
            email = email,
            active = True
            )
        db.session.add(alert)
        db.session.commit()
        return render_template("index.html", message = "Alert sucessfully created!")

@app.route("/alerts")
def alerts():
    if "user_id" not in session:
        return redirect("/login")

    get_alert_status()
    
    user_id = session["user_id"]
    username = Users.query.get(user_id)
    user_alerts = Alerts.query.filter_by(user_id=user_id).all()
    return render_template("alerts.html", alerts=user_alerts, username=username)

##runner and debugger
if __name__ == "__main__":
    #use this to create database
    with app.app_context():
        db.create_all()
    ## use host = 0.0.0.0 and 5000 to allow any ip to access with ec2
    app.run(host="0.0.0.0", port=5000, debug=True)

