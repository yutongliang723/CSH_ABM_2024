from household import Household
from village import Village
from agent import Agent
from agent import Vec1
from variables import *
import pandas as pd
import utils
import random
import math
import sys
from IPython.display import clear_output

random.seed(10)
# args = sys.argv
# if len(args) > 1:
#     random.seed(int(args[1]))
vec1_instance = Vec1()
village = utils.generate_random_village(num_house, land_cells, vec1_instance, food_expiration_steps, land_ecovery_rate, land_max_capacity, initial_quality, fish_chance, fallow_period)
village.initialize_network()
village.initialize_network_relationship()
for _ in range(year): 
    village.run_simulation_step(vec1_instance, prod_multiplier = prod_multiplier, fishing_discount = fishing_discount, fallow_ratio = fallow_ratio, fallow_period = fallow_period, food_expiration_steps = food_expiration_steps, marriage_from = marriage_from, marriage_to = marriage_to, bride_price_ratio = bride_price_ratio, exchange_rate = exchange_rate, storage_ratio_low=storage_ratio_low, storage_ratio_high=storage_ratio_high, land_capacity_low = land_capacity_low, max_member=max_member, excess_food_ratio = excess_food_ratio, trade_back_start = trade_back_start, lux_per_year = lux_per_year, land_depreciate_factor = land_depreciate_factor, fertility_scaler = fertility_scaler, spare_food_enabled=False, fallow_farming = True)
    # utils.print_village_summary(village)
    
village.plot_simulation_results(file_name)
village.generate_animation(file_path, grid_dim=math.ceil(math.sqrt(land_cells)))
clear_output()
