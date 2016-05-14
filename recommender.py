from scipy.spatial.distance import euclidean
from scipy.stats.stats import pearsonr
from sparql import FoodDatabase
from config import *
import numpy as np


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

    # Get random recipes. Each recipes gets a score S_i = sum(x_i * w_i)
    # where x_i is the i'th ingredient of the recipe
    # w_i is the frequency of the ith ingredient in the user-ingredient matrix
    # The user gets the recipe with the highest score, since this recipe
    # has the most ingredients already used by the user.
    # Maybe include a check so that a user does not get recommended
    # it's own recipe?
    def best_matches(self, user, avoid_self=True):
        recipe_ingredient = self.get_recipe_ingredient_matrix(3)
        user_ingredient = self.get_user_ingredient_matrix()
        recipes = recipe_ingredient.columns.values
        num_recipes = len(recipes)
        scores = np.zeros(num_recipes)
        for i in range(num_recipes):
            ingredient_row = recipe_ingredient.iloc[:, i]
            for ingredient, used in ingredient_row.iteritems():
                scores[i] += used * user_ingredient.loc[ingredient, user]
        recommend = recipes[np.argmax(scores)]
        while avoid_self:
            uploader = self.get_recipe_uploader(recommend)
            if uploader == user:
                recipes = np.delete(recipes, np.argmax(scores))
                scores = np.delete(scores, np.argmax(scores))
                recommend = recipes[np.argmax(scores)]
            else:
                break
        recipe = self.get_recipe_name(recommend)
        print('We would recommend recipe', recipe)
        return

    # Returns the Euclidian distance between two users
    def euclidian(self, user1, user2):
        return euclidean(self.user_matrix.loc[:, user1],
                         self.user_matrix.loc[:, user2])

    # Returns the Pearson correlation coefficient between two users
    def pearson(self, user1, user2):
        return pearsonr(self.user_matrix.loc[:, user1],
                        self.user_matrix.loc[:, user2])[0]

    # Returns the most similar user for the given user from the matrix
    # Number of the results and similarity function are optional parameters
    def similar_users(self, user, n=5, similarity='pearson'):
        if similarity == 'pearson':
            scores = [(self.pearson(user, other), other) for other in self.user_matrix.columns.values if other != user]
        elif similarity == 'euclidean':
            scores = [(self.euclidean(user, other), other) for other in self.user_matrix.columns.values if other != user]
        scores.sort()
        scores.reverse()
        return scores[:n]

    
    # [2] what you are currently doing: correlations between users
    #     (pearson/euclidiean/...), then get a random recipe from
    #      the highest scoring user (?)
    # maybe experiment with both approaches,
    # all the methods needed for these two approaches should be available now

if __name__ == '__main__':
    stardog = {
        'endpoint': STARDOG_ENDPOINT,
        'username': STARDOG_USERNAME,
        'password': STARDOG_PASSWORD
        }
    foodDB = FoodDatabase(stardog)
    recsys = Recommender(foodDB)
    recsys.best_matches('jens.nevens@vub.ac.be')
