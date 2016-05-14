# import credentials
import pandas as pd
from config import *
from rdflib.plugins.stores import sparqlstore
from rdflib import Namespace

my_config = {
	'endpoint': STARDOG_ENDPOINT,	
	'username': STARDOG_USERNAME,
	'password': STARDOG_PASSWORD
}


class FoodDatabase(object):

	def __init__(self,configuration):
		super(FoodDatabase, self).__init__()
		#setup the SPARQL endpoint
		self.store = sparqlstore.SPARQLUpdateStore()
		self.store.open((configuration['endpoint'],configuration['endpoint']))
		self.store.setCredentials(configuration['username'],configuration['password'])
		#setup prefixed for common namespaces
		self.store.bind('ont',Namespace('http://www.food-groups.com/ontology#'))
		self.store.bind('dc',Namespace('http://purl.org/dc/elements/1.1/'))

	def load_data(self):
		query = """SELECT (count(?recipe) as ?count) ?uploader ?ingredient WHERE 
				{
				 ?recipe a ont:Recipe;
				         dc:creator ?uploader;
				         ont:requiresQuantityOfIngredient/ont:hasIngredient ?ingredient.
				} GROUP BY ?uploader ?ingredient""" 
		uploader_dct = {} #start with empty dct
		for result in self.store.query(query):
			uploader = result.uploader.toPython()
			if uploader not in uploader_dct:
				uploader_dct[uploader] = {}
			ingredient_dct = uploader_dct[uploader]
			ingredient = result.ingredient.toPython()
			ingredient_dct[ingredient] = result[0].toPython()
		return pd.DataFrame.from_dict(uploader_dct).fillna(0)

	def load_recipes(self,limit=20):
		query = """SELECT ?recipe ?ingredient WHERE 
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
			ingredient_dct[ingredient] = True #recipe uses this ingredient
		return pd.DataFrame.from_dict(recipe_dct).fillna(False)

	def load_user_recipes(self,user):
		query = """SELECT ?recipe WHERE 
					{
					    ?recipe dc:creator \"%s\";
					    		a ont:Recipe.
					}""" % user
		results = self.store.query(query)
		results = map(lambda r: r.recipe.toPython(),results)
		return list(results) #explicit list conversion

if __name__ == '__main__':
	#example usage
	sparqldb = FoodDatabase(my_config)
	#results = sparqlstore.load_data()								# load all user-recipe data for the recommender matrix
	#results = sparqldb.load_recipes(3)  							# load a maximum of 3 random recipes and their ingredients
	results = sparqldb.load_user_recipes("noah.van.es@vub.ac.be") 	# load all recipes of a user
	print(results)