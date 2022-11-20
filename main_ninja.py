import re
import warnings
from pprint import pprint

import pandas as pd
import requests
from bs4 import BeautifulSoup
from tqdm import tqdm
from os.path import exists as file_exists
import sys
from datetime import datetime
 

warnings.filterwarnings("ignore")

class IngredientSplit(object):
    def __init__(self, raw_text):
        self.raw_text = raw_text
        self.unite_dict = {
            ' packet ':'packet',
            ' ounce ' : 'ounce',
            ' ounces ': 'ounce',
            ' box ': 'box',
            ' boxes ': 'box',
            ' cans ': 'can',  
            ' can ' : 'can',
            ' teaspoons ': 'teaspoon', 
            ' teaspoon ': 'teaspoon', 
            ' tsp. ': 'teaspoon',
            ' tsp ' : 'teaspoon',
            ' cups ' : 'cup',
            ' cup ': 'cup', 
            ' oz ' : 'oz',
            ' oz. ': 'oz',
            ' tablespoons ': 'tablespoon',
            ' tablespoon ': 'tablespoon', 
            ' tbsp. ': 'tablespoon',
            ' tbsp ': 'tablespoon',
            ' container ': 'container', 
            ' pounds ': 'pound', 
            ' pound ': 'pound', 
            ' inchs ': 'inch', 
            ' inch ': 'inch', 
            ' cloves ': 'clove', 
            ' clove ': 'clove',
            ' bags ': 'bag',
            ' bag ': 'bag',
            ' stalks ': 'stalk',
            ' stalk ': 'stalk',
            ' packages ': 'package',
            ' package ': 'package',
            ' stems ' : 'stem',
            ' stem ' : 'stem',
            ' strips ': 'strip',
            ' strip ': 'strip',
            ' cubes ': 'cube',
            ' cube ': 'cube',
            ' sticks ': 'stick',
            ' stick ': 'stick',
            ' slices ': 'slice',
            ' slice ': 'slice',
            ' jars ': 'jar',
            ' jar ': 'jar',
            ' envelopes ': 'envelope',
            ' envelope ': 'envelope',
            ' tube ' : 'tube',
            ' tubes ' : 'tube',
            ' dashes ': 'dash',
            ' dash ': 'dash',
        }

    def unit_mapping(self, unit):
        return self.unite_dict.get(unit, unit)

    def get_ingredients_amount(self):
        pattern = r"[0-9]{1,5}\/[0-9]{1,3}|[0-9]{1,3}"
        res = re.search(pattern, self.raw_text)
        return ''.join(re.search(pattern, self.raw_text).group()) if res else ''

    def get_ingredients_unit(self):
        raw_text = re.sub(r"\(.*\)","", self.raw_text).lower()
        for unit in self.unite_dict.keys():
            if unit in raw_text:
                return self.unit_mapping(unit)
        return ''

    def ingredient_split_result(self):
        try:
            ingredients_name = self.raw_text
            ingredients_amount = self.get_ingredients_amount()
            ingredients_unit = self.get_ingredients_unit()

            return ingredients_name, ingredients_amount, ingredients_unit
        except Exception as e:
            print(f'error: {self.raw_text}, {type(self.raw_text)}')

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

def get_device_info(url:str=""):
    try:
        response = requests.get(url)
        html = BeautifulSoup(response.text,features="html.parser")
        device = html.find("div",{"id":"TabbedVariants_Current"}).find("span",{"class":"middle"}).find("img")
        device_name = device['alt']
        device_image_url = device['data-original']
        return device_name , device_image_url
    except Exception as e:
        return "", ""

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
    url = recipe.get("url",'')
    device_name , device_image_url = get_device_info(url)
    for i in range(max_len):
        ingredient = ingredients[i] if ingredients[i]!='' else ''
        intro = introductions[i] if introductions[i]!=''  else ''
        if ingredient:
            ingredients_name, ingredients_amount, ingredients_unit = IngredientSplit(ingredient).ingredient_split_result()
        else:
            ingredients_name, ingredients_amount, ingredients_unit = '', '', ''
        intro_step = i +1  if intro else ''
        new_records.append({
            'url': url,
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
            'step_image':'',
            'device_name': device_name,
            'device_image_url':f'https://www.ninjakitchen.com{device_image_url}'
        })
    return new_records

def get_recipes_by_page_to_csv(fn,pages:int=1):
    """
    pages:int last page
    """
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
    if len(sys.argv) == 2:
        _, pages = sys.argv
        pages = int(pages)
    else:
        pages = 2
    dt = datetime.now()
    fn = f"./data/recipes_ninja_{pages}_pages_{dt.month}{dt.day}.csv"
    get_recipes_by_page_to_csv(fn,pages)
