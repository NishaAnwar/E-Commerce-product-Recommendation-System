from flask import Flask,request,render_template,session
import pandas as pd
import  random
from flask_sqlalchemy import SQLAlchemy
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
app=Flask(__name__)
trending_products=pd.read_csv("models/trending_products.csv")
training_data=pd.read_csv("models/clean_data.csv")



#Database Configuration Setup


app.secret_key="12345fghutrsabut"
app.config['SQLALCHEMY_DATABASE_URI']="mysql://root:@localhost/ecommerce"
app.config['SQLALCHEMY_TRACK_MODIFICATIONS']=False
db=SQLAlchemy(app)

class Signup(db.Model):

    id=db.Column(db.Integer, primary_key=True)
    username=db.Column(db.String(100),nullable=False)
    email=db.Column(db.String(100),nullable=False)
    password=db.Column(db.String(100),nullable=False)


class Signin(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(100), nullable=False)
    password = db.Column(db.String(100), nullable=False)


image_urls=["static/images/image_1.jpg","static/images/image_2.jpg","static/images/image_3.jpg","static/images/image_4.jpg"
    ,"static/images/image_5.jpg","static/images/image_6.jpg","static/images/image_7.jpg","static/images/image_8.jpg","static/images/image_9.jpg","static/images/image_10.jpg"]





def truncate(text,length):
    if len(text) > length:
        return text[:length] + "..."
    else:
        return text

price_list=[100,70,230,400,150,340,290,670]


def content_based_recommendations(train_data, item_name, top_n):
    top_n = int(top_n)

    # Find products that contain the given item_name as a substring (case-insensitive)
    matching_items = train_data[train_data['Name'].str.contains(item_name, case=False, na=False)]

    if matching_items.empty:
        print(f"No products found containing '{item_name}' in their name.")
        return pd.DataFrame()

    # If multiple products match, pick the first one (or let the user specify further)
    item_index = matching_items.index[0]

    # Create a TF-IDF vectorizer for item descriptions
    tfidf_vectorizer = TfidfVectorizer(stop_words='english')

    # Apply TF-IDF vectorization to item descriptions
    tfidf_matrix_content = tfidf_vectorizer.fit_transform(train_data['Tags'])

    # Calculate cosine similarity between items based on descriptions
    cosine_similarities_content = cosine_similarity(tfidf_matrix_content, tfidf_matrix_content)

    # Get the cosine similarity scores for the selected item
    similar_items = list(enumerate(cosine_similarities_content[item_index]))

    # Sort similar items by similarity score in descending order
    similar_items = sorted(similar_items, key=lambda x: x[1], reverse=True)

    # Get the top N most similar items (excluding the item itself)
    top_similar_items = similar_items[1:]  # Get all similar items first

    # Filter out items without images and select the top N with valid images
    recommended_item_indices = [
        x[0] for x in top_similar_items
        if pd.notna(train_data.iloc[x[0]]['ImageURL']) and train_data.iloc[x[0]]['ImageURL'].strip() != ''
    ][:top_n]

    # Get the details of the top similar items with valid images
    recommended_items_details = train_data.iloc[recommended_item_indices][
        ['Name', 'ReviewCount', 'Brand', 'ImageURL', 'Rating']]

    return recommended_items_details

###########################################Routes##########################################
@app.route("/")
def index():
    # Create a list of random image URLs for each product
    random_product_image_urls = [random.choice(image_urls) for _ in range(len(trending_products))]
    price = [40, 50, 60, 70, 100, 122, 106, 50, 30, 50]
    return render_template('index.html',trending_products=trending_products.head(8),truncate = truncate,
                           random_product_image_urls=random_product_image_urls,
                           random_price = random.choice(price))

@app.route('/signup', methods=['POST','GET'])
def signup():
    if request.method == 'POST':
        username=request.form['username']
        email=request.form['email']
        password=request.form['password']

        new_signup_form=Signup(username=username,email=email,password=password)
        db.session.add(new_signup_form)
        db.session.commit()
        # Create a list of random image URLs for each product
        random_product_image_urls = [random.choice(image_urls) for _ in range(len(trending_products))]
        price = [40, 50, 60, 70, 100, 122, 106, 50, 30, 50]
        return render_template('index.html', trending_products=trending_products.head(8), truncate=truncate,
                               random_product_image_urls=random_product_image_urls,
                               random_price=random.choice(price),signup_message='Successful SignUp!')


