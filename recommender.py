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
    # When avoid_self is set to True, no recipes uploaded by the given user
    # will be recommended to that same user.
    def best_matches(self, user, avoid_self=True):
        recipe_ingredient = self.get_recipe_ingredient_matrix(3)
        user_ingredient = self.get_user_ingredient_matrix()
        recipes = recipe_ingredient.columns.values
        num_recipes = len(recipes)
        scores = np.zeros(num_recipes)
        for i in range(num_recipes):
            ingredient_row = recipe_ingredient.iloc[:, i]
            # Need another for-loop since user_ingredient matrix contains
            # all ingredients, while recipe_ingredient matrix contains
            # only union of ingredients in these recipes. Otherwise, this
            # would simply be:
            # scores[i] = np.dot(ingredient_row, user_ingredient.loc[:,user])
            for ingredient, used in ingredient_row.iteritems():
                scores[i] += used * user_ingredient.loc[ingredient, user]
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
        recipe = self.get_recipe_name(recommend)
        print('We would recommend recipe', recipe)
        return

    # Returns the Euclidian distance between two users
    def euclidian(self, matrix, user1, user2):
        return euclidean(matrix.loc[:, user1], matrix.loc[:, user2])

    # Returns the Pearson correlation coefficient between two users
    def pearson(self, matrix, user1, user2):
        return pearsonr(matrix.loc[:, user1], matrix.loc[:, user2])[0]

    # Get (ingredient) recommendations for a user by using a weighted average
    # of every other user's usage frequency.
    # Next step is finding recipes with the most highly recommended
    # ingredients. This can again be done using a weighted average.
    def best_ingredients(self, user, similarity='pearson'):
        user_ingredient = self.get_user_ingredient_matrix()
        totals = {}
        sim_sums = {}
        # It calculates how similar the persons are to the specified user
        # and afterwards looks at each ingredient used by those other users.
        # As result you have a classified ingredient list and
        # an estimated rating that 'user' would give for each ingredient in it.
        for person in user_ingredient.columns.values:
            # Don't compare me to myself
            if user == person:
                continue
            if similarity == 'pearson':
                sim = self.pearson(user_ingredient, user, person)
            elif similarity == 'euclidian':
                sim = self.euclidian(user_ingredient, user, person)
            # Ignore scores of zero or lower
            # if sim <= 0:
            #     continue
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
        rankings = [(total/sim_sums[item], item)
                    for item, total in totals.items()]
        # Return the sorted list
        rankings.sort()
        rankings.reverse()
        return rankings

if __name__ == '__main__':
    stardog = {
        'endpoint': STARDOG_GROUP1_ENDPOINT,
        'username': STARDOG_USERNAME,
        'password': STARDOG_PASSWORD
    }
    foodDB = FoodDatabase(stardog)
    recsys = Recommender(foodDB)
    recsys.best_matches('arno.moonens@vub.ac.be')
    # print(recsys.best_ingredients('jens.nevens@vub.ac.be'))
