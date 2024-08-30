from household import Household
from village import Village
from agent import Agent
from agent import Vec1
import pandas as pd
import utils
import random
import sys
random.seed(10)

num_house = 10
vec1_instance = Vec1()
village = utils.generate_random_village(num_house, 36, vec1_instance)
village.initialize_network()
village.initialize_network_relationship()
for _ in range(300): 
    village.run_simulation_step(vec1_instance)
    # utils.print_village_summary(village)
# print(village.network)
# village.plot_simulation_results(file_name = 'Plot.png')
# village.generate_animation(grid_dim=5)