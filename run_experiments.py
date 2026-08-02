import os
import json
import random
import math
import pandas as pd
import numpy as np
from scipy import stats
import datetime
import sys
import logging
import copy
from village import Village
from household import Household
from agent import Agent
from vec import Vec1
from demog_scale import demog_scale
import utils
from clock import Clock

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

def save_parameters(params, folder):
    with open(os.path.join(folder, "parameters.json"), "w") as f:
        json.dump(params, f, indent=4)

def run_single_simulation(params, seed, experiment_name=None, run_number=None):
    """Run one simulation with given params and seed"""
    random.seed(seed)
    np.random.seed(seed)
    
    if experiment_name and run_number:
        timestamp = datetime.datetime.now().strftime("%d-%m-%Y&%H-%M-%S")
        folder_name = f"run_results/experiments/{experiment_name}_{timestamp}_run{run_number}"
    else:
        timestamp = datetime.datetime.now().strftime("%d-%m-%Y&%H-%M-%S")
        folder_name = f"run_results/experiments/experiment_{timestamp}"
    
    os.makedirs(folder_name, exist_ok=True)
    
    plots_folder = os.path.join(folder_name, 'plots')
    data_folder = os.path.join(folder_name, 'data')
    os.makedirs(plots_folder, exist_ok=True)
    os.makedirs(data_folder, exist_ok=True)
    
    save_parameters(params, folder_name)
    
    vec1_instance = Vec1(params)
    village = utils.generate_random_village(
        num_households=params["num_house"],
        num_land_cells=params["land_cells"],
        vec1_instance=vec1_instance,
        food_expiration_steps=params["food_expiration_steps"],
        land_recovery_rate=params["land_recovery_rate"],
        land_max_capacity=params["land_max_capacity"],
        fallow_period=params["fallow_period"],
        resources={"stone": 0, "obsidian": 0, "jade": 0},
        clock=Clock(),
        fish=params["fish"]
    )
    village.initialize_network()
    village.initialize_network_relationship()
    
    effects = temp_to_effect(params, T_opt=0.0, alpha=0.25, min_effect=0.4)
    mechanisms = params.get('mechanisms', {})
    
    for year in range(params["year"]):
        village.run_simulation_step(
            vec1_instance=vec1_instance,
            prod_multiplier=params["prod_multiplier"],
            fishing_discount=params["fishing_discount"],
            fallow_period=params["fallow_period"],
            food_expiration_steps=params["food_expiration_steps"],
            marriage_from=params["marriage_from"],
            marriage_to=params["marriage_to"],
            bride_price_ratio=params["bride_price_ratio"],
            bride_price=params['bride_price'],
            exchange_rate=params["exchange_rate"],
            storage_ratio_low=params["storage_ratio_low"],
            land_capacity_low=params["land_capacity_low"],
            max_member=params["max_member"],
            land_depreciate_factor=params["land_depreciate_factor"],
            fertility_scaler=params["fertility_scaler"],
            work_scale=params["work_scale"],
            conditions=params['conditions'],
            prob_emigrate=params['prob_emigrate'],
            emigrate_enabled=mechanisms.get('emigrate_enabled', True),
            spare_food_enabled=mechanisms.get('spare_food_enabled', True),
            fallow_farming=mechanisms.get('fallow_farming', True),
            trading_enabled=mechanisms.get('trading_enabled', True),
            shifting_cultivation=mechanisms.get('shifting_cultivation', True),
            farming_counter_max=params['farming_counter_max'],
            climate=effects[year] if mechanisms.get('climate_effects', True) else 1.0,
            trade_surplus_threshold=params['trade_surplus_threshold'],
            max_fish=params['max_fish'],
            mechanisms=mechanisms,
            marriage_min_wealth=params.get('marriage_min_wealth', 10.0)
        )
    
    print(f"Saving plots for {experiment_name} run {run_number}...")
    
    file_name = os.path.join(plots_folder, "results.svg")
    file_name_second = os.path.join(plots_folder, "results_second.svg")
    file_name_gif = os.path.join(plots_folder, "simulation.gif")
    
    utils.plot_simulation_results(village, file_name)
    utils.plot_simulation_results_second(village, file_name_second)
    utils.generate_animation(village, file_name_gif, grid_dim=math.ceil(math.sqrt(params['land_cells'])))
    
    save_numerical_data(village, data_folder)
    
    final_gini = village.gini_coefficients[-1] if village.gini_coefficients else 0
    total_population = sum(len(h.members) for h in village.households)
    total_food = sum(sum(amount for amount, _ in h.food_storage) for h in village.households)
    
    return {
        'gini': final_gini,
        'population': total_population,
        'food': total_food,
        'num_households': len(village.households),
        'folder': folder_name,
        'plots_folder': plots_folder,
        'data_folder': data_folder
    }

