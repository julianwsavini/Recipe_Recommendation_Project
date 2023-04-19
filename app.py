
from connector import run_query, get_recipes, get_ingredients
from flask import Flask, Blueprint, render_template, request, jsonify, Response
import pandas as pd
import json


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
    return render_template("index.html", recipe_types=recipe_types, courses=courses, techniques=techniques, cuisines=cuisines)


@app.route('/print_list', methods=['POST'])
def display_string():
    ingredients_list = request.form.get("recipe_ingredients")
    return render_template('index.html', string_value=ingredients_list, recipe_types=recipe_types,
                           courses=courses, techniques=techniques, cuisines=cuisines)


@app.route("/search/<string:box>")
def process(box):
    query = request.args.get('query')
    if box == 'recipe_ingredients':
        # do some stuff to open your names text file
        # do some other stuff to filter
        # put suggestions in this format...
        suggestions = [{'value': x, 'data': x}
                       for x in get_ingredients() if query.lower() in x.lower()]
    if box == 'recipe_name':
        # do some stuff to open your songs text file
        # do some other stuff to filter
        # put suggestions in this format...
        suggestions = [{'value': x, 'data': x}
                       for x in get_recipes() if query.lower() in x.lower()]

    return jsonify({"suggestions": suggestions})


@app.route("/get_text", methods=['POST'])
def get_text():
    name = request.form['recipe_name']
    type = request.form['recipe_types']
    course = request.form['courses']
    technique = request.form['techniques']
    cuisine = request.form['cuisines']
    ingredients = request.form['ingredients']
    dct = {'name': name, 'recipeType': type, 'course': course,
           'technique': technique, 'cuisine': cuisine, 'ingredients': ingredients}
    dct = {key: val for key, val in dct.items() if val !=
           'None Selected' and val != ''}
    rslt = run_query(dct)
    return render_template("index.html", recipe_types=recipe_types,
                           courses=courses, techniques=techniques, cuisines=cuisines, recommendations=rslt)


@app.route("/clear_results")
def clear_variables():
    return render_template("index.html")


if __name__ == '__main__':
    app.run(debug=True, port=8000)
