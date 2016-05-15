from wikitaaable_queries import *
from config import *

from rdflib.plugins.stores import sparqlstore
from rdflib import Namespace, Graph, URIRef, Literal
from rdflib.namespace import XSD, RDF, DC

from urllib.parse import quote
import sys

wikitaaable_config = {
    'endpoint': STARDOG_WIKI_ENDPOINT,
    'username': STARDOG_USERNAME,
    'password': STARDOG_PASSWORD
}

group1_config = {
    'endpoint': STARDOG_GROUP1_ENDPOINT,
    'username': STARDOG_USERNAME,
    'password': STARDOG_PASSWORD
}

wiki_store = sparqlstore.SPARQLUpdateStore()
wiki_store.open((wikitaaable_config['endpoint'], wikitaaable_config['endpoint']))
wiki_store.setCredentials(wikitaaable_config['username'], wikitaaable_config['password'])

group1_store = sparqlstore.SPARQLUpdateStore()
group1_store.open((group1_config['endpoint'], group1_config['endpoint']))
group1_store.setCredentials(group1_config['username'], group1_config['password'])
ONT = Namespace('http://www.food-groups.com/ontology#')
# group1_store.bind('ont', Namespace('http://www.food-groups.com/ontology#'))
# group1_store.bind('dc', Namespace('http://purl.org/dc/elements/1.1/'))
# group1_store.bind('xsd', XSD)


default_graph = URIRef('http://www.food-groups.com/ontology/wiki')
ng = Graph(group1_store, identifier=default_graph)

def get_wiki_recipe(recipe_id):
    recipe_name = next(wiki_store.query(wiki_recipe % recipe_id).__iter__()).label.toPython()
    steps = []
    for result in wiki_store.query(wiki_steps % recipe_id):
        steps.append({'number': int(result.stepnb.toPython()), 'description': result.stepDescr.toPython()})
    ingredients = []
    for result in wiki_store.query(wiki_ingredients % recipe_id):
        ingredients.append({
                           'name': result.ingredientName.toPython(),
                           'quantity': result.ingredientQuantity.toPython() if result.ingredientQuantity else 0,
                           'unit': result.ingredientUnit.toPython() if result.ingredientUnit else 'kilogram'
                           })
    return recipe_name, steps, ingredients

unit_mapping = {
    'c': 'cup',
    'tblsp': 'spoon',
    'tsp': 'teaspoon',
    'pk': 'peck',
    'pt': 'pint',
    'qt': 'quart'
}

def insert_recipe_data(food_name, recipe_id, creator, steps, ingredients):
    food_uri = URIRef('http://data.group1.com/ontology/Food/%s' % quote(food_name))
    recipe_uri = URIRef('http://data.group1.com/ontology/Recipe/%i' % recipe_id)
    ng.add((food_uri, RDF.type, ONT.Food))
    ng.add((food_uri, ONT.hasFoodName, Literal(food_name, datatype=XSD.string)))
    ng.add((recipe_uri, RDF.type, ONT.Recipe))
    ng.add((recipe_uri, DC.creator, Literal(creator, datatype=XSD.string)))
    ng.add((recipe_uri, ONT.resultsIn, food_uri))
    for step in steps:
        recipe_step_uri = URIRef('http://data.group1.com/ontology/RecipeStep/%i-%i' % (recipe_id, step['number']))
        ng.add((recipe_step_uri, RDF.type, ONT.RecipeStep))
        ng.add((recipe_step_uri, ONT.hasStepDescription, Literal(step['description'], datatype=XSD.string)))
        ng.add((recipe_step_uri, ONT.hasOrderingNumber, Literal(step['number'], datatype=XSD.integer)))
        ng.add((recipe_uri, ONT.hasStep, recipe_step_uri))
    for ingredient in ingredients:
        ingredient_uri = URIRef('http://data.group1.com/ontology/Ingredient/%s' % quote(ingredient['name']))
        ng.add((ingredient_uri, RDF.type, ONT.Ingredient))
        ng.add((ingredient_uri, ONT.hasIngredientName, Literal(ingredient['name'], datatype=XSD.string)))
        recipe_ingredient_uri = URIRef('http://data.group1.com/ontology/IngredientQuantity/%i-%s' % (recipe_id, quote(ingredient['name'])))
        ng.add((recipe_ingredient_uri, RDF.type, ONT.IngredientQuantity))
        unit = unit_mapping[ingredient['unit']] if ingredient['unit'] in unit_mapping else unit
        ng.add((recipe_ingredient_uri, ONT.hasIngredientQuantity, Literal(ingredient['quantity'], datatype=XSD.float)))
        ng.add((recipe_ingredient_uri, ONT.hasQuantityUnit, Literal(unit, datatype=XSD.string)))
        ng.add((recipe_uri, ONT.requiresQuantityOfIngredient, recipe_ingredient_uri))
        ng.add((recipe_ingredient_uri, ONT.hasIngredient, ingredient_uri))
    return

wiki_namespace = Namespace('http://wikitaaable.loria.fr/index.php/Special:URIResolver/')
wiki_store.bind('wiki', wiki_namespace)

if __name__ == '__main__':
    if len(sys.argv) < 4:
        print('Please provide parameters: [1] recipe name on wikitaaable, [2] unique recipe id, [3] creator email address')
    else:
        name, steps, ingredients = get_wiki_recipe(sys.argv[1])
        insert_recipe_data(name, int(sys.argv[2]), sys.argv[3], steps, ingredients)