def temp_to_effect(params, T_opt=0.0, alpha=0.3, min_effect=0.3):
    """Simulate temperature anomaly via Ornstein-Uhlenbeck"""
    years = params["year"]
    temps = np.zeros(years)
    temps[0] = 0.0
    dt = 1.0
    for i in range(1, years):
        dT = 0.05 * (0.0 - temps[i-1]) * dt + 0.2 * np.random.randn() * np.sqrt(dt)
        temps[i] = temps[i-1] + dT
    effects = 1.0 - 0.25 * (temps - 0.0)**2
    effects = np.clip(effects, 0.3, None)
    return effects

def get_experiments():
    """Define all experiments to run"""
    
    all_mechanisms = {
        'spare_food_enabled': True,
        'fallow_farming': True,
        'emigrate_enabled': True,
        'trading_enabled': True,
        'shifting_cultivation': True,
        'fishing_enabled': True,
        'resource_discovery': True,
        'climate_effects': True,
        'marriage_enabled': True,
        'birth_limit_enabled': True,
        'marriage_min_wealth_check': True,
        'neighbor_boost_enabled': True  
    }
    
    experiments = {
        'baseline': {#
            'mechanisms': all_mechanisms.copy()
        },
        'no_birth_limit': {#
            'mechanisms': {**all_mechanisms, 'birth_limit_enabled': False}
        },
        
        'no_marriage_min_wealth': {#
            'mechanisms': {**all_mechanisms, 'marriage_min_wealth_check': False}
        },
        
        'marriage_min_wealth_high': {#
            'mechanisms': all_mechanisms.copy(),
            'params_override': {
                'marriage_min_wealth': 50.0
            }
        },
        'no_spare_food': {#
            'mechanisms': {**all_mechanisms, 'spare_food_enabled': False}
        },
        'no_fallow': {
            'mechanisms': {**all_mechanisms, 'fallow_farming': False}
        },
        'no_emigration': {
            'mechanisms': {**all_mechanisms, 'emigrate_enabled': False}
        },
        'no_trading': {
            'mechanisms': {**all_mechanisms, 'trading_enabled': False}
        },
        'no_shifting': {
            'mechanisms': {**all_mechanisms, 'shifting_cultivation': False}
        },
        'no_fishing': {
            'mechanisms': {**all_mechanisms, 'fishing_enabled': False}
        },
        'no_resources': {
            'mechanisms': {**all_mechanisms, 'resource_discovery': False}
        },
        'no_neighbor_boost': {
            'mechanisms': {**all_mechanisms, 'neighbor_boost_enabled': False}
        },
        'no_climate': {
            'mechanisms': {**all_mechanisms, 'climate_effects': False}
        },
        
        'scarcity': {
            'mechanisms': all_mechanisms.copy(),
            'params_override': {
                'prod_multiplier': 1.5,
                'land_max_capacity': 0.5,
                'fish': 3,
                'max_fish': 5
            }
        },
        'abundance': {
            'mechanisms': all_mechanisms.copy(),
            'params_override': {
                'prod_multiplier': 10,
                'land_max_capacity': 2.0,
                'fish': 20,
                'max_fish': 40
            }
        },
        
        # TEST 3: Extreme scenarios
        'extreme_scarcity': {
            'mechanisms': all_mechanisms.copy(),
            'params_override': {
                'prod_multiplier': 0.5,
                'land_max_capacity': 0.2,
                'fish': 1,
                'max_fish': 2
            }
        },
        'extreme_abundance': {
            'mechanisms': all_mechanisms.copy(),
            'params_override': {
                'prod_multiplier': 15,
                'land_max_capacity': 3.0,
                'fish': 50,
                'max_fish': 100
            }
        }
    }
    
    return experiments

