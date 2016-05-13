# import credentials
from config import *

# from rdflib.namespace import RDFS
from rdflib.plugins.stores import sparqlstore
from rdflib import Namespace

class FoodDatabase(object):

	def __init__(self):
		super(FoodDatabase, self).__init__()
		self.user_matrix = 0

	def 