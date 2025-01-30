import scipy.special as sp
import pandas as pd
import numpy as np
import os
import json
with open("parameters.json", "r") as f:
    params = json.load(f)

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
file_path = params["file_path"]
file_name = params["file_name"]

vec1 = pd.read_csv('demog_vectors.csv')
# vec1 = vec1.rename_axis('age').reset_index()
# new_max_age = 60
# old_max_age = vec1['age'].max()
# scale_factor = new_max_age / old_max_age
# scale_factor = 1
# other_para = ['rho', 'pstar', 'mortparms']
# bins = pd.cut(vec1['age'], bins=new_max_age)
# binned_vec = pd.DataFrame()
# for col in other_para:
#     binned_col = vec1.groupby(bins, observed=False).agg({col: 'mean'}).reset_index()
#     binned_col[col] = binned_col[col] * scale_factor
#     binned_vec[col] = binned_col[col]

# bin_centers = [interval.mid for interval in binned_col['age']]

# binned_vec = binned_vec.rename_axis('age_new').reset_index()
# binned_vec.loc[binned_vec['age_new'] <= 3, 'pstar'] *= 0.5
# binned_vec['mstar'] = vec1['mstar']
# binned_vec['fertparm'] = vec1['fertparm']
# binned_vec['mortscale'] = vec1['mortscale']
# binned_vec['fertscale'] = vec1['fertscale']
# binned_vec['phi'] = vec1['phi']
# vec1 = binned_vec


