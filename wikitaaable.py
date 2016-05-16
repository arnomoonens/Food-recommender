from wikitaaable_queries import *
from config import *

from rdflib.plugins.stores import sparqlstore
from rdflib import Namespace, URIRef, Literal
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
wiki_namespace = Namespace('http://wikitaaable.loria.fr/index.php/Special:URIResolver/')
wiki_store.bind('wiki', wiki_namespace)

group1_store = sparqlstore.SPARQLUpdateStore()
group1_store.open((group1_config['endpoint'], group1_config['endpoint']))
group1_store.setCredentials(group1_config['username'], group1_config['password'])
ONT = Namespace('http://www.food-groups.com/ontology#')
# group1_store.bind('ont', Namespace('http://www.food-groups.com/ontology#'))
# group1_store.bind('dc', Namespace('http://purl.org/dc/elements/1.1/'))
# group1_store.bind('xsd', XSD)


def get_wiki_recipe(recipe_id):
    recipe_name = next(wiki_store.query(wiki_recipe % recipe_id).__iter__()).label.toPython()
    steps = []
    for result in wiki_store.query(wiki_steps % recipe_id):
        steps.append({'number': int(result.stepnb.toPython()), 'description': result.stepDescr.toPython()})
    ingredients = []
    for result in wiki_store.query(wiki_ingredients % recipe_id):
        ingredients.append({
                           'name': result.ingredientName.toPython(),
                           'quantity': result.ingredientQuantity.toPython() if result.ingredientQuantity else None,
                           'unit': result.ingredientUnit.toPython() if result.ingredientUnit else None
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

last_recipe_id_query = """
PREFIX ont:<http://www.food-groups.com/ontology#>
select (max(xsd:integer(STRAFTER(str(?entity), "http://data.group1.com/ontology/Recipe/"))) as ?id)
where {
    ?entity a ont:Recipe .
}
"""

def insert_recipe_data(food_name, creator, steps, ingredients):
    recipe_id = next(group1_store.query(last_recipe_id_query).__iter__()).id.toPython() + 1
    food_uri = URIRef('http://data.group1.com/ontology/Food/%s' % quote(food_name))
    recipe_uri = URIRef('http://data.group1.com/ontology/Recipe/%i' % recipe_id)
    group1_store.add((food_uri, RDF.type, ONT.Food))
    group1_store.add((food_uri, ONT.hasFoodName, Literal(food_name, datatype=XSD.string)))
    group1_store.add((recipe_uri, RDF.type, ONT.Recipe))
    group1_store.add((recipe_uri, DC.creator, Literal(creator, datatype=XSD.string)))
    group1_store.add((recipe_uri, ONT.resultsIn, food_uri))
    for step in steps:
        recipe_step_uri = URIRef('http://data.group1.com/ontology/RecipeStep/%i-%i' % (recipe_id, step['number']))
        group1_store.add((recipe_step_uri, RDF.type, ONT.RecipeStep))
        group1_store.add((recipe_step_uri, ONT.hasStepDescription, Literal(step['description'], datatype=XSD.string)))
        group1_store.add((recipe_step_uri, ONT.hasOrderingNumber, Literal(step['number'], datatype=XSD.integer)))
        group1_store.add((recipe_uri, ONT.hasStep, recipe_step_uri))
    for ingredient in ingredients:
        ingredient_uri = URIRef('http://data.group1.com/ontology/Ingredient/%s' % quote(ingredient['name'].lower()))
        group1_store.add((ingredient_uri, RDF.type, ONT.Ingredient))
        group1_store.add((ingredient_uri, ONT.hasIngredientName, Literal(ingredient['name'].lower(), datatype=XSD.string)))
        recipe_ingredient_uri = URIRef('http://data.group1.com/ontology/IngredientQuantity/%i-%s' % (recipe_id, quote(ingredient['name'].lower())))
        group1_store.add((recipe_ingredient_uri, RDF.type, ONT.IngredientQuantity))
        if ingredient['unit']:
            unit = unit_mapping[ingredient['unit']] if ingredient['unit'] in unit_mapping else ingredient['unit']
            group1_store.add((recipe_ingredient_uri, ONT.hasQuantityUnit, Literal(unit, datatype=XSD.string)))
        if ingredient['quantity']:
            group1_store.add((recipe_ingredient_uri, ONT.hasIngredientQuantity, Literal(ingredient['quantity'], datatype=XSD.float)))
        group1_store.add((recipe_uri, ONT.requiresQuantityOfIngredient, recipe_ingredient_uri))
        group1_store.add((recipe_ingredient_uri, ONT.hasIngredient, ingredient_uri))
    return


if __name__ == '__main__':
    if len(sys.argv) < 3:
        print("""
              Please provide parameters:
              [1] recipe name on wikitaaable,
              [2] creator email address
              """)
    else:
        name, steps, ingredients = get_wiki_recipe(sys.argv[1])
        insert_recipe_data(name, sys.argv[2], steps, ingredients)
