import random
import scipy.special as sp
import pandas as pd
import household
import itertools



class Agent:
    _id_iter = itertools.count(start = 1)
    def __init__(self, age, gender, household_id, fertility, productivity):
        self.id = next(Agent._id_iter)
        self.age = age
        self.gender = gender
        self.household_id = household_id
        self.is_alive = True  
        self.newborn_agents = []
        self.fertility = fertility
        self.marital_status = 'single'
        self.partner_id = None
        self.productivity = productivity

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
        judge = -1

        failures = village.failure_baby.setdefault(village.clock, {})

        # gender check
        if conditions.get("check_gender", False) and self.gender != "female":
            failures["gender"] = failures.get("gender", 0) + 1
            judge += 1

        # marital status check
        elif conditions.get("check_marital_status", False) and self.marital_status != "married":
            failures["marriage"] = failures.get("marriage", 0) + 1
            judge += 1

        # fertility probability
        elif conditions.get("use_fertility", False) and random.random() >= fertility_probability:
            failures["fertility"] = failures.get("fertility", 0) + 1
            judge += 1

        # land availability
        elif conditions.get("check_land", False) and not village.is_land_available():
            failures["land"] = failures.get("land", 0) + 1
            judge += 1

        # household size
        elif conditions.get("exceed_member", False) and len(household.members) + len(self.newborn_agents) >= max_member:
            failures["household"] = failures.get("household", 0) + 1
            judge += 1

        if judge == -1:
            self.reproduce() # only reproduce if no failures
        
    def reproduce(self):
        """Simulate reproduction by adding new agents to the household."""
        new_agent = Agent(
        age = 0, 
        gender=random.choice(['male', 'female']),  
        household_id=self.household_id,
        fertility = 0, 
        productivity=0
        )
        # print(f"Newborn Agent added to Household {self.household_id}.")
        self.newborn_agents.append(new_agent)
    
    def marry(self, partner):
        """Marry another agent."""
        self.marital_status = 'married'
        self.partner_id = partner.id
        partner.marital_status = 'married'
        partner.partner_id = self.id