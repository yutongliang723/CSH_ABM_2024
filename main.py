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

    file_name = f"{folder_name}/results.svg"
    file_name_second = f"{folder_name}/results_second.svg"
    file_path = f"{folder_name}/simulation_output"
    file_name_csv = f"{folder_name}/simulation_results.csv"

    with open(os.path.join(folder_name, "parameters.json"), "w") as f:
        json.dump(params, f, indent=4)
    print("setup_simulation_parameters")
    return folder_name, file_name, file_path, file_name_csv, file_name_second


def initialize_village(params):
    vec1_instance = Vec1(params)
    village = utils.generate_random_village(
        num_households=params["num_house"],  
        num_land_cells=params["land_cells"], 
        vec1_instance=vec1_instance, 
        food_expiration_steps=params["food_expiration_steps"],
        land_recovery_rate=params["land_recovery_rate"], 
        land_max_capacity=params["land_max_capacity"],
        initial_quality=params["initial_quality"], 
        fallow_period=params["fallow_period"], 
        luxury_goods_in_village=params["luxury_goods_in_village"]
    )
    try:
        village.initialize_network()
    except Exception as e:
        print(e)
        raise

    print("\nInitializing network relationships...")
    try:
        village.initialize_network_relationship()
    except Exception as e:
        print(e)
        raise
    return village

def simulate_temperature(params, T0=0.0, mu=0.0, theta=0.1, sigma=0.3):
    """
    Simulate temperature anomaly via Ornstein-Uhlenbeck (mean-reverting):
    dT = theta*(mu - T)*dt + sigma * dW
    Returns an array of temperatures (anomalies).
    """
    years = params["year"]
    temps = np.zeros(years)
    temps[0] = T0
    dt = 1.0
    for i in range(1, years):
        dT = theta * (mu - temps[i-1]) * dt + sigma * np.random.randn() * np.sqrt(dt)
        temps[i] = temps[i-1] + dT
    return temps

def temp_to_effect(params, T_opt=0.0, alpha=0.3, min_effect=0.3):
    """
    Convert temperature anomaly to a production multiplier.
    Peak at T = T_opt, downward quadratic penalty.
    effect = 1 - alpha*(T - T_opt)^2
    Clip at min_effect.
    """
    temps = simulate_temperature(params, T0=0.0, mu=0.0, theta=0.05, sigma=0.2)
    effects = 1.0 - alpha * (temps - T_opt)**2
    effects = np.clip(effects, min_effect, None)
    return effects

def run_simulation(village, vec1_instance, params):
    effects = temp_to_effect(params, T_opt=0.0, alpha=0.25, min_effect=0.4)
    for year in range(params["year"]):
        village.run_simulation_step(
            vec1_instance = vec1_instance, 
            prod_multiplier=params["prod_multiplier"], 
            fishing_discount=params["fishing_discount"], 
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
            farming_counter_max = params['farming_counter_max'],
            climate = effects[year]
            )

def save_results(village, file_name, file_name_second, params, file_name_gif):
    utils.plot_simulation_results(village, file_name)
    utils.plot_simulation_results_second(village, file_name_second)
    utils.generate_animation(village, file_name_gif, grid_dim=math.ceil(math.sqrt(params['land_cells'])))


def main():
    # random.seed(10)
    demog_scale()
    params = load_parameters()
    _, file_name, _, file_name_csv, file_name_second = setup_simulation_parameters(params)
    vec1_instance = Vec1(params)
    village = initialize_village(params)
    run_simulation(village, vec1_instance, params)
    save_results(village, file_name, file_name_second, params, params['file_name_gif'])
    
if __name__ == "__main__":
    main()