import random
import scipy.special as sp
import pandas as pd
# from household import Household
import household
vec1 = pd.read_csv('demog_vectors.csv')

class Vec1:
    def __init__(self):
        self.phi = vec1.phi
        self.rho = vec1.rho
        self.pstar = vec1.pstar
        self.mstar = vec1.mstar
        self.mortscale = vec1.mortscale[0]
        self.mortparms = vec1.mortparms
        self.fertparm = vec1.fertparm[0]
        self.fertscale = vec1.fertscale[0]
        

class Agent:
    def __init__(self, age, gender, household_id, vec1, fertility):
        self.age = age
        self.gender = gender
        self.household_id = household_id
        self.vec1 = vec1  
        self.is_alive = True  
        self.newborn_agents = []
        self.fertility = fertility

    def get_age_group_index(self):
        """Determine the age group index for the agent."""
        
        if self.age >= len(self.vec1.phi):
            return len(self.vec1.phi) - 1
        return self.age

    def consume_resources(self):
        """Simulate resource consumption based on effectiveness and consumption parameters."""
        if self.is_alive:
            age_index = self.get_age_group_index()
            phi = self.vec1.phi[age_index]
            rho = self.vec1.rho[age_index]
            # consumption_amount = phi * (self.calories_needed + self.proteins_needed + self.water_needed) * rho
            consumption_amount = rho * 10
            # print(f"Agent {self.household_id} consumes {consumption_amount:.2f} units of resources.")

    def work(self):
        """Simulate work done by the agent based on effectiveness parameter."""
        work_output = 0
        if self.is_alive:
            age_index = self.get_age_group_index()
            phi = self.vec1.phi[age_index]
            # work_output = phi * (self.calories_needed + self.proteins_needed)  # Example calculation
            work_output = phi 
            # print(f"Agent {self.household_id} works and produces {work_output:.2f} units of output.")
            return work_output
        return work_output

    def age_and_die(self):
        from household import Household
        """Simulate aging, survival, and reproduction based on probabilities."""
        if not self.is_alive:
            return
        # avg_food_storage = household.food_storage / len(household.members)
        # # print(avg_food_storage)
        self.age += 1
        p0 = self.vec1.pstar * sp.gdtr(1.0 / self.vec1.mortscale, self.vec1.mortparms, 1)
        m0 = self.vec1.mstar * sp.gdtr(1.0 / self.vec1.fertscale, self.vec1.fertparm, 1)
        
        age_index = self.get_age_group_index()
        survival_probability = p0[age_index]  # survival probability
        # # print(age_index, survival_probability)
        if random.random() > survival_probability:
            self.is_alive = False
            # print(f"Agent {self.household_id} has died at age {self.age}.")
            # household = self.get_household()
            # if household:
            #     household.remove_member(self)
            return
        
        fertility_probability = m0[age_index]
        self.fertility = fertility_probability
        if random.random() < fertility_probability and self.gender == 'female':
            # print(f"Agent {self.household_id} reproduces at age {self.age}.")
            self.reproduce()

    def reproduce(self):
        """Simulate reproduction by adding new agents to the household."""
        new_agent = Agent(
        age = 0, 
        gender=random.choice(['male', 'female']),  
        household_id=self.household_id,
        vec1=self.vec1,
        fertility = 0
        )
        # print(f"Newborn Agent added to Household {self.household_id}.")
        self.newborn_agents.append(new_agent)
    
