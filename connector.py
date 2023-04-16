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

    # expand ingredients column
    df['ingredients'] = df.apply(lambda row: [x['name'] for x in row['ingredients']], axis=1)
    df = expand_column(df, 'ingredients')

    # expand nutrition column
    df['nutrition'] = df.apply(lambda row: [f"{x['value']} {x['name']}" for x in row['nutrition']], axis=1)
    df = expand_column(df, 'nutrition')

    return df


def run_famd(collection):
    """Run dimensionality reduction algorithm on collection"""
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


def compare_recipe(row, df):
    """Compare one recipe to all other recipes"""
    new_df = pd.DataFrame(columns=['id_1', 'id_2', 'similarity'])
    df = df.loc[df['id'] != row['id']]
    new_df['id_2'] = df['id']
    new_df['similarity'] = df.apply(lambda recipe: euclidean([row[0], row[1]], [recipe[0], recipe[1]]), axis=1)
    new_df['id_1'] = row['id']
    return new_df.sort_values(by='similarity').iloc[:20]


def compare_all_recipes(df):
    """Compare every recipe to every other recipe in dataframe"""
    return pd.concat([x for x in df.apply(lambda row: compare_recipe(row, df), axis=1)])


if __name__ == '__main__':
    dbname = get_database()
    collection = dbname['recipes']
    collection.delete_many({})

    with open('data/recipe_data.json') as data_file:
        data = json.load(data_file)

    collection.insert_many([item for item in data])

    # generate similarity between recipes dataset
    df = run_famd(collection)
    edge_df = compare_all_recipes(df)
    edge_df.to_csv('data/edges.csv', index=False)

    # connect to neo4j
    uri = 'bolt://localhost:7687'
    user = 'neo4j'
    password = 'epd9htf5kvd_hwt.PZR'  # 'Cheetah871'
    driver = GraphDatabase.driver(uri, auth=(user, password))

    # get data from Mongodb
    data1 = collection.find()

    with driver.session() as session:
        # flush database
        tx = session.begin_transaction()
        query = 'MATCH (n) DETACH DELETE n'
        # tx.commit()

        # insert nodes from Mongo
        # tx = session.begin_transaction()
        for record in data1:
            ingredients = []
            for ingredient in record['ingredients']:
                ingredients.append(ingredient['name'])
            fields = {'field1': record['name'], 'field2': record['url'], 'field3': record['recipeType'],
                      'field4': record['keywords'], 'field5': record['description'],
                      'field6': record['steps'], 'field7': record['dish'], 'field8': record['course'],
                      'field9': record['technique'], 'field10': record['cuisine'],
                      'field11': record['avgRating'], 'field12': record['numReviews'],
                      'field13': list(filter(None, ingredients)),
                      'field14': record['id']}
            query = 'CREATE (recipe:recipes {name: $field1, url: $field2, recipeType: $field3, keywords: \
            $field4, description: $field5, steps: $field6, dish: $field7, course: $field8, \
            technique: $field9, cuisine: $field10, avgRating: $field11, numReviews: $field12, \
            ingredients: $field13, recipeId: $field14})'
            print(record)

            tx.run(query, **fields)
        tx.commit()

        # insert edges from csv
        # tx = session.begin_transaction()
        # query = '''
        # LOAD CSV WITH HEADERS FROM 'file:///Users/max/Northeastern/spring_2023/DS_4300/recipes/data/edges.csv' AS row
        # MATCH (source {recipe_id: row.id_1})
        # MATCH (target {recipe_id: row.id_2})
        # CREATE (source)-[:SIMILAR {similarity: row.similarity}]->(target)
        # '''
        # tx.run(query)
        # tx.commit()
