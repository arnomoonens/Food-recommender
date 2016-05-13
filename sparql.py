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
					         ont:requiresQuantityOfIngredient ?ingredientQuantity.
					 ?ingredientQuantity ont:hasIngredient ?ingredient.
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

if __name__ == '__main__':
	sparqldb = FoodDatabase(my_config)
	results = sparqldb.load_data()
	print(str(results))