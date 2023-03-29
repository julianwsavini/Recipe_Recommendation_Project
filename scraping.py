import requests
import json


def scrape_recipe(dct):
    seo = dct['seo']
    dct = dct['feed'][0]

    recipe = dict()
    # get recipe metadata
    recipe['name'] = dct['display']['displayName']
    recipe['url'] = seo['web']['link-tags'][0]['href']
    recipe['recipeType'] = dct['recipeType'][0]

    recipe['keywords'] = dct['seo']['spotlightSearch']['keywords']

    # recipe description
    if dct['content']['description']:
        recipe['description'] = dct['content']['description']['text']
    else:
        recipe['description'] = ''

    # recipe steps
    if dct['content']['preparationSteps']:
        recipe['steps'] = [x for x in dct['content']['preparationSteps']]
    else:
        recipe['steps'] = []

    # get recipe content
    recipe['tags'] = dict()
    tags = dct['content']['tags'].keys()
    all_tags = ['dish', 'course', 'technique', 'cuisine']
    for tag in all_tags:
        if tag in tags:
            recipe['tags'][tag] = [x['display-name'] for x in dct['content']['tags'][tag]]
        else:
            recipe['tags'][tag] = list()

    # get ingredient data
    recipe['ingredients'] = []
    for ingredient in dct['content']['ingredientLines']:
        ing_dct = dict()
        ing_dct['name'] = ingredient['ingredient']
        ing_dct['category'] = ingredient['category']

        if not ingredient['quantity']:
            ing_dct['quantity'] = dict()
        else:
            ing_dct['quantity'] = {
                'metric': str(ingredient['amount']['metric']['quantity']) + ' ' +
                          ingredient['amount']['metric']['unit'][
                              'abbreviation'],
                'imperial': str(ingredient['amount']['imperial']['quantity']) + ' ' +
                            ingredient['amount']['imperial']['unit']['abbreviation'],
            }

        recipe['ingredients'].append(ing_dct)

    # get review data
    recipe['reviews'] = {'avgRating': dct['content']['reviews']['averageRating'],
                         'numReviews': dct['content']['reviews']['totalReviewCount']}

    # get nutritional data
    recipe['nutrition'] = list()
    for nut in dct['content']['nutrition']['nutritionEstimates']:
        nut_dct = dict()
        nut_dct['name'] = nut['attribute']
        nut_dct['value'] = f"{nut['display']['value']} {nut['unit']['abbreviation']}"
        nut_dct['pctDailyValue'] = nut['display']['percentDailyValue']
        recipe['nutrition'].append(nut_dct)

    return recipe


def scrape_feed(total=499, limit=50):
    # set urls to scrape through
    start_urls = [f'https://mapi.yummly.com/mapi/v19/content/feed?start={x}&limit=50&allowedContent=single_recipe' for x
                  in range(0, total, limit)]

    # get each page in the feed, get ids, and call scrape recipe for each recipe
    recipe_data = list()
    for url in start_urls:
        dct = requests.get(url).json()
        ids = [x['tracking-id'].split(',')[0].strip('recipe:') for x in dct['feed']]
        for id in ids:
            dct = requests.get(f'https://mapi.yummly.com/mapi/v19/content/feed?id={id}').json()
            if dct and dct['feed']:
                recipe_data.append(scrape_recipe(dct))
    return recipe_data


def main():
    dct = scrape_feed()
    with open("data/recipe_data.json", "w") as final:
        json.dump(dct, final)


main()
