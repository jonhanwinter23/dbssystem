from flask import Flask, request, render_template, redirect, flash, send_from_directory, jsonify, url_for,session
from werkzeug.utils import secure_filename
import sqlite3
import os
from datetime import datetime

app = Flask(__name__)

app.secret_key = 'super secret key'
app.config['SESSION_TYPE'] = 'filesystem'


# Define the upload folder
UPLOAD_FOLDER = 'uploads'
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg'}
def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


# Predefined username and password
valid_username = "admin"
valid_password = "password"


# Authentication function
def authenticate(username, password):
    return username == valid_username and password == valid_password


# Home route
@app.route('/', methods=['GET', 'POST'])
def home():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')

        if authenticate(username, password):
            session['authenticated'] = True
            return redirect(url_for('dashboard'))

    return render_template('home.html')


# Dashboard route (requires authentication)
@app.route('/dashboard')
def dashboard():
    if session.get('authenticated'):
        return render_template('dashboard.html')
    else:
        return redirect(url_for('home'))


# Logout route
@app.route('/logout')
def logout():
    session.pop('authenticated', None)
    return redirect(url_for('home'))
@app.route('/uploads/<filename>')
def uploaded_file(filename):
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename)

@app.route('/add_new_recipe', methods=['GET', 'POST'])
def add_new_recipe():
    if request.method == 'POST':
        # Handle form submission to add new recipe
        name = request.form['name']
        quantity = request.form['quantity']
        price = request.form['price']
        category = request.form['category']
        unit = request.form['unit']

        # Handle file upload
        if 'image' in request.files:
            file = request.files['image']
            if file.filename == '':
                flash('No selected file')
                return redirect(request.url)
            if file and allowed_file(file.filename):
                filename = secure_filename(file.filename)
                file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
                # Now 'filename' contains the name of the saved file, you can store it in the database if needed
            else:
                flash('Invalid file type')
                return redirect(request.url)

        # Use a context manager to manage the database connection
        with sqlite3.connect('kitchen.db') as conn:
            c = conn.cursor()

            # Check if a record with the same name already exists
            c.execute("SELECT * FROM recipes WHERE name = ?", (name,))
            existing_recipe = c.fetchone()

            if existing_recipe:
                # Update the existing record
                c.execute("UPDATE recipes SET quantity_in_stock = ?, price = ?, category = ?, unit = ?, image = ? WHERE name = ?",
                          (quantity, price, category, unit, filename, name))
            else:
                # Insert a new record
                c.execute(
                    "INSERT INTO recipes (name, quantity_in_stock, price, category, unit, image) VALUES (?, ?, ?, ?, ?, ?)",
                    (name, quantity, price, category, unit, filename))

            conn.commit()

        return render_template('add_new_recipe.html')
    else:
        return render_template('add_new_recipe.html')


@app.route('/add_existing_recipe', methods=['GET', 'POST'])
def add_existing_recipe():
    if request.method == 'POST':
        # Handle adding existing recipe
        name = request.form['name']
        quantity = int(request.form['quantity'])

        conn = sqlite3.connect('kitchen.db')
        c = conn.cursor()
        c.execute("SELECT COUNT(*) FROM recipes WHERE name = ?", (name,))
        recipe_exists = c.fetchone()[0] > 0

        if recipe_exists:
            c.execute("SELECT quantity_in_stock FROM recipes WHERE name = ?", (name,))
            current_quantity = c.fetchone()[0]
            new_quantity = current_quantity + quantity
            c.execute("UPDATE recipes SET quantity_in_stock = ? WHERE name = ?", (new_quantity, name))
            conn.commit()
            conn.close()
            return 'Recipe quantity updated successfully!'
        else:
            conn.close()
            return 'Error: Recipe not found!'
    else:
        conn = sqlite3.connect('kitchen.db')
        c = conn.cursor()
        c.execute("SELECT name FROM recipes")
        recipe_names = c.fetchall()
        conn.close()
        return render_template('add_existing_recipe.html', recipe_names=recipe_names)

# # View database route
# @app.route('/view_database', methods=['GET', 'POST'])
# def view_database():
#     conn = sqlite3.connect('kitchen.db')
#     c = conn.cursor()

#     if request.method == 'POST':
#         selected_category = request.form['category']
#         c.execute("SELECT * FROM recipes WHERE category=?", (selected_category,))
#         recipes = c.fetchall()
#     else:
#         c.execute("SELECT * FROM recipes")
#         recipes = c.fetchall()

#     categories = c.execute("SELECT DISTINCT category FROM recipes").fetchall()

#     conn.close()
#     return render_template('view_database.html', recipes=recipes, categories=categories)

