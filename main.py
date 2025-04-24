import os
import json
import logging
import datetime
import sys
import random
import math
import pandas as pd
from household import Household
from village import *
from agent import *
from vec import *
from village import *
# from variables import *
from demog_scale import *
import utils

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def load_parameters(file_path="parameters.json"):

    try:
        with open(file_path, "r") as f:
            params = json.load(f)
        logging.info("Parameters loaded successfully.")
        return params["simulation_parameters"]
    except Exception as e:
        logging.error(f"Error loading parameters: {e}")
        sys.exit(1)

def setup_simulation_parameters(params):
    timestamp = datetime.datetime.now().strftime("%d-%m-%Y&%H-%M-%S")
    folder_name = f"run_results/{timestamp}"
    os.makedirs(folder_name, exist_ok=True)

    file_name = f"{folder_name}/results"
    file_name_second = f"{folder_name}/results_second"
    file_path = f"{folder_name}/simulation_output"
    file_name_csv = f"{folder_name}/simulation_results.csv"

    with open(os.path.join(folder_name, "parameters.json"), "w") as f:
        json.dump(params, f, indent=4)

    return folder_name, file_name, file_path, file_name_csv, file_name_second

def initialize_village(params):

    vec1_instance = Vec1(params)
    village = utils.generate_random_village(
    num_households=params["num_house"],  
    num_land_cells=params["land_cells"], 
    vec1_instance=vec1_instance, 
    food_expiration_steps=params["food_expiration_steps"],
    land_ecovery_rate=params["land_ecovery_rate"], 
    land_max_capacity=params["land_max_capacity"],
    initial_quality=params["initial_quality"], 
    # fish_chance=params["fish_chance"], 
    fallow_period=params["fallow_period"], 
    luxury_goods_in_village=params["luxury_goods_in_village"]
)
    village.initialize_network()
    village.initialize_network_relationship()
    return village

def run_simulation(village, vec1_instance, params):
    # pd.read_csv(params['demog_file'])
    for _ in range(params["year"]):
        village.run_simulation_step(
            vec1_instance = vec1_instance, 
            prod_multiplier=params["prod_multiplier"], 
            fishing_discount=params["fishing_discount"], 
            fallow_ratio=params["fallow_ratio"], 
            fallow_period=params["fallow_period"], 
            food_expiration_steps=params["food_expiration_steps"], 
            marriage_from=params["marriage_from"], 
            marriage_to=params["marriage_to"], 
            bride_price_ratio=params["bride_price_ratio"], 
            bride_price = params['bride_price'],
            exchange_rate=params["exchange_rate"], 
            storage_ratio_low=params["storage_ratio_low"], 
            storage_ratio_high=params["storage_ratio_high"], 
            land_capacity_low=params["land_capacity_low"], 
            max_member=params["max_member"], 
            excess_food_ratio=params["excess_food_ratio"], 
            trade_back_start=params["trade_back_start"], 
            lux_per_year=params["lux_per_year"], 
            land_depreciate_factor=params["land_depreciate_factor"], 
            fertility_scaler=params["fertility_scaler"], 
            work_scale=params["work_scale"], 
            conditions = params['conditions'],
            prob_emigrate = params['prob_emigrate'],
            emigrate_enabled = params['emigrate_enabled'],
            spare_food_enabled=params["spare_food_enabled"],
            fallow_farming=params["fallow_farming"],
            trading_enabled = params['trading_enabled'],
            farming_counter_max = params['farming_counter_max']
            )

def save_results(village, file_name, file_name_second, file_name_csv, vec1_instance, params, file_name_gif):
    village.plot_simulation_results(file_name, file_name_csv, vec1_instance)
    village.plot_simulation_results_second(file_name_second)
    village.generate_animation(file_name_gif, grid_dim=math.ceil(math.sqrt(params['land_cells'])))

def main():

    random.seed(10)
    demog_scale()
    params = load_parameters()
    _, file_name, _, file_name_csv, file_name_second = setup_simulation_parameters(params)

    vec1_instance = Vec1(params)
    village = initialize_village(params)
    run_simulation(village, vec1_instance, params)
    save_results(village, file_name, file_name_second, file_name_csv, vec1_instance, params, params['file_name_gif'])
    
if __name__ == "__main__":
    main()