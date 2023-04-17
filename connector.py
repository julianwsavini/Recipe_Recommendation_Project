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
    df[nums] = df[nums].fillna(0)
    df = df.fillna('N/A')

    # run famd and output dataframe
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


def generate_edges(df):
    """Compare every recipe to every other recipe in dataframe"""
    edge_df = pd.concat([x for x in df.apply(lambda row: compare_recipe(row, df), axis=1)])
    edge_df.to_csv('data/edges.csv', index=False)
    return edge_df


def load_mongo(db, data_url):
    """Load data from file into mongo database"""

    # flush database
    dbname = get_database()
    collection = dbname[db]
    collection.delete_many({})

    # load in data
    with open(data_url) as data_file:
        data = json.load(data_file)
    collection.insert_many([item for item in data])

    return collection


def load_neo4j(collection, edge_url, uri='bolt://localhost:7687', user='neo4j', pw='epd9htf5kvd_hwt.PZR'):
    """Load data from Mongo into neo4j"""
    driver = GraphDatabase.driver(uri, auth=(user, pw))
    data = collection.find()

    with driver.session() as session:
        # flush database
        tx = session.begin_transaction()
        query = 'MATCH (n) DETACH DELETE n'
        tx.run(query)

        # insert nodes from Mongo
        for record in data:
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
            tx.run(query, **fields)

        # insert edges from csv
        query = f"LOAD CSV WITH HEADERS FROM 'file:///{edge_url}' AS row " + '''
        MERGE (source {recipeId: row.id_1})
        MERGE (target {recipeId: row.id_2})
        MERGE (source)-[:SIMILAR {similarity: row.similarity}]->(target)
        '''
        tx.run(query)
        tx.commit()


if __name__ == '__main__':
    # import data into mongo
    collection = load_mongo('recipes', 'data/recipe_data.json')

    # import data into neo4j need full url because of neo4j security settings
    load_neo4j(collection, '/Users/max/Northeastern/spring_2023/DS_4300/recipes/data/edges.csv')
