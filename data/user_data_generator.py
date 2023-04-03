import pandas as pd
import random as rnd


def get_recipes(df, names, recipes_per=10):
    # common = ['cuisine', 'dish', 'technique', 'keywords', 'ingredients']
    user_df = pd.DataFrame(columns=['user', 'recipe', 'rating'])

    for name in names:
        while len(user_df.loc[user_df.user == name]) < recipes_per:
            recipe = df.sample()
            row = {'user': name, 'recipe': recipe.name.values[0],
                   'rating': rnd.choices([1, 2, 3, 4, 5], weights=[0.1, 0.2, 0.3, 0.2, 0.1], k=1)[0]}
            if len(user_df.loc[(user_df.user == name) & (user_df.recipe == row['recipe'])]) == 0:
                user_df.loc[len(user_df)] = row

    return user_df


def main():
    df = pd.read_json('recipe_data.json')
    names = ['John', 'Anjali', 'Ava', 'Julian', 'Max', 'Catherine', 'Duncan', 'Joel', 'Ellie']
    user_df = get_recipes(df, names)
    print(user_df)
    user_df.to_csv('mock_users.csv', index=False)
    

main()
