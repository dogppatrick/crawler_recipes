import re
import warnings
from pprint import pprint

import pandas as pd
import requests
from tqdm import tqdm
from os.path import exists as file_exists

warnings.filterwarnings("ignore")

class IngredientSplit(object):
    def __init__(self, raw_text):
        self.raw_text = raw_text
        self.unit_sets = set(['packet', 'ounces', 'can', 'teaspoon', 'cup', 'container', 'pounds', 'inch'])

    def get_ingredients_amount(self):
        pattern = r"[0-9]{1,5}\/[0-9]{1,3}|[0-9]{1,3}"
        res = re.search(pattern, self.raw_text)
        return ''.join(re.search(pattern, self.raw_text).group()) if res else ''

    def get_ingredients_unit(self):
        for unit in self.unit_sets:
            if unit in self.raw_text:
                return unit

    def ingredient_split_result(self):
        ingredients_name = self.raw_text
        ingredients_amount = self.get_ingredients_amount()
        ingredients_unit = self.get_ingredients_unit()

        return ingredients_name, ingredients_amount, ingredients_unit

def clean_html(txt:str, li_replace:bool=True):
    if li_replace:
        txt = txt.replace("<li>","[obj_start]")
        if '[object_start]' not in txt:
            txt = '[object_start]' + txt.replace(r"<br/>", "[obj_start]").replace(r"<br>", "[obj_start]")
        if '[object_start]' not in txt:
            txt = '[object_start]' + txt.replace(",","[obj_start]")
    txt = re.sub(r"<(.*?)>","",txt) # remove html items
    remove_list = ['\n','\r','\t']
    for icon in remove_list:
        txt = txt.replace(icon,' ')
    while '  'in txt:
        txt = txt.replace('  ',' ')
    return txt

def extract_recipe(recipie:dict):
    img_url = recipie.get("recipeImage",{})
    if img_url:
        img_url_large = f'https://www.ninjakitchen.com/{img_url.get("large","")}'
        img_url_small = f'https://www.ninjakitchen.com/{img_url.get("small","")}'
    return {
        'url': f'https://www.ninjakitchen.com{recipie.get("recipeUrl")}',
        'language': 'eng',
        'image_large':img_url_large,
        'image_small':img_url_small,
        'title': recipie.get("title"),
        'prep_time': recipie.get("prepServe"),
        'cook_time': recipie.get("cooktime"),
        'servings': recipie.get("servings"),
        'ingredients':clean_html(recipie.get("ingredients"), li_replace=True),
        'introductions':clean_html(recipie.get("instructions"), li_replace=True),
        
    }

def detail_recipe(recipe:dict):
    """
    recipes_data >> detail recipes data with table join like result
    """
    new_records = []
    ingredients = recipe.pop("ingredients","").split("[obj_start]")[1:]
    ingredients = [igr for igr in ingredients if len(igr)>3]
    introductions = recipe.pop("introductions","").split("[obj_start]")[1:]
    introductions = [intro_step for intro_step in introductions if len(intro_step)>1]
    max_len = max(len(ingredients), len(introductions))
    ingredients += [''] * (max_len - len(ingredients))
    introductions += [''] * (max_len - len(introductions))
    for i in range(max_len):
        ingredient = ingredients[i] if ingredients[i]!='' else ''
        intro = introductions[i] if introductions[i]!=''  else ''
        if ingredient:
            ingredients_name, ingredients_amount, ingredients_unit = IngredientSplit(ingredient).ingredient_split_result()
        else:
            ingredients_name, ingredients_amount, ingredients_unit = '', '', ''
        intro_step = i +1  if intro else ''
        new_records.append({
            'url': recipe.get("url",''),
            'language': recipe.get("language",'eng'),
            'image_large': recipe.get("image_large",''),
            'image_small': recipe.get("image_small",''),
            'title': recipe.get("title",''),
            'prep_time': recipe.get("prep_time",''),
            'cook_time': recipe.get("cook_time",''),
            'servings': recipe.get("servings",''),
            'ingredients_name': ingredients_name,
            'ingredients_amount': ingredients_amount,
            'ingredients_unit': ingredients_unit,
            'step': intro_step,
            'instructions' : intro,
            'step_image':''
        })
    return new_records

def get_recipes_by_page_to_csv(fn,pages:int=1):
    """
    pages:int last page
    """
    page = 1
    records = []
    for page in tqdm(range(1,pages+1)):
        url = f'https://www.ninjakitchen.com/api/recipe/?q=&sort=A-Z&tags=&page={page}'
        payload = {}
        json_headers = {'accept': 'application/json', 'Content-Type': 'application/json'}
        response = requests.request("GET", url, headers=json_headers, data=payload)
        data = response.json()
        recipes = [extract_recipe(rec) for rec in data.get("recipes")]
        for recipe in recipes:
            records += detail_recipe(recipe)
            if len(records) > 200:
                df = pd.DataFrame(records)
                if file_exists(fn):
                    df.to_csv(fn, index=False, mode='a', header=False)
                else:
                    df.to_csv(fn, index=False, mode='a', header=True)
                records = []

    df = pd.DataFrame(records)
    if file_exists(fn):
        df.to_csv(fn, index=False, mode='a', header=False)
    else:
        df.to_csv(fn, index=False, mode='a', header=True)

if __name__ == '__main__':
    fn = "./data/recipes_ninja_139_pages.csv"
    pages = 139
    get_recipes_by_page_to_csv(fn,pages)
