from household import Household
from village import Village
from agent import Agent
from agent import Vec1
import pandas as pd
import utils
vec1 = pd.read_csv('demog_vectors.csv')

def test_household_and_agents():
    vec1 = Vec1()
    agents = [Agent(age=30, gender='F', calories_needed=2000, proteins_needed=50, water_needed=2, household_id=1, vec1=vec1)]
    household = Household(id=1, members=agents, location='Original Location', food_storage=100, luxury_good_storage=10, land_quality=0.8, land_max_capacity=1.0, land_recovery_rate=0.02)
    print("Initial Household members:", [agent.household_id for agent in household.members])
    new_agent = Agent(age=25, gender='M', calories_needed=2500, proteins_needed=70, water_needed=2.5, household_id=1, vec1=vec1)
    household.extend(new_agent)
    print("Household members after adding new agent:", [agent.household_id for agent in household.members])
    household.remove_member(agents[0])
    print("Household members after removing an agent:", [agent.household_id for agent in household.members])
test_household_and_agents()