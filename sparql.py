# import credentials
import pandas as pd
from config import *
from rdflib.plugins.stores import sparqlstore
from rdflib import Namespace


class FoodDatabase(object):

    def __init__(self, configuration):
        super(FoodDatabase, self).__init__()
        # Setup the SPARQL endpoint
        self.store = sparqlstore.SPARQLUpdateStore()
        self.store.open((configuration['endpoint'], configuration['endpoint']))
        self.store.setCredentials(configuration['username'], configuration['password'])
        # Setup prefixed for common namespaces
        self.store.bind('ont', Namespace('http://www.food-groups.com/ontology#'))
        self.store.bind('dc', Namespace('http://purl.org/dc/elements/1.1/'))

    def user_ingredient_matrix(self):
        query = """
                SELECT (count(?recipe) as ?count) ?uploader ?ingredient WHERE
                {
                 ?recipe a ont:Recipe;
                         dc:creator ?uploader;
                         ont:requiresQuantityOfIngredient/ont:hasIngredient ?ingredient.
                } GROUP BY ?uploader ?ingredient
                """
        uploader_dct = {}  # start with empty dct
        for result in self.store.query(query):
            uploader = result.uploader.toPython()
            if uploader not in uploader_dct:
                uploader_dct[uploader] = {}
            ingredient_dct = uploader_dct[uploader]
            ingredient = result.ingredient.toPython()
            ingredient_dct[ingredient] = result[0].toPython()
        return pd.DataFrame.from_dict(uploader_dct).fillna(0)

    def recipe_ingredient_matrix(self, limit=20):
        query = """
                SELECT ?recipe ?ingredient WHERE
                {
                    {
                      SELECT ?recipe WHERE
                      {
                        ?recipe a ont:Recipe.
                      } ORDER BY RAND() LIMIT %d
                    }
                    ?recipe ont:requiresQuantityOfIngredient/ont:hasIngredient ?ingredient.
                }""" % limit
        recipe_dct = {}
        for result in self.store.query(query):
            recipe = result.recipe.toPython()
            if recipe not in recipe_dct:
                recipe_dct[recipe] = {}
            ingredient_dct = recipe_dct[recipe]
            ingredient = result.ingredient.toPython()
            ingredient_dct[ingredient] = True  # Recipe uses this ingredient
        return pd.DataFrame.from_dict(recipe_dct).fillna(False)

    def user_recipes(self, user):
        query = """
                SELECT ?recipe WHERE
                {
                    ?recipe dc:creator \"%s\";
                            a ont:Recipe.
                }
                """ % user
        results = self.store.query(query)
        results = map(lambda r: r.recipe.toPython(), results)
        return list(results)  # Explicit list conversion

    def recipe_name(self, recipe):
        query = """
                SELECT ?recipeName WHERE
                {
                    <%s> ont:resultsIn/ont:hasFoodName ?recipeName.
                }
                """ % recipe
        results = self.store.query(query)
        results = map(lambda r: r.recipeName.toPython(), results)
        return list(results)[0]  # Assumption: Recipe has only 1 name

    def recipe_uploader(self, recipe):
        query = """
                SELECT ?uploader WHERE
                {
                    <%s> dc:creator ?uploader.
                }
                """ % recipe
        results = self.store.query(query)
        results = map(lambda r: r.uploader.toPython(), results)
        return list(results)[0]  # Assumption: Recipe has only 1 uploader


# if __name__ == '__main__':
#     stardog = {
#         'endpoint': STARDOG_ENDPOINT,
#         'username': STARDOG_USERNAME,
#         'password': STARDOG_PASSWORD
#         }
