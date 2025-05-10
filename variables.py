import scipy.special as sp
import pandas as pd
import numpy as np
import os
import json
import warnings
warnings.filterwarnings("ignore")

def load_parameters(file_path):
    with open(file_path, "r") as f:
        return json.load(f)

params = load_parameters("parameters.json")  

year = params["year"] # simulation years
num_house = params["num_house"] # number of initial houses
land_cells = params["land_cells"] # initial amount of land cells
prod_multiplier = params["prod_multiplier"]
fishing_discount = params["fishing_discount"]
fallow_ratio = params["fallow_ratio"] # % of the total land
fallow_period = params["fallow_period"] # years
food_expiration_steps = params["food_expiration_steps"] # initial 3, by changing it from 3 to 2, everything changed a lot!
marriage_from = params["marriage_from"]
marriage_to = params["marriage_to"]
bride_price_ratio = params["bride_price_ratio"] # by changing it up, I haven't observed any changes yet
land_ecovery_rate = params["land_ecovery_rate"] # initial 0.03
land_max_capacity = params["land_max_capacity"] # initial 10
initial_quality = params["initial_quality"] # initial 5
fish_chance = params["fish_chance"] # initial 0.3
exchange_rate = params["exchange_rate"] # luxury to food # by changing it from 10 to 30, the gini changed a lot
luxury_good_storage = params["luxury_good_storage"] # initial 0
storage_ratio_low = params["storage_ratio_low"]
storage_ratio_high = params["storage_ratio_high"]
land_capacity_low = params["land_capacity_low"]
max_member = params["max_member"]
excess_food_ratio = params["excess_food_ratio"] # initial 2
trade_back_start = params["trade_back_start"]
lux_per_year = params["lux_per_year"] # initial 5 lowering it lower the gini coefficient
land_depreciate_factor = params["land_depreciate_factor"] # very important, when it was 0.01, the population died after 1000 years
fertility_scaler = params["fertility_scaler"] # very important, society cannot live up to 1000 yr if it is below 4 or 3. however, then the accumulative population is too much
work_scale = params['work_scale']
file_path = params["file_path"]
file_name = params["file_name"]
file_name_csv = params['file_name_csv']
demog_file = params['demog_file']
luxury_goods_in_village = params['luxury_goods_in_village']

spare_food_enabled = True
fallow_farming = True

vec1 = pd.read_csv(demog_file)