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

    def get_age_group_index(self, vec1_instance):
        """Determine the age group index for the agent."""
        
        if self.age >= len(vec1_instance.phi):
            return len(vec1_instance.phi) - 1
        return self.age

    def work(self, vec1_instance, work_scale):
        """Simulate work done by the agent based on effectiveness parameter."""
        work_output = 0
        # if self.is_alive:
        if 1 ==1:
            age_index = self.get_age_group_index(vec1_instance)
            phi = vec1_instance.phi[age_index]
            work_output = phi * work_scale
            return work_output
    
    def age_survive_reproduce(self, household, village, z, max_member, fertility_scaler, vec1_instance, conditions):

        """Simulate aging, survival, and reproduction based on probabilities."""
        
        if not self.is_alive:
            return
        
        self.age += 1

        age_index = self.get_age_group_index(vec1_instance)
        # z = 1
        survival_probability = vec1_instance.pstar[age_index] * sp.gdtr(1.0 / vec1_instance.mortscale, vec1_instance.mortparms[age_index], z)
        fertility_probability = vec1_instance.mstar[age_index]* sp.gdtr(1.0 / vec1_instance.fertscale, vec1_instance.fertparm, z) * fertility_scaler
        
        if random.random() > survival_probability:
            self.is_alive = False # need this
            partner = village.get_agent_by_id(self.partner_id)
            if partner:
                partner.marital_status = 'single'
            return
        
        self.fertility = fertility_probability
        # print(village.land_types.values())
        # if random.random() < fertility_probability and self.gender == 'female' and self.marital_status == 'married' and village.is_land_available() is True:
        # if random.random() < fertility_probability and self.gender == 'female':
        judge = -1
        

        if not conditions["use_fertility"] or random.random() < fertility_probability:
            pass
        else:
            village.failure_baby[village.time]["fertility"] = village.failure_baby[village.time].get("fertility", 0) + 1
            judge += 1

        if not conditions["check_gender"] or self.gender == "female":
            pass
        else:
            village.failure_baby[village.time]["gender"] = village.failure_baby[village.time].get("gender", 0) + 1
            judge += 1

        if not conditions["check_marital_status"] or self.marital_status == "married":
            pass
        else:
            village.failure_baby[village.time]["marriage"] = village.failure_baby[village.time].get("marriage", 0) + 1
            judge += 1

        if not conditions["check_land"] or village.is_land_available():
            pass
        else:
            village.failure_baby[village.time]["land"] = village.failure_baby[village.time].get("land", 0) + 1
            judge += 1

        if not conditions["exceed_member"] or len(household.members) + len(self.newborn_agents) < max_member:
            pass
        else:
            village.failure_baby[village.time]["household"] = village.failure_baby[village.time].get("household", 0) + 1
            judge += 1

        if judge == -1:
            self.reproduce()  # only reproduce if no failures
            
            # if len(household.members) + len(self.newborn_agents) < max_member: 
                
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


