import random
from agent import Agent
from household import Household
from village import Village
from vec import Vec1
import scipy.special as sp
import math
import uuid
import warnings
warnings.filterwarnings("ignore")

# random.seed(10)
def generate_random_agent(household_id, vec1_instance):

    """Generate a random agent with basic attributes."""
    m0 = vec1_instance.mstar * sp.gdtr(1.0 / vec1_instance.fertscale, vec1_instance.fertparm, 1)
    # print('issues', vec1_instance.phi)
    age = random.randint(1, 20)
    gender = random.choice(['male', 'female'])
    fertility = m0[age]
    return Agent(age, gender, household_id, fertility)

def generate_random_household(num_members, location, farmlands, vec1_instance, food_expiration_steps):
    """Generate a random household with a specified number of agents."""
    food_storage = num_members
    luxury_good_storage = 0
    new_household = Household([], location, farmlands, food_storage, luxury_good_storage, food_expiration_steps)
    new_household.members = [generate_random_agent(new_household.id, vec1_instance) for _ in range(num_members)]
    
    return new_household

def generate_random_village(num_households, num_land_cells, vec1_instance, food_expiration_steps, land_recovery_rate, land_max_capacity, initial_quality, fallow_period, luxury_goods_in_village, water_source): #TODO: introduce the water source
    """Generate a village with a specified number of households and land cells."""
    grid_size = math.ceil(math.sqrt(num_land_cells))
    land_types = {}
    for i in range(num_land_cells):
        location = (i // grid_size, i % grid_size)
        land_types[location] = {
            'quality': initial_quality,
            'water_source':water_source,
            'occupied': False, # 'house' or 'farm' or None
            'owner': None, # which family owns this pixel of land. 
            'max_capacity': land_max_capacity,
            'recovery_rate': land_recovery_rate,
            'fallow': False,      
            'fallow_timer': 0,
            # 'fishing': random.random() < fish_chance  # 30% chance of being True
            'farming_intensity': 0,
            'farming_counter': 0
        }

    households = []

    new_village = Village(households, land_types, food_expiration_steps, fallow_period, luxury_goods_in_village)
    new_village.population_accumulation.append(0)

    for i in range(num_households):
        location = random.choice(list(land_types.keys()))
        farmlands = allocate_household_land(location,  land_types, weights=None, num_farm_pixels = 100)
        while land_types[location]['occupied']:
            location = random.choice(list(land_types.keys()))
        land_types[location]['occupied'] = True
        household = generate_random_household(# next(Household._id_iter),
            random.randint(0, 5), location, farmlands, vec1_instance, food_expiration_steps)
        households.append(household)
        new_village.population_accumulation[0] += len(household.members)
    
    new_village.land_types = land_types
    new_village.households = households

    return new_village


def print_village_summary(village):
    """Print a summary of the village, including details of each household."""
    print(f"Village has {len(village.households)} households.")
    
    for household in village.households:
        land = village.land_types[household.location]
        land_quality = land['quality']
        print(f"Household ID: {household.id}, Location: {household.location}, Land Quality: {land_quality}")
        food = sum(amount for amount, _ in household.food_storage)
        need = sum(member.vec1_instance.rho[member.get_age_group_index()] for member in household.members)
        print(f"  Food Storage: {food}, Luxury Good Storage: {household.luxury_good_storage}, Needs: {need}")
        print(f"Household ID: {household.members}, Location: {household.location}, Land Quality: {household.land_quality}")
        
        if household.members:
            print(f"  Members:")
            for member in household.members:

                print(f"    Agent - Age: {member.age}, Gender: {member.gender}, Alive: {member.is_alive}, Fertility Prob: {member.fertility}， Marital Status: {member.marital_status}")
                pass
        else:
            print(f"  No members in this household.")



def land_score(cell, home_location, allocated_cells=None, weights=None):
    """
    Compute a score for a land pixel for allocation to a household.
    allocated_cells: list of already allocated land pixels for this household
    """
    if weights is None:
        weights = {
            'distance_home': 1.0,   # distance to home
            'distance_cluster': 2.0,  # distance to existing allocated pixels
            'quality': 2.0,
            'water': 2.0,
            'max_capacity': 1.0,
            'recovery_rate': 1.0
        }
    
    # distance to home
    distance_home = math.sqrt((cell['location'][0]-home_location[0])**2 + (cell['location'][1]-home_location[1])**2)
    distance_home_score = 1 / (1 + distance_home)

    # distance to existing allocated pixels (cluster factor)
    if allocated_cells:
        distances = [math.sqrt((cell['location'][0]-loc[0])**2 + (cell['location'][1]-loc[1])**2) 
                     for loc in allocated_cells]
        min_distance = min(distances)
        distance_cluster_score = 1 / (1 + min_distance)
    else:
        distance_cluster_score = 0  # no cluster yet

    # resource factors
    water_score = 1 if cell['water_source'] else 0
    quality_score = cell['quality']
    max_cap_score = cell['max_capacity']
    recovery_score = cell['recovery_rate']

    # weighted sum
    score = (weights['distance_home'] * distance_home_score +
             weights['distance_cluster'] * distance_cluster_score +
             weights['quality'] * quality_score +
             weights['water'] * water_score +
             weights['max_capacity'] * max_cap_score +
             weights['recovery_rate'] * recovery_score)
    
    return score

def allocate_household_land(home_location, num_farm_pixels, land_types, weights=None):
    """
    allocate farm pixels to a household such that pixels are clustered together.
    """
    free_land = [(loc, cell) for loc, cell in land_types.items() if cell['occupied'] is None]
    
    for loc, cell in free_land:
        cell['location'] = loc
    
    allocated = []

    for _ in range(num_farm_pixels):
        # score each free pixel based on current allocated cells
        scored_land = [(loc, land_score(cell, home_location, allocated, weights)) 
                       for loc, cell in free_land]
        if not scored_land:
            break  # no more free land
        # pick highest scored pixel
        scored_land.sort(key=lambda x: x[1], reverse=True)
        best_loc, _ = scored_land[0]
        allocated.append(best_loc)
        
        # mark it occupied
        land_types[best_loc]['occupied'] = 'farm'
        land_types[best_loc]['owner'] = home_location
        
        # remove from free land
        free_land = [(loc, cell) for loc, cell in free_land if loc != best_loc]
    
    return allocated