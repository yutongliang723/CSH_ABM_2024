import os
import json
import logging
import datetime
import sys
import itertools
import pandas as pd
from household import Household
from village import *
from agent import *
from vec import *
from demog_scale import *
import utils
import warnings
warnings.filterwarnings("ignore")

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

RESULTS_FOLDER = "experiment_results"
os.makedirs(RESULTS_FOLDER, exist_ok=True)

def load_experiment_parameters(file_path="params_exp_short.json"):
    try:
        with open(file_path, "r") as f:
            params = json.load(f)
        logging.info("Experiment parameters loaded successfully.")
        return params["simulation_parameters"]
    except Exception as e:
        logging.error(f"Error loading parameters: {e}")
        sys.exit(1)

def get_param_combinations(params):
    param_keys = [k for k in params.keys() if k != "conditions"]
    condition_keys = list(params["conditions"].keys())
    
    param_values = [params[k] if isinstance(params[k], list) else [params[k]] for k in param_keys]
    condition_values = [params["conditions"][k] if isinstance(params["conditions"][k], list) else [params["conditions"][k]] for k in condition_keys]
    
    param_combinations = list(itertools.product(*param_values))
    condition_combinations = list(itertools.product(*condition_values))
    
    all_combinations = list(itertools.product(param_combinations, condition_combinations))
    return param_keys, condition_keys, all_combinations

def make_clickable_image(relative_path):
    """Creates an HTML clickable image link for local files."""
    abs_path = os.path.abspath(relative_path)
    return f'<a href="file://{abs_path}" target="_blank">{os.path.basename(relative_path)}</a>'

def run_experiment(experiment_id, params, param_values, condition_values):
    timestamp = datetime.datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    img_name_1 = f"experiment_{experiment_id}_1.png"
    img_name_2 = f"experiment_{experiment_id}_2.png"
    img_path_1 = os.path.join(RESULTS_FOLDER, img_name_1)
    img_path_2 = os.path.join(RESULTS_FOLDER, img_name_2)
    csv_path = os.path.join(RESULTS_FOLDER, f"experiment_{experiment_id}.csv")
    
    params.update(dict(zip(param_keys, param_values)))
    params["conditions"].update(dict(zip(condition_keys, condition_values)))
    
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
    
    for _ in range(params["year"]):
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
            farming_counter_max = params['farming_counter_max']
            )

    
    eigen = village.get_eigen_value(vec1_instance)
    import statistics

    def compute_stats(values):
        if not values:
            return {"min": None, "avg": None, "max": None, "std": None}
        return {
            "min": min(values),
            "avg": sum(values) / len(values),
            "max": max(values),
            "std": statistics.stdev(values) if len(values) > 1 else 0
        }

    metrics = {
        "Population Over Time": village.population_over_time,
        "Occupied Land Capacity": village.land_capacity_over_time,
        "All Land Capacity": village.land_capacity_over_time_all,
        "Food Storage Over Time": village.food_storage_over_time,
        "Average Household Fertility": village.average_fertility_over_time,
        "Average Age Over Time": village.average_age,
        "Average Life Span Over Time": village.average_life_span[1:],
        "Accumulated Population": village.population_accumulation[1:],
        "Gini Coefficients": village.gini_coefficients,
        "# Households": village.num_households,
        "# Migrants": village.num_migrated
    }
    village.migrate_counter = 0 # to reset the migration records per year      
    
    avg_metrics = {k: compute_stats(v) for k, v in metrics.items()}
    # avg_metrics = {k: sum(v) / len(v) if v else None for k, v in metrics.items()} # getting the average of the list for each output para
    avg_metrics.update({
        "Experiment ID": experiment_id,
        "Timestamp": timestamp,
        "Image Path 1": make_clickable_image(img_path_1),
        "Image Path 2": make_clickable_image(img_path_2),
        "Eigenvalue": eigen,
    })
    
    # Add parameters as columns
    avg_metrics.update(params)
    
    village.plot_simulation_results(img_path_1, csv_path, vec1_instance)
    village.plot_simulation_results_second(img_path_2)
    
    return avg_metrics

def main():
    params = load_experiment_parameters()
    global param_keys, condition_keys
    param_keys, condition_keys, all_combinations = get_param_combinations(params)
    
    results = []
    
    for experiment_id, (param_values, condition_values) in enumerate(all_combinations):
        logging.info(f"Running experiment {experiment_id + 1}/{len(all_combinations)}")
        avg_metrics = run_experiment(experiment_id, params.copy(), param_values, condition_values)
        results.append(avg_metrics)
    
    results_df = pd.DataFrame(results)
    
    # Reorder columns to have ID, Timestamp, and file paths first
    column_order = ["Experiment ID", "Timestamp", "Image Path 1", "Image Path 2"] + [col for col in results_df.columns if col not in ["Experiment ID", "Timestamp", "Image Path 1", "Image Path 2"]]
    results_df = results_df[column_order]
    
    results_df.to_html(os.path.join(RESULTS_FOLDER, "all_experiments_summary.html"), index=False, escape=False)
    logging.info("All experiments completed. Summary saved.")

if __name__ == "__main__":
    main()