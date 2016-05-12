from config import *

# from rdflib.namespace import RDFS
from rdflib.plugins.stores import sparqlstore
from rdflib import Namespace

store = sparqlstore.SPARQLUpdateStore()
store.open((STARDOG_ENDPOINT, STARDOG_ENDPOINT))
store.setCredentials(STARDOG_USERNAME, STARDOG_PASSWORD)

mfg_namespace = Namespace('http://www.food-groups.com/ontology#')

store.bind('mfg', mfg_namespace)

if __name__ == '__main__':
    print("Getting food with as name 'Pancakes'")
    query = "SELECT ?id ?type where {?id a ?type ; mfg:hasFoodName 'Pancakes'}"
    for result in store.query(query):
        print("ID:", result.id, ", type:", result.type)
