from pymongo import MongoClient
import json
from neo4j import GraphDatabase

def get_database():
    CONNECTION_STRING = 'mongodb://localhost:27017/'

    client = MongoClient(CONNECTION_STRING)

    return client['4300project']

if __name__ == '__main__':
    dbname = get_database()
    collection = dbname['recipes']

    with open('/Users/avaduggan/Desktop/rachlin/ds4300project/ds4300_recipes/data/recipe_data.json') as data_file:
        data = json.load(data_file)

    collection.insert_many([item for item in data])

    uri = 'bolt://localhost:7687'
    user ='neo4j'
    password = 'Cheetah871'
    driver = GraphDatabase.driver(uri, auth=(user,password))

    #query data from Mongodb
    data1 = collection.find()


    with driver.session() as session:
        tx = session.begin_transaction()
        for record in data1:
            fields = {'field1': record['name'], 'field2': record['url'], 'field3': record['recipeType'], 'field4':
                      record['keywords'], 'field5': record['description'], 'field6': record['steps']} #'field7': [x['name'] for x in record['ingredients']]}
            query = 'CREATE (recipe:recipes {name: $field1, url: $field2, recipeType: $field3, keywords: \
            $field4, description: $field5, steps: $field6})' # ingredients: $field7})'

            tx.run(query, **fields)
            tx.run('UNWIND $value as ingredients  \
                    MERGE (recipe:recipes {ing_name:ingredients.name})', value = record['ingredients'])
            #issue with ingredients and tags, reviews, nutrition
        tx.commit()
        #for record in data1:


 #ingredients[$name] is not NULL