def save_numerical_data(village, data_folder):
    """Save all plot data as CSV files"""
    os.makedirs(data_folder, exist_ok=True)
    
    data_attributes = [
        'population_over_time',
        'land_capacity_over_time',
        'land_capacity_over_time_all',
        'food_storage_over_time',
        'luxury_goods_over_time',
        'average_fertility_over_time',
        'average_age',
        'average_life_span',
        'population_accumulation',
        'gini_coefficients',
        'gini_coefficients_food',
        'gini_coefficients_luxury',
        'emigrate',
        'male',
        'female',
        'new_born',
        'trade_count_over_time',
        'food_traded_over_time',
        'resource_traded_over_time'
    ]
    
    data_dict = {}
    max_length = 0
    
    for key in data_attributes:
        if hasattr(village, key):
            values = getattr(village, key)
            if values and isinstance(values, list):
                data_dict[key] = values
                max_length = max(max_length, len(values))
    
    if max_length > 0:
        combined_csv_path = os.path.join(data_folder, 'simulation_data.csv')
        df = pd.DataFrame({'time_step': list(range(max_length))})
        for key, values in data_dict.items():
            padded = values + [None] * (max_length - len(values))
            df[key] = padded
        df.to_csv(combined_csv_path, index=False)
        print(f"Combined data saved to: {combined_csv_path}")
    
    for key, values in data_dict.items():
        df_plot = pd.DataFrame({
            'time_step': list(range(len(values))),
            key: values
        })
        csv_path = os.path.join(data_folder, f'{key}.csv')
        df_plot.to_csv(csv_path, index=False)



def run_experiments(experiment_names=None, runs_per_experiment=10):
    """
    Run experiments
    - experiment_names: list of experiment names to run, or None for all
    - runs_per_experiment: number of simulation runs per experiment
    """
    
    base_params = load_parameters()
    experiments = get_experiments()
    
    if experiment_names:
        experiments = {k: v for k, v in experiments.items() if k in experiment_names}
    
    results = {}
    
    for exp_name, exp_config in experiments.items():
        print(f"\n{'='*60}")
        print(f"RUNNING EXPERIMENT: {exp_name}")
        print(f"{'='*60}")
        
        exp_results = []
        
        for run in range(runs_per_experiment):
            seed = run + 1
            print(f"  Run {run+1}/{runs_per_experiment} (seed={seed})...")
            
            params = copy.deepcopy(base_params)
            params['mechanisms'] = exp_config['mechanisms']
            
            if 'params_override' in exp_config:
                for key, value in exp_config['params_override'].items():
                    params[key] = value
            
            try:
                result = run_single_simulation(params, seed, exp_name, run+1)
                exp_results.append(result)
                print(f"    Gini: {result['gini']:.4f}, Pop: {result['population']}, Food: {result['food']:.0f}")
                print(f"    Saved to: {result['folder']}")
            except Exception as e:
                print(f"    ERROR: {e}")
                import traceback
                traceback.print_exc()
                continue
        
        results[exp_name] = exp_results
        
        if exp_results:
            ginis = [r['gini'] for r in exp_results]
            print(f"\n  SUMMARY for {exp_name}:")
            print(f"    Mean Gini: {np.mean(ginis):.4f} (+/- {np.std(ginis):.4f})")
            print(f"    Min Gini: {np.min(ginis):.4f}")
            print(f"    Max Gini: {np.max(ginis):.4f}")
    
    return results