@app.route('/view_database', methods=['GET', 'POST'])
def view_database():
    try:
        conn = sqlite3.connect('kitchen.db')
        c = conn.cursor()

        if request.method == 'POST':
            selected_category = request.form['category']
            c.execute("SELECT * FROM recipes WHERE category=?", (selected_category,))
            recipes = c.fetchall()
        else:
            c.execute("SELECT * FROM recipes")
            recipes = c.fetchall()

        categories = c.execute("SELECT DISTINCT category FROM recipes").fetchall()

        conn.close()
        return render_template('view_database.html', recipes=recipes, categories=categories)

    except sqlite3.Error as e:
        error_message = f"SQLite error: {e}"
        print(error_message)  # Log the error for debugging
        return f"An error occurred: {error_message}", 500  # Return a specific error message and HTTP status code
    except Exception as e:
        error_message = f"An unexpected error occurred: {str(e)}"
        print(error_message)  # Log the error for debugging
        return f"An unexpected error occurred", 500  # Return a generic error message and HTTP status code

# Delete recipe route
@app.route('/delete_recipe/<name>', methods=['POST'])
def delete_recipe(name):
    conn = sqlite3.connect('kitchen.db')
    c = conn.cursor()
    c.execute("DELETE FROM recipes WHERE name = ?", (name,))
    conn.commit()
    conn.close()
    return 'Recipe deleted successfully!'

@app.route('/update_quantity/<name>', methods=['POST'])
def update_quantity(name):
    new_quantity = request.form['new_quantity']
    conn = sqlite3.connect('kitchen.db')
    c = conn.cursor()
    c.execute("UPDATE recipes SET quantity_in_stock = ? WHERE name = ?", (new_quantity, name))
    conn.commit()
    conn.close()
    return redirect(url_for('view_database'))

@app.route('/add_new_menu_item', methods=['GET', 'POST'])
def add_new_menu_item():
    if request.method == 'POST':
        # Handle form submission to add new menu item
        name = request.form['name']
        category = request.form['category']  # Get category from form

        # Collect ingredients and quantities
        ingredients = []
        quantities = []
        for i in range(1, 11):
            ingredient = request.form.get(f'ingredient{i}')
            quantity = request.form.get(f'quantity{i}')
            if ingredient and quantity:
                ingredients.append(ingredient)
                quantities.append(float(quantity))

        # Calculate total cost of ingredients
        total_cost = 0
        conn = sqlite3.connect('kitchen.db')
        c = conn.cursor()
        for ingredient, quantity in zip(ingredients, quantities):
            c.execute("SELECT price FROM recipes WHERE name=?", (ingredient,))
            ingredient_cost = c.fetchone()[0] * quantity
            total_cost += ingredient_cost
        conn.close()

        # Calculate selling prices
        selling_price_75 = total_cost * 1.75
        selling_price_72 = total_cost * 1.72
        selling_price_70 = total_cost * 1.70
        selling_price_65 = total_cost * 1.65
        selling_price_60 = total_cost * 1.60

        # Add new menu item to the database
        conn = sqlite3.connect('menu.db')
        c = conn.cursor()
        c.execute("INSERT INTO menu (name, category, ingredients, quantities, cost, selling_price_75, selling_price_72, selling_price_70, selling_price_65, selling_price_60) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
                  (name, category.lower(), ','.join(ingredients), ','.join(map(str, quantities)), total_cost, selling_price_75, selling_price_72, selling_price_70, selling_price_65, selling_price_60))
        conn.commit()
        conn.close()

        return 'New menu item added successfully!'
    else:
        # Fetch recipe names for dropdown menu
        conn = sqlite3.connect('kitchen.db')
        c = conn.cursor()
        c.execute("SELECT name FROM recipes")
        recipe_names = [row[0] for row in c.fetchall()]
        conn.close()

        return render_template('add_new_menu_item.html', recipe_names=recipe_names)

def update_kitchen_stock(menu_name, quantity):
    try:
        # Connect to the databases
        menu_conn = sqlite3.connect('menu.db')
        kitchen_conn = sqlite3.connect('kitchen.db')
        record_conn = sqlite3.connect('record.db')

        # Retrieve recipe information
        cursor = menu_conn.cursor()
        cursor.execute("SELECT * FROM menu WHERE name=?", (menu_name,))
        recipe_data = cursor.fetchone()

        if recipe_data is None:
            return "Recipe not found"

        # Calculate overall cost based on the cost of ingredients
        overall_cost = recipe_data[4] * quantity

        # Split ingredients and quantities
        ingredients = recipe_data[2].split(',')
        ingredient_quantities = recipe_data[3].split(',')

        # Update kitchen stock
        kitchen_cursor = kitchen_conn.cursor()
        for ingredient, ingredient_quantity in zip(ingredients, ingredient_quantities):
            ingredient_quantity = float(ingredient_quantity) * quantity
            kitchen_cursor.execute("UPDATE recipes SET quantity_in_stock = quantity_in_stock - ? WHERE name=?",
                                   (ingredient_quantity, ingredient,))
            kitchen_conn.commit()

        # Insert update record into the record database
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        record_cursor = record_conn.cursor()
        record_cursor.execute("INSERT INTO updates (timestamp, menu_item_name, overall_cost, quantity) VALUES (?, ?, ?, ?)",
                              (timestamp, menu_name, overall_cost, quantity))
        record_conn.commit()

        return "Stock updated successfully"
    except sqlite3.Error as e:
        return f"SQLite error: {e}"

