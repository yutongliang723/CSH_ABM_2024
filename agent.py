import random
import scipy.special as sp
import pandas as pd
# from household import Household
import household
import itertools

vec1 = pd.read_csv('demog_vectors.csv')
vec1 = vec1.rename_axis('age').reset_index()
new_max_age = 60
old_max_age = vec1['age'].max()
scale_factor = new_max_age / old_max_age
scale_factor = 1
other_para = ['rho', 'pstar', 'mortparms']
bins = pd.cut(vec1['age'], bins=new_max_age)
binned_vec = pd.DataFrame()
for col in other_para:
    binned_col = vec1.groupby(bins).agg({col: 'mean'}).reset_index()
    binned_col[col] = binned_col[col] * scale_factor
    binned_vec[col] = binned_col[col]
    
bin_centers = [interval.mid for interval in binned_col['age']]
binned_vec = binned_vec.rename_axis('age_new').reset_index()
binned_vec['mstar'] = vec1['mstar']
binned_vec['mortparms'] = vec1['mortparms']
binned_vec['fertparm'] = vec1['fertparm']
binned_vec['mortscale'] = vec1['mortscale']
binned_vec['fertscale'] = vec1['fertscale']
binned_vec['phi'] = vec1['phi']


vec1 = binned_vec

rho_scaled = vec1.rho
pstar_scaled = vec1.pstar
mstar_scaled = vec1.mstar
mortparms_scaled = vec1.mortparms
fertparm_scaled = vec1.fertparm
neolithic_mortscale = vec1.mortscale[0]
neolithic_fertscale = vec1.fertscale[0]

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
    _id_iter = itertools.count(start = 1)
    def __init__(self, age, gender, household_id, vec1, fertility):
        self.id = next(Agent._id_iter)
        self.age = age
        self.gender = gender
        self.household_id = household_id
        self.vec1 = vec1  
        self.is_alive = True  
        self.newborn_agents = []
        self.fertility = fertility
        self.marital_status = 'single'
        self.partner_id = None

    def get_age_group_index(self):
        """Determine the age group index for the agent."""
        
        if self.age >= len(self.vec1.phi):
            return len(self.vec1.phi) - 1
        return self.age

    def work(self):
        """Simulate work done by the agent based on effectiveness parameter."""
        work_output = 0
        if self.is_alive:
            age_index = self.get_age_group_index()
            phi = self.vec1.phi[age_index]
            work_output = phi * 6
            return work_output
        return work_output
    
    def age_and_die(self, household, village, z):

        """Simulate aging, survival, and reproduction based on probabilities."""
        if not self.is_alive:
            return
        
        self.age += 1

        age_index = self.get_age_group_index()
        
        survival_probability = self.vec1.pstar[age_index] * sp.gdtr(1.0 / self.vec1.mortscale, self.vec1.mortparms[age_index], z)
        fertility_probability = self.vec1.mstar[age_index] * sp.gdtr(1.0 / self.vec1.fertscale, self.vec1.fertparm, z) * 5
        
        if random.random() > survival_probability:
            self.is_alive = False
            partner = village.get_agent_by_id(self.partner_id)
            if partner:
                partner.marital_status = 'single'
            return
        
        self.fertility = fertility_probability
        if random.random() < fertility_probability and self.gender == 'female' and self.marital_status == 'married':
            if len(household.members) + len(self.newborn_agents) < 20: # or village.is_land_available():
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
        print(f"Newborn Agent added to Household {self.household_id}.")
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


