# Name of a recipe
wiki_recipe = """
SELECT ?label WHERE {
  { wiki:%s rdfs:label ?label }
}
"""

# Steps of recipe
wiki_steps = """
SELECT ?stepnb ?stepDescr WHERE {
  wiki:%s wiki:Property-3AHas_preparation ?step .
  ?step wiki:Property-3AStep ?stepDescr .
  ?step wiki:Property-3AStepnb ?stepnb .
}
"""

# Ingredients of recipe
wiki_ingredients = """
SELECT ?ingredientName ?ingredientQuantity ?ingredientUnit WHERE {
  wiki:%s wiki:Property-3AHas_ingredient_line ?ingredient .
  ?ingredient wiki:Property-3AIngredient ?ingrCategory .
  OPTIONAL {
    ?ingredient wiki:Property-3AIngredient_quantity ?ingredientQuantity .
    ?ingredient wiki:Property-3AIngredient_unit ?ingredientUnit .}
  ?ingrCategory rdfs:label ?ingredientName .
}
"""
