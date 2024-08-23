from household import Household
from village import Village
from agent import Agent
from agent import Vec1
import pandas as pd
import utils
# vec1 = pd.read_csv('demog_vectors.csv')


vec1_instance = Vec1()
village = utils.generate_random_village(5, 36, vec1_instance)
village.initialize_network()
# print('nw', village.network)
for _ in range(300): 
    village.run_simulation_step(vec1_instance)
    # utils.print_village_summary(village)
# print(village.network)
village.plot_simulation_results(file_name = 'Plot.png')
village.generate_animation(grid_dim=5)