def analyze_results(results):
    """Compare experiments to baseline using statistical tests"""
    
    print(f"\n{'='*60}")
    print("STATISTICAL ANALYSIS")
    print(f"{'='*60}")
    
    if 'baseline' not in results or not results['baseline']:
        print("No baseline results to compare!")
        return
    
    baseline_ginis = [r['gini'] for r in results['baseline']]
    baseline_mean = np.mean(baseline_ginis)
    baseline_std = np.std(baseline_ginis)
    
    print(f"\nBASELINE: Mean Gini = {baseline_mean:.4f} (+/- {baseline_std:.4f})")
    print(f"{'Experiment':<25} {'Mean Diff':>12} {'p-value':>12} {'Significant?':>15}")
    print("-" * 65)
    
    summary = []
    
    for exp_name, exp_results in results.items():
        if exp_name == 'baseline' or not exp_results:
            continue
        
        exp_ginis = [r['gini'] for r in exp_results]
        exp_mean = np.mean(exp_ginis)
        diff = exp_mean - baseline_mean
        
        t_stat, p_value = stats.ttest_ind(baseline_ginis, exp_ginis)
        
        pooled_std = np.sqrt((np.std(baseline_ginis)**2 + np.std(exp_ginis)**2) / 2)
        cohens_d = diff / pooled_std if pooled_std > 0 else 0
        
        significant = p_value < 0.05
        
        print(f"{exp_name:<25} {diff:>12.4f} {p_value:>12.4f} {'YES' if significant else 'NO':>15}")
        
        summary.append({
            'experiment': exp_name,
            'mean_gini': exp_mean,
            'diff': diff,
            'p_value': p_value,
            'significant': significant,
            'cohens_d': cohens_d,
            'n_runs': len(exp_results)
        })
    
    return summary



def save_results_to_csv(results, summary, filename="experiment_results.csv"):
    """Save experiment results to CSV"""
    
    detailed_data = []
    for exp_name, exp_results in results.items():
        for i, r in enumerate(exp_results):
            detailed_data.append({
                'experiment': exp_name,
                'run': i + 1,
                'gini': r['gini'],
                'population': r['population'],
                'food': r['food'],
                'num_households': r['num_households']
            })
    
    df_detailed = pd.DataFrame(detailed_data)
    df_detailed.to_csv(f"{filename}_detailed.csv", index=False)
    
    if summary:
        df_summary = pd.DataFrame(summary)
        df_summary.to_csv(f"{filename}_summary.csv", index=False)
    
    print(f"\nResults saved to: {filename}_detailed.csv and {filename}_summary.csv")



def main():

    
    print("="*60)
    print("SIMULATION EXPERIMENT RUNNER")
    print("="*60)
    print("\nTesting which mechanisms affect inequality...")
    
    results = run_experiments(
        experiment_names=None,  # None = run all experiments defined in get_experiments()
        runs_per_experiment=5   # Increase for better statistics
    )
    
    summary = analyze_results(results)
    save_results_to_csv(results, summary)
    
    print("\n" + "="*60)
    print("EXPERIMENTS COMPLETE!")
    print("="*60)
    
    if summary:
        print("\nMECHANISMS THAT SIGNIFICANTLY AFFECT INEQUALITY (p < 0.05):")
        significant = [s for s in summary if s['significant']]
        if significant:
            for s in significant:
                print(f"  - {s['experiment']}: diff={s['diff']:.4f}, p={s['p_value']:.4f}, effect size={s['cohens_d']:.3f}")
        else:
            print("  None found with current runs. Try increasing runs_per_experiment.")
        
        print("\nMECHANISMS THAT DO NOT SIGNIFICANTLY AFFECT INEQUALITY:")
        not_significant = [s for s in summary if not s['significant']]
        for s in not_significant:
            print(f"  - {s['experiment']}: diff={s['diff']:.4f}, p={s['p_value']:.4f}")

if __name__ == "__main__":
    main()