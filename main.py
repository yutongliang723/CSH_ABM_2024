from household import Household
from village import Village
from agent import Agent
from agent import Vec1
import variables
import pandas as pd
import utils
import random
import math
import sys
from IPython.display import clear_output


pars = variables.load_params("parameters.json")

random.seed(10)
# args = sys.argv
# if len(args) > 1:
#     random.seed(int(args[1]))
vec1_instance = Vec1()
village = utils.generate_random_village(pars.num_house, pars.land_cells, vec1_instance, pars.food_expiration_steps, pars.land_ecovery_rate, pars.land_max_capacity, pars.initial_quality, pars.fish_chance, pars.fallow_period)
village.initialize_network()
village.initialize_network_relationship()
for _ in range(pars.year): 
    village.run_simulation_step(vec1_instance, pars)
    # utils.print_village_summary(village)
    
village.plot_simulation_results(pars.file_name)
village.generate_animation(pars.file_path, grid_dim=math.ceil(math.sqrt(pars.land_cells)))
clear_output()
