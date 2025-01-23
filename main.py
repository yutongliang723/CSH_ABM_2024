from household import Household
from village import Village
from agent import Agent
from agent import Vec1
import pandas as pd
import utils
import random
import math
import sys
random.seed(10)
# args = sys.argv
# if len(args) > 1:
#     random.seed(int(args[1]))

num_house = 56 # number of initial houses
land_cells = 56 # initial amount of land cells
year = 1000 # simulation years
prod_multiplier = 1
fishing_discount = 1
fallow_ratio = 50 # % of the total land
fallow_period = 5 # years
food_expiration_steps = 2 # initial 3, by changing it from 3 to 2, everything changed a lot!
marriage_from = 10
marriage_to = 50
bride_price_ratio=  0.5 # by changing it up, I haven't observed any changes yet
land_ecovery_rate = 0.01 # initial 0.03
land_max_capacity = 20 # initial 10
initial_quality = 5 # initial 5
fish_chance = 0.3 # initial 0.3
exchange_rate = 10 # luxury to food # by changing it from 10 to 30, the gini changed a lot
luxury_good_storage = 0 # initial
storage_ratio_low = 0.2
storage_ratio_high = 1.5
land_capacity_low = 1
max_member = 5
excess_food_ratio = 2 # initial 2
trade_back_start = 50
lux_per_year = 3 # initial 5 lowering it lower the gini coefficient

vec1_instance = Vec1()
village = utils.generate_random_village(num_house, land_cells, vec1_instance, food_expiration_steps, land_ecovery_rate, land_max_capacity, initial_quality, fish_chance, fallow_period)
village.initialize_network()
village.initialize_network_relationship()
for _ in range(year): 
    village.run_simulation_step(vec1_instance, prod_multiplier = prod_multiplier, fishing_discount = fishing_discount, fallow_ratio = fallow_ratio, fallow_period = fallow_period, food_expiration_steps = food_expiration_steps, marriage_from = marriage_from, marriage_to = marriage_to, bride_price_ratio = bride_price_ratio, exchange_rate = exchange_rate, storage_ratio_low=storage_ratio_low, storage_ratio_high=storage_ratio_high, land_capacity_low = land_capacity_low, max_member=max_member, excess_food_ratio = excess_food_ratio, trade_back_start = trade_back_start, lux_per_year = lux_per_year, spare_food_enabled=False, fallow_farming = True)
    utils.print_village_summary(village)
    
village.plot_simulation_results(file_name = f"simulation_{year}")
# village.generate_animation(grid_dim=math.ceil(math.sqrt(land_cells)))