from pymongo import MongoClient
import json
import pandas as pd
import numpy as np
from neo4j import GraphDatabase
from prince import FAMD
import warnings

warnings.simplefilter(action='ignore', category=FutureWarning)


def get_database():
    CONNECTION_STRING = 'mongodb://localhost:27017/'

    client = MongoClient(CONNECTION_STRING)
    print(client.server_info())

    return client['4300project']


def expand_column(df, col):
    """Expand a simple column of lists into multiple discrete columns"""
    max_len = max(map(len, df[col].values))
    cols = [f'{col}_{x}' for x in range(max_len)]
    df[cols] = df[col].apply(lambda x: pd.Series(x))
    df = df.drop(columns=col)
    return df


def clean_columns(collection):
    # create dataframe, drop unnecessary columns
    df = pd.DataFrame(list(collection.find()))
    pca_drops = ['url', 'recipeType', 'steps']
    df = df.drop(columns=pca_drops)

    # expand columns that are simple lists into individual columns
    list_cols = ['keywords', 'dish', 'course', 'technique', 'cuisine']
    for col in list_cols:
        df = expand_column(df, col)

    # complex cols
    complex = ['ingredients', 'reviews', 'nutrition']

    # expand ingredients column
    df['ingredients'] = df.apply(lambda row: [x['name'] for x in row['ingredients']], axis=1)
    df = expand_column(df, 'ingredients')

    # expand nutrition column
    df['nutrition'] = df.apply(lambda row: [f"{x['value']} {x['name']}" for x in row['nutrition']], axis=1)
    df = expand_column(df, 'nutrition')

    # expand ratings column
    df['avgRating'] = df.apply(lambda row: row['avgRating'], axis=1)
    df['numReviews'] = df.apply(lambda row: row['numReviews'], axis=1)
    df = df.drop(columns=['reviews'])

    return df


def run_famd(collection):
    org_df = pd.DataFrame(list(collection.find()))
    df = clean_columns(collection)

    # drop empties
    nums = df.select_dtypes(include=[np.number]).columns
    strs = df.select_dtypes(exclude=[np.number]).columns
    df[nums] = df[nums].fillna(0)
    df[strs] = df[strs].fillna('N/A')

    famd = FAMD().fit(df)
    fit_df = famd.transform(df)

    df = pd.concat([org_df, fit_df], axis=1).reset_index(drop=True)

    return df


def euclidean(x, y):
    return (((y[1] - x[1]) ** 2) + ((y[0] - x[0]) ** 2)) ** 0.5


def compare_recipe(row, df, id):
    return df.loc[df['_id'] != id].apply(lambda recipe: euclidean([row[0], row[1]], [recipe[0], recipe[1]]), axis=1)


def compare_all_recipes(df):
    return df.apply(lambda row: compare_recipe(row, df, row['_id']), axis=1)


if __name__ == '__main__':
    dbname = get_database()
    collection = dbname['recipes']
<<<<<<< HEAD

    #df = run_pca(collection)
=======
    collection.delete_many({})
>>>>>>> cb170ced9f790cd73f407ac7593865b88528510a

    with open('data/recipe_data.json') as data_file:
        data = json.load(data_file)

    collection.insert_many([item for item in data])
    df = run_pca(collection)

    # generate similarity between recipes dataset
    df = run_famd(collection)
    edge_df = pd.concat([x for x in compare_all_recipes(df)])

    uri = 'bolt://localhost:7687'
    user = 'neo4j'
    password = 'Cheetah871' #epd9htf5kvd_hwt.PZR'
    driver = GraphDatabase.driver(uri, auth=(user, password))

    # query data from Mongodb
    data1 = collection.find()
    with driver.session() as session:
        tx = session.begin_transaction()
        for record in data1:
            ingredients = []
            for ingredient in record['ingredients']:
                ingredients.append(ingredient['name'])
            fields = {'field1': record['name'], 'field2': record['url'], 'field3': record['recipeType'], 'field4':
                record['keywords'], 'field5': record['description'],
                      'field6': record['steps'], 'field7': list(filter(None,ingredients))}  # 'field7': [x['name'] for x in record['ingredients']]}
            query = 'CREATE (recipe:recipes {name: $field1, url: $field2, recipeType: $field3, keywords: \
            $field4, description: $field5, steps: $field6, ingredients: $field7})'

            query2 = 'MERGE (recipe: recipes {ingredients: $list})'

            tx.run(query, **fields)
            #tx.run('MERGE (recipe: recipes {ingredients: $list1})', list1=list(filter(None,ingredients)))
            # issue with ingredients and tags, reviews, nutrition
        tx.commit()
        # for record in data1:

# ingredients[$name] is not NULL
