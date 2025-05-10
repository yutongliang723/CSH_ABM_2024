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

def generate_random_household(num_members, location, vec1_instance, food_expiration_steps):
    """Generate a random household with a specified number of agents."""
    food_storage = num_members
    luxury_good_storage = 0
    new_household = Household([], location, food_storage, luxury_good_storage, food_expiration_steps)
    new_household.members = [generate_random_agent(new_household.id, vec1_instance) for _ in range(num_members)]
    
    return new_household

def generate_random_village(num_households, num_land_cells, vec1_instance, food_expiration_steps, land_recovery_rate, land_max_capacity, initial_quality, fallow_period, luxury_goods_in_village):
    """Generate a village with a specified number of households and land cells."""
    grid_size = math.ceil(math.sqrt(num_land_cells))
    land_types = {}
    for i in range(num_land_cells):
        location = (i // grid_size, i % grid_size)
        land_types[location] = {
            'quality': initial_quality,
            'occupied': False,
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
        while land_types[location]['occupied']:
            location = random.choice(list(land_types.keys()))
        land_types[location]['occupied'] = True
        household = generate_random_household(# next(Household._id_iter),
            random.randint(0, 5), location, vec1_instance, food_expiration_steps)
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



