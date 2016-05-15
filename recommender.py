from scipy.spatial.distance import euclidean
from scipy.stats.stats import pearsonr
from sparql import FoodDatabase
from config import *
import numpy as np
import sys


class Recommender(object):

    def __init__(self, foodDB):
        super(Recommender, self).__init__()
        self.foodDB = foodDB

    # User x Ingredient matrix where each entry
    # specifies how often the user used the ingredient
    def get_user_ingredient_matrix(self):
        return self.foodDB.user_ingredient_matrix()

    # Recipe x Ingredient matrix where each entry
    # specifies whether the ingredient is in the recipe
    def get_recipe_ingredient_matrix(self, limit=20):
        return self.foodDB.recipe_ingredient_matrix(limit)

    # Returns all recipes of a user
    def get_user_recipes(self, user):
        return self.foodDB.user_recipes(user)

    # Returns the name of a recipe
    def get_recipe_name(self, recipe):
        return self.foodDB.recipe_name(recipe)

    # Returns the uploader of a recipe
    def get_recipe_uploader(self, recipe):
        return self.foodDB.recipe_uploader(recipe)

    # Returns the Euclidian distance between two users
    def euclidian(self, matrix, user1, user2):
        return euclidean(matrix.loc[:, user1], matrix.loc[:, user2])

    # Returns the Pearson correlation coefficient between two users
    def pearson(self, matrix, user1, user2):
        return pearsonr(matrix.loc[:, user1], matrix.loc[:, user2])[0]

    # This method calculates preferences for ingredients the given user
    # has not used before, based on the similarites to other users and
    # their ingredients.
    def collaborative_filtering(self, user, n=10, similarity='pearson'):
        user_ingredient = self.get_user_ingredient_matrix()
        totals = {}
        sim_sums = {}
        for person in user_ingredient.columns.values:
            # Don't compare me to myself
            if user == person:
                continue
            if similarity == 'pearson':
                sim = self.pearson(user_ingredient, user, person)
            elif similarity == 'euclidian':
                sim = self.euclidian(user_ingredient, user, person)
            # Ignore similarites of zero or lower
            if sim <= 0:
                continue
            for ingr, val in user_ingredient.loc[:, person].iteritems():
                if user_ingredient.loc[ingr, user] == 0:
                    if ingr in totals:
                        totals[ingr] += user_ingredient.loc[ingr, person] * sim
                    else:
                        totals[ingr] = user_ingredient.loc[ingr, person] * sim
                    if ingr in sim_sums:
                        sim_sums[ingr] += sim
                    else:
                        sim_sums[ingr] = sim
        # Create the normalized list
        rankings = [(total/sim_sums[item], item) for item, total in totals.items()]
        rankings.sort()
        rankings.reverse()
        return rankings[:n]

    # These ingredient preferences computed above will be used here to
    # find a matching recipe. First, #'limit' random recipes will be
    # queried from the triplestore. Then, each recipe is assigned a score
    # using the weighted average of the ingredients. The weights are
    # the preferences.
    def find_matching_recipe(self, user, ingredients, avoid_self=True):
        recipe_ingredient = self.get_recipe_ingredient_matrix(limit=10)
        recipes = recipe_ingredient.columns.values
        num_recipes = len(recipes)
        scores = np.zeros(num_recipes)
        for i in range(num_recipes):
            ingredient_row = recipe_ingredient.iloc[:, i]
            for preference, ingredient in ingredients:
                if ingredient in ingredient_row:
                    scores[i] += preference * ingredient_row.loc[ingredient]
            scores[i] = scores[i] / np.sum(ingredient_row)
        recommend = recipes[np.argmax(scores)]
        while avoid_self:
            uploader = self.get_recipe_uploader(recommend)
            if uploader == user:
                recipes = np.delete(recipes, np.argmax(scores))
                scores = np.delete(scores, np.argmax(scores))
                recommend = recipes[np.argmax(scores)]
            else:
                break
        recipe_name = self.get_recipe_name(recommend)
        return recipe_name

    def recommend_recipe(self, user):
        ingredients = self.collaborative_filtering(user)
        recipe = self.find_matching_recipe(user, ingredients)
        print('Hello,', user)
        print('We would recommend our recipe for', recipe, 'for you.')
        print('Enjoy your meal!')
        return

if __name__ == '__main__':
    if len(sys.argv) < 2:
        print("""
              Please provide the following arguments:
              [1] your email address on MyFoodGuru
              """)
    else:
        stardog = {
            'endpoint': STARDOG_GROUP1_ENDPOINT,
            'username': STARDOG_USERNAME,
            'password': STARDOG_PASSWORD
        }
        foodDB = FoodDatabase(stardog)
        recsys = Recommender(foodDB)
        recsys.recommend_recipe(sys.argv[1])
