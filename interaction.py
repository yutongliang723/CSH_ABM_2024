from flask import Flask, request, jsonify, render_template
import random
import matplotlib
matplotlib.use('Agg')  # Use non-GUI backend for matplotlib (suitable for Flask and headless environments)
import matplotlib.pyplot as plt
from household import Household
from village import Village
from agent import Agent
from agent import Vec1
import pandas as pd
import utils
import math


app = Flask(__name__)

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/run_simulation', methods=['POST'])

@app.route('/run_simulation', methods=['POST'])

def run_simulation():
    # Check for all required parameters in the JSON request
    data = request.json
    required_params = ["num_house", "year", "land_cells", "prod_multiplier", "fishing_discount", "spare_food_enabled", "fallow_farming"]

    for param in required_params:
        if param not in data:
            return jsonify({"error": f"Missing required parameter: {param}"}), 400

    try:
        num_house = int(data["num_house"])
        year = int(data["year"])
        land_cells = int(data["land_cells"])
        prod_multiplier = float(data["prod_multiplier"])
        fishing_discount = float(data["fishing_discount"])
        spare_food_enabled = data["spare_food_enabled"] == "true"
        fallow_farming = data["fallow_farming"] == "true"
    except (ValueError, TypeError) as e:
        return jsonify({"error": f"Invalid data type in parameters: {e}"}), 400

    # Initialize the simulation environment
    vec1_instance = utils.Vec1()
    village = utils.generate_random_village(num_house, land_cells, vec1_instance)
    village.initialize_network()
    village.initialize_network_relationship()
    
    # Run the simulation over the specified years
    for _ in range(year):
        village.run_simulation_step(
            vec1_instance,
            prod_multiplier=prod_multiplier,
            fishing_discount=fishing_discount,
            spare_food_enabled=spare_food_enabled,
            fallow_farming=fallow_farming
        )

    # Generate animation and save plots
    village.generate_animation(grid_dim=int(math.sqrt(land_cells)))
    animation_gif_path = f"static/village_simulation.gif"  # Path for animation GIF
    results_image_path = f"static/simulation_results.png"    # Path for main results plot
    gini_image_path = f"static/gini_overtime.png"            # Path for Gini plot

    # Save the plots and animation
    village.plot_simulation_results(file_name=results_image_path)

    return jsonify({
        "image_url": results_image_path,
        "animation_url": animation_gif_path,
        "gini_url": gini_image_path
    })

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5001)