from flask import Flask, request, jsonify, render_template, send_from_directory
import random
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import pandas as pd
import threading
import math
import os
import json
import time
import shutil
from demog_scale import demog_scale
from vec import Vec1
from village import Village
import utils

app = Flask(__name__)
progress_percent = 0
RESULTS_FOLDER = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'run_results', 'website')
os.makedirs(RESULTS_FOLDER, exist_ok=True)

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/run_results/website/<path:filename>')
def serve_results(filename):
    return send_from_directory(RESULTS_FOLDER, filename)

@app.route("/progress")
def get_progress():
    global progress_percent
    return jsonify({"percent": progress_percent})

@app.route('/run_simulation', methods=['POST'])
def run_simulation():
    global progress_percent
    progress_percent = 0  # reset at start

    data = request.json
    required_params = [
        "num_house", "year", "land_cells",
        "spare_food_enabled", "fallow_farming", "emigrate_enabled",
        "land_recovery_rate", "food_expiration_steps", "trading_enabled"
    ]

    for param in required_params:
        if param not in data:
            return jsonify({"error": f"Missing required parameter: {param}"}), 400

    try:
        params = {
            "num_house": int(data["num_house"]),
            "year": int(data["year"]),
            "land_cells": int(data["land_cells"]),
            "prod_multiplier": 1.0,
            "fishing_discount": 0.0,
            "spare_food_enabled": data["spare_food_enabled"] == "true",
            "fallow_farming": data["fallow_farming"] == "true",
            "emigrate_enabled": data["emigrate_enabled"] == "true",
            "trading_enabled": data["trading_enabled"] == "true",
            "land_recovery_rate": float(data["land_recovery_rate"]),
            "food_expiration_steps": int(data["food_expiration_steps"]),
            "land_depreciate_factor": float(data["land_depreciate_factor"]),
            "max_member": int(data["max_member"]),
            "fallow_period": 2,
            "marriage_from": 14,
            "marriage_to": 60,
            "bride_price_ratio": 0.4,
            "bride_price": 1,
            "land_max_capacity": 20,
            "initial_quality": 5,
            "exchange_rate": 3,
            "luxury_good_storage": 0,
            "storage_ratio_low": 0.2,
            "storage_ratio_high": 1.5,
            "land_capacity_low": 1,
            "excess_food_ratio": 1.5,
            "trade_back_start": 20,
            "lux_per_year": 15,
            "fertility_scaler": 2,
            "work_scale": 5,
            "luxury_goods_in_village": 0,
            "demog_file": "demog_vectors_scaled.csv",
            "prob_emigrate": 0.2,
            "farming_counter_max": 10,
            "conditions": {
                "use_fertility": True,
                "check_gender": True,
                "check_marital_status": True,
                "check_land": False,
                "exceed_member": True
            }
        }

    except (ValueError, TypeError) as e:
        return jsonify({"error": f"Invalid parameter: {e}"}), 400

    timestamp = str(int(time.time()))
    temp_folder = os.path.join(RESULTS_FOLDER, timestamp)
    os.makedirs(temp_folder, exist_ok=True)

    # Launch simulation in background
    thread = threading.Thread(target=run_simulation_task, args=(params, temp_folder, timestamp))
    thread.start()

    return jsonify({"status": "started", "folder": timestamp})

def run_simulation_task(params, temp_folder, timestamp):
    global progress_percent

    results_png = os.path.join(temp_folder, "results.svg")
    results_second_png = os.path.join(temp_folder, "results_second.svg")
    results_csv = os.path.join(temp_folder, "simulation_results.csv")
    animation_gif = os.path.join(temp_folder, "simulation.gif")

    with open(os.path.join(temp_folder, "parameters.json"), "w") as f:
        json.dump(params, f, indent=4)

    demog_scale()
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

    village.initialize_network()
    village.initialize_network_relationship()

    for i in range(params["year"]):
        village.run_simulation_step(
            vec1_instance=vec1_instance,
            prod_multiplier=params["prod_multiplier"],
            fishing_discount=params["fishing_discount"],
            fallow_period=params["fallow_period"],
            food_expiration_steps=params["food_expiration_steps"],
            marriage_from=params["marriage_from"],
            marriage_to=params["marriage_to"],
            bride_price_ratio=params["bride_price_ratio"],
            bride_price=params["bride_price"],
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
            conditions=params["conditions"],
            prob_emigrate=params["prob_emigrate"],
            emigrate_enabled=params["emigrate_enabled"],
            spare_food_enabled=params["spare_food_enabled"],
            fallow_farming=params["fallow_farming"],
            trading_enabled=params["trading_enabled"],
            farming_counter_max=params["farming_counter_max"]
        )

        progress_percent = int((i + 1) / params["year"] * 100)

    village.plot_simulation_results(results_png, results_csv, vec1_instance)
    village.plot_simulation_results_second(results_second_png)
    village.generate_animation(animation_gif, grid_dim=math.ceil(math.sqrt(params['land_cells'])))

    # Save results to a known "latest" location for retrieval
    latest_folder = os.path.join(RESULTS_FOLDER, "latest")
    if os.path.exists(latest_folder):
        shutil.rmtree(latest_folder)
    shutil.copytree(temp_folder, latest_folder)

    # Cleanup old
    all_runs = sorted([d for d in os.listdir(RESULTS_FOLDER) if os.path.isdir(os.path.join(RESULTS_FOLDER, d)) and d != "latest"], reverse=True)
    for old_run in all_runs[5:]:
        shutil.rmtree(os.path.join(RESULTS_FOLDER, old_run))

    progress_percent = 100

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5001)