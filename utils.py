import random
from agent import Agent
from household import Household
from village import Village
from agent import Vec1
import scipy.special as sp
import math
import uuid
random.seed(10)
def generate_random_agent(household_id, vec1):

    """Generate a random agent with basic attributes."""
    m0 = vec1.mstar * sp.gdtr(1.0 / vec1.fertscale, vec1.fertparm, 1)
    age = random.randint(1, 20)
    gender = random.choice(['male', 'female'])
    fertility = m0[age]
    return Agent(age, gender, household_id, vec1, fertility)

def generate_random_household(num_members, location, vec1):
    """Generate a random household with a specified number of agents."""
    food_storage = num_members
    luxury_good_storage = 0
    new_household = Household([], location, food_storage, luxury_good_storage)
    new_household.members = [generate_random_agent(new_household.id, vec1) for _ in range(num_members)]
    
    return new_household

def generate_random_village(num_households, num_land_cells, vec1):
    """Generate a village with a specified number of households and land cells."""
    grid_size = math.ceil(math.sqrt(num_land_cells))
    land_types = {}
    for i in range(num_land_cells):
        location = (i // grid_size, i % grid_size)
        land_types[location] = {
            'quality': 5,
            'occupied': False,
            'max_capacity': 10,
            'recovery_rate': 0.03,
            'fallow': False,      
            'fallow_timer': 0,
            'fishing': random.random() < 0.3  # 30% chance of being True
        }

    households = []
    for i in range(num_households):
        location = random.choice(list(land_types.keys()))
        while land_types[location]['occupied']:
            location = random.choice(list(land_types.keys()))
        land_types[location]['occupied'] = True
        household = generate_random_household(# next(Household._id_iter),
            random.randint(5, 10), location, vec1)
        households.append(household)

    return Village(households, land_types)

def print_village_summary(village):
    """Print a summary of the village, including details of each household."""
    print(f"Village has {len(village.households)} households.")
    
    for household in village.households:
        land = village.land_types[household.location]
        land_quality = land['quality']
        print(f"Household ID: {household.id}, Location: {household.location}, Land Quality: {land_quality}")
        food = sum(amount for amount, _ in household.food_storage)
        need = sum(member.vec1.rho[member.get_age_group_index()] for member in household.members)
        print(f"  Food Storage: {food}, Luxury Good Storage: {household.luxury_good_storage}, Needs: {need}")
        # print(f"Household ID: {household.members}, Location: {household.location}, Land Quality: {household.land_quality}")
        
        if household.members:
            print(f"  Members:")
            for member in household.members:

                print(f"    Agent - Age: {member.age}, Gender: {member.gender}, Alive: {member.is_alive}, Fertility Prob: {member.fertility}， Marital Status: {member.marital_status}")
        else:
            print(f"  No members in this household.")



