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

class Land:
    def __init__(self, index, max_capacity, recovery_rate, grid_size):
        self.location = (index // grid_size, index % grid_size)
        self.water = self._generate_water(grid_size)
        self.soil = self._generate_soil()
        self.max_capacity = max_capacity
        self.recovery_rate = recovery_rate
        self.fallow = False
        self.farming_intensity = 0
        self.farming_counter = 0
        self.owner = None
        self.occupied = None
        self.has_stone = random.random() < 1 #TODO: later make it the parameter
        self.has_obsidian = random.random() < 0.5
        self.has_jade = random.random() < 0.3

    def _generate_water(self, grid_size):
        x, y = self.location
        base = max(0, 1 - (y / grid_size))  # top-dry, bottom-wet
        noise = random.uniform(-0.1, 0.1)
        return max(0, min(1, base + noise))  # clamp between 0–1
    
    def _generate_soil(self):
        base = 0.5 + 0.3 * self.water  # wetter land = more fertile
        noise = random.uniform(-0.1, 0.1)
        return max(0, min(1, base + noise))
    