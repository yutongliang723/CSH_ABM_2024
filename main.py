from household import Household
from village import Village
from agent import Agent
from agent import Vec1
import pandas as pd
import utils
vec1 = pd.read_csv('demog_vectors.csv')


vec1_instance = Vec1()
village = utils.generate_random_village(10, vec1_instance)
for _ in range(100): 
    village.run_simulation_step()
    utils.print_village_summary(village)
village.plot_simulation_results()

