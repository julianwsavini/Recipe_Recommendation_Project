from flask import Flask, Blueprint, render_template, request
from connector import run_query, get_recipes
import pandas as pd


recipe_types = ['None Selected', 'YummlyOriginal',
                'BasicRecipe', 'ProRecipe', 'GuidedRecipe']

courses = ['None Selected', 'Main Dishes', 'Appetizers', 'Side Dishes', 'Desserts', 'Beverages',
           'Salads', 'Breakfast and Brunch', 'Soups', 'Condiments and Sauces', 'Breads',
           'Lunch', 'Cocktails']

techniques = ['None Selected', 'Grilling', 'Blending', 'Baking', 'Boiling', 'Browning', 'Glazing',
              'Roasting', 'Microwaving', 'Broiling', 'Frying', 'Drying', 'Sauteeing',
              'Slow Cooking', 'Marinating', 'Steaming', 'Frosting', 'Pressure Cooking',
              'Braising', 'Pickling', 'Stir Frying', 'Brining']

cuisines = ['None Selected', 'Barbecue', 'Turkish', 'Kid-Friendly', 'American', 'Indian',
            'Southern & Soul Food', 'Italian', 'Chinese', 'Asian', 'Greek', 'Southwestern',
            'Mexican', 'Moroccan', 'Puerto rican' 'Filipino', 'Japanese', 'Thai' 'Korean',
            'English', 'French', 'Jewish', 'Cajun & Creole', 'Caribbean', 'Arab', 'Cuban',
            'Mediterranean', 'Spanish']


app = Flask(__name__, template_folder="templates", static_folder="staticFiles")


@app.route("/")
def index():
    return render_template("index.html", recipe_types=recipe_types, courses=courses, techniques=techniques, users=users, cuisines=cuisines)


@app.route('/print_list', methods=['POST'])
def display_string():
    ingredients_list = "hi"
    return render_template('index.html', string_value=ingredients_list, recipe_types=recipe_types,
                           courses=courses, techniques=techniques, users=users, cuisines=cuisines)


@app.route("/get_text", methods=['POST'])
def get_text():
    name = request.form['recipe_name']
    type = request.form['recipe_types']
    course = request.form['courses']
    technique = request.form['techniques']
    cuisine = request.form['cuisines']
    ingredients = request.form['recipe_ingredients']
    input_user = request.form['users']
    dct = {'name': name, 'recipeType': type, 'course': course,
           'technique': technique, 'cuisine': cuisine, 'ingredients': ingredients}
    dct = {key: val for key, val in dct.items() if val !=
           'None Selected' and val != ''}
    rslt = run_query(dct)
    print(rslt)

    recipes = get_recipes()
    print(recipes)
    # print(name, type, course, technique, cuisine, ingredients, input_user)
    return render_template("index.html", recipe_types=recipe_types,
                           courses=courses, techniques=techniques, users=users, cuisines=cuisines)


@app.route("/clear_results")
def clear_variables():

    return render_template("index.html")


def read_csv(filename):
    df = pd.read_csv(filename)
    return df


if __name__ == '__main__':
    users_df = read_csv('data/mock_users.csv')
    users = users_df['user'].unique()
    users[:0] = ['None Selected']
    app.run(debug=True, port=8000)
