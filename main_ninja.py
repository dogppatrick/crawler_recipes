import re
import warnings
from pprint import pprint

import pandas as pd
import requests
from tqdm import tqdm
from os.path import exists as file_exists

warnings.filterwarnings("ignore")

def clean_html(txt):
    txt = re.sub(r"<(.*?)>","",txt) # remove html items
    remove_list = ['\n','\r','\t']
    for icon in remove_list:
        txt = txt.replace(icon,' ')
    while '  'in txt:
        txt = txt.replace('  ',' ')
    return txt

def extract_recipe(recipie:dict):
    img_url = recipie.get("recipeImage",{}).get("large","")
    if img_url:
        img_url = f'https://www.ninjakitchen.com/{img_url}'
    return {
        'url': f'https://www.ninjakitchen.com/{recipie.get("recipeUrl")}',
        'language': 'eng',
        'hero_image':img_url,
        'title': recipie.get("title"),
        'prep_time': recipie.get("prepServe"),
        'cook_time': recipie.get("cooktime"),
        'servings': recipie.get("servings"),
        'ingredients':clean_html(recipie.get("ingredients")),
        'introductions':clean_html(recipie.get("instructions")),
        
    }

def get_recipes_by_page_to_csv(fn,pages:int=1):
    """
    pages:int last page
    """
    page = 1
    all_recipes = []
    for page in tqdm(range(1,pages+1)):
        url = f'https://www.ninjakitchen.com/api/recipe/?q=&sort=A-Z&tags=&page={page}'
        payload = {}
        json_headers = {'accept': 'application/json', 'Content-Type': 'application/json'}
        response = requests.request("GET", url, headers=json_headers, data=payload)
        data = response.json()
        recpies = data.get("recipes")
        all_recipes += [extract_recipe(rec) for rec in recpies]
        if len(recpies) > 100:
            df = pd.DataFrame(all_recipes)
            if file_exists(fn):
                df.to_csv(fn, index=False, mode='a', header=False)
            else:
                df.to_csv(fn, index=False, mode='a', header=True)
            all_recipes = []

    df = pd.DataFrame(all_recipes)
    if file_exists(fn):
        df.to_csv(fn, index=False, mode='a', header=False)
    else:
        df.to_csv(fn, index=False, mode='a', header=True)



fn = "./recipes_ninja_20_page.csv"
pages = 20
get_recipes_by_page_to_csv(fn,pages)