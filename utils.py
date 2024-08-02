import random
from agent import Agent
from household import Household
from village import Village

def generate_random_agent(household_id, vec1):
    """Generate a random agent with basic attributes."""
    age = random.randint(1, 80)
    gender = random.choice(['male', 'female'])
    # calories_needed = random.randint(1500, 3000)
    # proteins_needed = random.randint(50, 150)
    # water_needed = random.randint(2000, 4000)
    return Agent(age, gender, household_id, vec1)

def generate_random_household(id, num_members, location, vec1):
    """Generate a random household with a specified number of agents."""
    members = [generate_random_agent(id, vec1) for _ in range(num_members)]
    food_storage = random.randint(100, 1000)
    luxury_good_storage = random.randint(0, 500)
    
    land_quality = random.uniform(0.0, 1.0)  
    land_max_capacity = random.uniform(0.5, 1.5)  
    land_recovery_rate = random.uniform(0.01, 0.1)  

    return Household(id, members, location, food_storage, luxury_good_storage, land_quality, land_max_capacity, land_recovery_rate)
def generate_random_village(num_households, vec1):
    '''Generate a village with a specified number of households.'''
    households = [generate_random_household(i, random.randint(1, 6), f'Location {i}', vec1) for i in range(num_households)]
    network = {}  # not implemented yet
    land_types = ['forest', 'plain', 'mountain']
    return Village(households, network, land_types)

def print_village_summary(village):
    """Print a summary of the village, including details of each household."""
    print(f"Village has {len(village.households)} households.")
    
    for household in village.households:
        print(f"Household ID: {household.id}, Location: {household.location}, Land Quality: {household.land_quality}")
        print(f"  Food Storage: {household.food_storage}, Luxury Good Storage: {household.luxury_good_storage}")
        # print(f"Household ID: {household.members}, Location: {household.location}, Land Quality: {household.land_quality}")
        
        if household.members:
            print(f"  Members:")
            for member in household.members:
                print(f"    Agent - Age: {member.age}, Gender: {member.gender}, Alive: {member.is_alive}")
        else:
            print(f"  No members in this household.")