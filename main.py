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

num_house = 10
year = 500
land_cells = 36
vec1_instance = Vec1()
village = utils.generate_random_village(num_house, land_cells, vec1_instance)
village.initialize_network()
village.initialize_network_relationship()
for _ in range(year): 
    village.run_simulation_step(vec1_instance, prod_multiplier = 1, spare_food_enabled=False)
    # utils.print_village_summary(village)
    
# village.plot_simulation_results(file_name = f"simulation_{year}")
# village.generate_animation(grid_dim=int(math.sqrt(land_cells)))