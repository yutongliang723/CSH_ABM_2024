import random
import scipy.special as sp
import pandas as pd
import household
import itertools



class Agent:
    _id_iter = itertools.count(start = 1)
    def __init__(self, age, gender, household_id, fertility):
        self.id = next(Agent._id_iter)
        self.age = age
        self.gender = gender
        self.household_id = household_id
        self.is_alive = True  
        self.newborn_agents = []
        self.fertility = fertility
        self.marital_status = 'single'
        self.partner_id = None

    def get_age_group_index(self, vec1):
        """Determine the age group index for the agent."""
        
        if self.age >= len(vec1.phi):
            return len(vec1.phi) - 1
        return self.age

    def work(self, vec1, work_scale):
        """Simulate work done by the agent based on effectiveness parameter."""
        work_output = 0
        if self.is_alive:
        # if 1 ==1:
            age_index = self.get_age_group_index(vec1)
            phi = vec1.phi[age_index]
            work_output = phi * work_scale
            return work_output
    
    def age_survive_reproduce(self, household, village, z, max_member, fertility_scaler, vec1):

        """Simulate aging, survival, and reproduction based on probabilities."""
        if not self.is_alive:
            return
        
        self.age += 1

        age_index = self.get_age_group_index(vec1)
        
        survival_probability = vec1.pstar[age_index] * sp.gdtr(1.0 / vec1.mortscale, vec1.mortparms[age_index], z)
        fertility_probability = vec1.mstar[age_index] * sp.gdtr(1.0 / vec1.fertscale, vec1.fertparm, z) * fertility_scaler
        
        if random.random() > survival_probability:
            self.is_alive = False # need this
            partner = village.get_agent_by_id(self.partner_id)
            if partner:
                partner.marital_status = 'single'
            return
        
        self.fertility = fertility_probability
        # print(village.land_types.values())
        if random.random() < fertility_probability and self.gender == 'female' and self.marital_status == 'married' and village.is_land_available() is True:
        # TODO: think about to make it less constrains
        
            if len(household.members) + len(self.newborn_agents) < max_member: 
                self.reproduce()
                # print('reproduced')
                # print('village.is_land_available()', village.is_land_available())
    
    def reproduce(self):
        """Simulate reproduction by adding new agents to the household."""
        new_agent = Agent(
        age = 0, 
        gender=random.choice(['male', 'female']),  
        household_id=self.household_id,
        fertility = 0
        )
        # print(f"Newborn Agent added to Household {self.household_id}.")
        self.newborn_agents.append(new_agent)
    
    def marry(self, partner):
        """Marry another agent."""
        self.marital_status = 'married'
        self.partner_id = partner.id
        partner.marital_status = 'married'
        partner.partner_id = self.id

    def bride_price_need(self):
        agent_house = household.get_household_by_id(self.household_id)
        agent_house_num = len(agent_house.members)


