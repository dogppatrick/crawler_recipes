import warnings

import pandas as pd
import requests
from bs4 import BeautifulSoup
from tqdm import tqdm

warnings.filterwarnings("ignore")

def url_to_csv(fn_url,pages:int=1):
    """
    pages:int last page
    """
    url_list = []
    for page in range(1,pages+1):
        url = f'https://recipes.instantpot.com/?index={page}'
        response = requests.get(url)
        html = BeautifulSoup(response.text)

        rec_box = html.select('div.items.clearfix')[0]
        recipies = rec_box.find_all(class_="item recipe")
        for rec in recipies:
            url = rec.find('a')['href']
            url_list.append(url)
    print(len(url_list))
    df = pd.DataFrame(url_list, columns=['url'])
    df.to_csv(fn_url, index=False)
    return df


class ExtractRecipe(object):
    def __init__(self,html:BeautifulSoup):
        self.html = html

    def get_title(self):
        return self.html.find('head').find('title').text

    def get_ingredients(self):
        format_ingredients = []
        # wpurp-recipe-ingredient-container 有 mobile / desktop 版本所以有兩個
        for ul_filter in self.html.select('ul'):
            e_class = ul_filter.get('class','')
            if 'wpurp-recipe-ingredient-container' in e_class:
                ingredients_raw = ul_filter.find_all('li')
                for ingredient in ingredients_raw:
                    format_ingredients.append([ing_part.text for ing_part in ingredient.find_all('span')])
                break
        return format_ingredients

    def get_introduction(self):
        introduction = []
        for ol_filter in self.html.select('ol'):
            e_class = ol_filter.get('class','')
            if 'wpurp-recipe-instruction-container' in e_class:
                introduction_raw = ol_filter.find_all('li')
                step = 1
                for intro in introduction_raw:
                    introduction.append([step,intro.select_one('span').text])
                    step +=1
        return introduction

    def get_prep_time(self):
        prep_time = ''
        try:
            prep_time = str(self.html.select('span.wpurp-recipe-prep-time')[0].text) + '_' + str(self.html.select('span.wpurp-recipe-prep-time-text')[0].text)
        except Exception as e:
            pass
        return prep_time

    def get_cook_time(self):
        cook_time = ''
        try:
            cook_time = str(self.html.select('span.wpurp-recipe-cook-time')[0].text) + '_' + str(self.html.select('span.wpurp-recipe-cook-time-text')[0].text)
        except Exception as e:
            pass
        return cook_time

fn_url = "./recipes_url_list_1031.csv"
result_fn = './recipes_data_1101.csv'
batch = 10
url_to_csv(fn_url, 54)
print(f'url_list done')
urls = list(pd.read_csv(fn_url)['url'])
recipes_data = []
for url in tqdm(urls):
    response = requests.get(url)
    html = BeautifulSoup(response.text)
    extract_rec = ExtractRecipe(html)
    title = extract_rec.get_title()
    prep_time = extract_rec.get_prep_time()
    cook_time = extract_rec.get_cook_time()
    ingredients = extract_rec.get_ingredients()
    introductions = extract_rec.get_introduction()
    recipes_data.append({
        'url': url,
        'title': title,
        'prep_time': prep_time,
        'cook_time': cook_time,
        'ingredients':ingredients,
        'introductions':introductions
    })

    if len(recipes_data) > batch:
        df = pd.DataFrame(recipes_data)
        df.to_csv(result_fn, index=False, mode='a', header=False)
        recipes_data = []

