import unittest
import os
import sys
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'app')))
from vec import Vec1
from village import Village
from utils import generate_random_village

class TestVillageGeneration(unittest.TestCase):
    def test_generate_random_village(self):
        params = {
            "num_house": 10,
            "land_cells": 50,
            "year": 10,
            "food_expiration_steps": 5,
            "land_recovery_rate": 0.05,
            "land_max_capacity": 10,
            "initial_quality": 5,
            "fallow_period": 2,
            "luxury_goods_in_village": 0,
            "fertility_scaler": 2,
            "demog_file": "demog_vectors_scaled.csv"
        }
        vec1_instance = Vec1(params)

        village = generate_random_village(
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

        self.assertEqual(len(village.households), 10)

if __name__ == '__main__':
    unittest.main()