@app.route('/signin', methods=['POST', 'GET'])
def signin():
    if request.method == 'POST':
        username = request.form['signinUsername']
        password = request.form['signinPassword']
        new_signup = Signin(username=username,password=password)
        db.session.add(new_signup)
        db.session.commit()

        # Create a list of random image URLs for each product
        random_product_image_urls = [random.choice(image_urls) for _ in range(len(trending_products))]
        price = [40, 50, 60, 70, 100, 122, 106, 50, 30, 50]
        return render_template('index.html', trending_products=trending_products.head(8), truncate=truncate,
                               random_product_image_urls=random_product_image_urls,random_price=random.choice(price),
                               signup_message='User signed in successfully!'
                               )
        # Create a list of random image URLs for each product


@app.route("/recommendations", methods=['POST', 'GET'])
def recommendations():
    content_based_rec = None  # Default value for GET or in case of no recommendations

    if request.method == 'POST':
        prod = request.form.get('prod')
        nbr = int(request.form.get('nbr'))

        content_based_rec = content_based_recommendations(training_data, prod,top_n=nbr)
        if content_based_rec is None:
            content_based_rec = pd.DataFrame()

        if content_based_rec.empty:
            message = "No recommendations available for this product."
            return render_template('main.html', message=message, content_based_rec=pd.DataFrame())

        # Create a list of random image URLs for each recommended product
        random_product_image_urls = [random.choice(image_urls) for _ in range(len(content_based_rec))]
        price = [40, 50, 60, 70, 100, 122, 106, 50, 30, 50]

        return render_template(
            'main.html',
            content_based_rec=content_based_rec,
            truncate=truncate,
            random_product_image_urls=random_product_image_urls,
            random_price=random.choice(price),
        )

    # Handle GET requests (e.g., initial page load)
    return render_template('main.html', content_based_rec=content_based_rec)


@app.route('/')
def home():
    return render_template('index.html')

@app.route('/main', methods=['GET', 'POST'])
def main():
    return render_template('main.html')


"""@app.route('/main')
def main():
    return render_template('main.html')"""
@app.route('/Settings')
def settings():
    return render_template('index.html')

@app.route("/index")
def indexredirect():
    # Create a list of random image URLs for each product
    random_product_image_urls = [random.choice(image_urls) for _ in range(len(trending_products))]
    price = [40, 50, 60, 70, 100, 122, 106, 50, 30, 50]
    return render_template('index.html',trending_products=trending_products.head(8),truncate=truncate,
                           random_product_image_urls=random_product_image_urls,
                           random_price=random.choice(price))
###################################Cart portion##############################
from flask import Flask, render_template, request, redirect, url_for
import os
import json



# File path to store cart items
CART_FILE = "Ali.json"

# Helper function to load cart items
def load_cart():
    try:
        with open(CART_FILE, 'r') as file:
            cart_items = json.load(file)
            # Validate each item in the cart
            return [
                item for item in cart_items
                if isinstance(item, dict) and 'Name' in item
            ]
    except (FileNotFoundError, json.JSONDecodeError):
        return []


# Helper function to save cart items
def save_cart(cart_items):
    with open(CART_FILE, 'w') as file:
        json.dump(cart_items, file)

@app.route('/add_to_cart', methods=['POST'])
def add_to_cart():
    product = request.json  # Receive product data as JSON
    cart_items = load_cart()
    cart_items.append(product)
    save_cart(cart_items)
    return {"status": "success"}, 200


@app.route('/remove_from_cart', methods=['POST'])
def remove_from_cart():
    data = request.json  # Get JSON payload
    product_name = data.get('Name')  # Get the product name


    cart_items = load_cart()  # Load current cart items

    # Filter out the product to be removed
    updated_cart = [item for item in cart_items if item['Name'] != product_name]

    save_cart(updated_cart)  # Save updated cart

    return {"status": "success", "message": f"{product_name} removed successfully"}, 200


@app.route('/cart')
def view_cart():
    cart_items = load_cart()
    return render_template('cart.html', cart_items=cart_items)



if __name__ == '__main__':
    app.run(debug=True)
