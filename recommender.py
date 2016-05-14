import numpy as np
import pandas as pd
from scipy.spatial.distance import euclidean
from scipy.stats.stats import pearsonr
from math import sqrt

class Recommender(object):

	def __init__(self):
		super(Recommender, self).__init__()
		self.user_matrix = 0

	# Loads the data and transforms it in matrix notation
	# !!!Temporary Assumption: data comes from Noah's SPARQL query (see Slack)
	def load_data(self, data):
		user_dict = {}
		for idx, row in data.iterrows():
			if row['uploader'] in user_dict:
				ingredient_dict = user_dict[row['uploader']]
				if row['ingredientName'] in ingredient_dict:
					ingredient_dict[row['ingredientName']] += row['count']
				else:
					ingredient_dict[row['ingredientName']] = row['count']
			else:
				user_dict[row['uploader']] = {row['ingredientName']: row['count']}
		self.user_matrix = pd.DataFrame.from_dict(user_dict).fillna(0)
		return


	# Returns the Euclidian distance between two users
	def euclidian(self, user1, user2):
		return euclidean(self.user_matrix.loc[:,user1], self.user_matrix.loc[:,user2])

	# Returns the Pearson correlation coefficient between two users
	def pearson(self, user1, user2):
		return pearsonr(self.user_matrix.loc[:,user1], self.user_matrix.loc[:,user2])[0]

	# Returns the best matches for the given user from the matrix
	# Number of the results and similarity function are optional parameters
	def best_matches(self, user, n=5, similarity='pearson'):
		if similarity == 'pearson':
			scores = [(self.pearson(user,other), other) for other in self.user_matrix.columns.values if other != user]
		elif similarity == 'euclidean':
			scores = [(self.euclidean(user,other), other) for other in self.user_matrix.columns.values if other != user]
		scores.sort()
		scores.reverse()
		return scores[:n]

	# My suggestions for the recommender:
	# [1] get some random recipes, assign each of them a score by doing a weighted average over the recipe's ingredients, where
	#		x_i = i-th ingredient in the recipe
	#		w_i = frequency of i-th ingredient in user-ingredient matrix
	# [2] what you are currently doing: do correlations between users (pearson/euclidiean/...),
	#		then get a random recipe from the highest scoring user (?)
	# maybe experiment with both approaches, all the methods needed for these two approaches should be available now :)

if __name__ == '__main__':
	data = pd.read_csv('./export.csv')
	recsys = Recommender()
	recsys.load_data(data)
	print(recsys.best_matches('jens.nevens@vub.ac.be'))
