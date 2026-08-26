#Imports
from flask import Flask , render_template, redirect, request
from flask_scss import Scss
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
from sqlalchemy import or_
import requests
from apipractice import get_token, api_search, location_search, id_specific_search
from dotenv import load_dotenv
import os

load_dotenv()
client_id = os.getenv("CLIENT_ID")
client_secret = os.getenv("CLIENT_SECRET")
token = get_token()

#app setup
app = Flask(__name__)
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///grocery.db"
db = SQLAlchemy(app)
Scss(app)

#data class aka row of data,, why not self why dbmodel, ask to explain. also ask why content and how it works and links together , where does it come from initially and how does it link together
class Product(db.Model):
    id=db.Column(db.Integer, primary_key=True)
    content=db.Column(db.String(100), nullable=False)
    prices= db.relationship("Price", backref="product")
    search_term= db.Column(db.String(100))
    def __repr__(self) -> str:
        return f"Product {self.id}: {self.content}"

class Store(db.Model):
    id=db.Column(db.Integer, primary_key=True)
    chain=db.Column(db.String(50))
    locationid=db.Column(db.Integer, nullable=False)
    city=db.Column(db.String(50), nullable=False)
    prices = db.relationship("Price", backref="store")

class Price(db.Model):
    id=db.Column(db.Integer, primary_key=True)
    product_id = db.Column(db.Integer,db.ForeignKey("product.id"))
    store_id=db.Column(db.Integer,db.ForeignKey("store.id"))
    price=db.Column(db.Float)
    size=db.Column(db.String(50))
    u_o_m=db.Column(db.String(50))

##admin page, THIS WAS HOME
@app.route("/admin",methods=["POST","GET"])

def admin():

    ##add a task  research later whats going on with new task being current task, ask where task came from and how this shit is getting in the database
    if request.method == "POST":
        try:
            current_product= request.form["content"].lower().strip()
            zipcode = request.form["zipcode"]
            api_data = fetch_product(token, current_product, zipcode)
            
            save_to_db(api_data, current_product)
            return redirect("/admin")
        except Exception as e:
            print(f"ERROR {e}")
            return f"ERROR {e}"
    ## see current tasks
    else:
        product = Product.query.all()
        #print(product)
        store = Store.query.all()
        #print(store)
        price = Price.query.all()
        #print(price)
        return render_template("admin.html", product=product, store=store, price=price)

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
    #searched_price = save_to_db(api_data, search_term)
        
    return render_template("index.html", products=api_data, search_term=search_term)

##select product to retrieve price and store to db
@app.route("/select-product", methods=["GET"])
def select_price():
    item_id= request.args.get("item_id")
    locationid= request.args.get("locationid")
    chain_name= request.args.get("chain_name")
    search_term = request.args.get("search_term")
    city= request.args.get("city")
    print("ITEM ID:", item_id)
    print("LOCATION ID:", locationid)
    print(request.args)
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
    print(api_product[0])
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
                content=api_data["product_name"],
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
            return f"ERROR {e}"
    
    

##runner and debugger
if __name__ == "__main__":
    #use this to create database
    with app.app_context():
        db.create_all()
    #this created database
    app.run(debug=True)