def get_categorie():
    try:
        conn = sqlite3.connect('menu.db')
        cursor = conn.cursor()
        cursor.execute("SELECT DISTINCT category FROM menu")
        categories = [row[0] for row in cursor.fetchall()]
        conn.close()
        return categories
    except sqlite3.Error as e:
        print(f"SQLite error: {e}")
        return []

@app.route('/update_stock', methods=['GET', 'POST'])
def update_stock():
    if request.method == 'POST':
        selected_menu = request.form['menu_name']
        quantity = int(request.form['quantity'])
        result = update_kitchen_stock(selected_menu, quantity)
        return result
    else:
        categories = get_categorie()
        return render_template('update_stock.html', categories=categories)

def get_menu_item(category):
    try:
        conn = sqlite3.connect('menu.db')
        cursor = conn.cursor()
        cursor.execute("SELECT name FROM menu WHERE category=?", (category,))
        menu_items = [row[0] for row in cursor.fetchall()]
        conn.close()
        return menu_items
    except sqlite3.Error as e:
        print(f"SQLite error: {e}")
        return []

@app.route('/get_menu_item', methods=['POST'])
def get_menu_items():
    selected_category = request.form['selected_category']
    menu_items = get_menu_item(selected_category)
    return jsonify(menu_items=menu_items, selected_category=selected_category)

# Define functions to interact with the database
# Function to connect to the SQLite database
def connect_db():
    return sqlite3.connect('menu.db')

# Route for the home page
@app.route('/menu')
def index():
    # Connect to the database
    conn = connect_db()
    c = conn.cursor()

    # Fetch all distinct categories from the database
    c.execute("SELECT DISTINCT category FROM menu")
    categories = c.fetchall()

    # Close the database connection
    conn.close()

    # Render the index.html template with the categories
    return render_template('menu.html', categories=categories)

# Route to display menu items in a selected category
@app.route('/menu_items', methods=['POST'])
def menu_items():
    # Get the selected category from the form
    selected_category = request.json['category']

    # Connect to the database
    conn = connect_db()
    c = conn.cursor()

    # Fetch menu items in the selected category
    c.execute("SELECT id, name FROM menu WHERE category=?", (selected_category,))
    menu_items = c.fetchall()

    # Close the database connection
    conn.close()

    # Return JSON response
    return jsonify(menu_items=menu_items)

# Route to display details of a selected menu item
@app.route('/menu_item_details/<int:item_id>')
def menu_item_details(item_id):
    # Connect to the database
    conn = connect_db()
    c = conn.cursor()

    # Fetch details of the selected menu item
    c.execute("SELECT * FROM menu WHERE id=?", (item_id,))
    item_details = c.fetchone()

    # Split ingredients and quantities into separate lists
    ingredients = item_details[2].split(',')
    quantities = item_details[3].split(',')

    # Close the database connection
    conn.close()

    # Return JSON response
    return jsonify(item_details=item_details, ingredients=ingredients, quantities=quantities)


def fetch_records(date=None):
    try:
        record_conn = sqlite3.connect('record.db')
        record_cursor = record_conn.cursor()

        # Construct the SQL query
        query = "SELECT * FROM updates WHERE DATE(timestamp) = ?"
        params = [date] if date else []

        # Execute the query
        record_cursor.execute(query, params)
        records = record_cursor.fetchall()

        record_conn.close()

        # Convert records to a list of dictionaries
        records_dict = []
        for record in records:
            record_dict = {
                "update_id": record[0],
                "timestamp": record[1],
                "menu_item_name": record[2],
                "quantity": record[4],  # Fetch quantity from the database
                "overall_cost": record[3]  # Fetch overall_cost from the database
            }
            records_dict.append(record_dict)

        return records_dict
    except sqlite3.Error as e:
        print(f"SQLite error: {e}")
        return []

@app.route('/view_records')
def view_records():
    return render_template('view_records.html')

@app.route('/get_records')
def get_records():
    date = request.args.get('date')
    records = fetch_records(date)
    return jsonify(records)

if __name__ == '__main__':
    app.secret_key = 'super secret key'
    app.config['SESSION_TYPE'] = 'filesystem'

    app.run(debug=True, port=5001)
