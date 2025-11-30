import random
from agent import Agent
import itertools
from collections import defaultdict

# from main import idh_count
# import utils

class Household:
    _id_iter = itertools.count(start = 1)
    def __init__(self, members, location, home, farmlands, food_storage, luxury_good_storage,food_expiration_steps):
        self.id = next(Household._id_iter)
        self.members = members
        self.location = location  # home location
        self.home = home
        self.food_storage = []
        self.food_storage_timestamps = []
        self.luxury_good_storage = luxury_good_storage
        self.current_step = 0
        self.food_expiration_steps = food_expiration_steps
        self.farmlands = []
        self.prestige = 0
        self.resources = {"stone":0,
                          "obsidian": 0,
                          "jade":0}
        self.farmers = []
        self.tech_labors = []
        self.productivity = 0
        self.parents = []
        self.spouses = []

    def clean_up(self):
        self.members.clear()  
        self.location = None
    
    def add_food(self, amount):
        """Add food with the current step count."""
        self.food_storage.append((amount, self.current_step))
    
    def update_food_storage(self):
        """Remove expired food from storage based on the current step."""
        self.food_storage = [(amount, age_added) for amount, age_added in self.food_storage
                             if self.current_step - age_added < self.food_expiration_steps]

    def deduct_food(household, amount_due):
        while amount_due > 0 and household.food_storage:
            amount, age_added = household.food_storage[0]
            if amount > amount_due:
                household.food_storage[0] = (amount - amount_due, age_added)
                amount_due = 0
            else:
                household.food_storage.pop(0)
                amount_due -= amount

    def advance_step(self):
        """Advance the step count for food expiration date."""
        self.current_step += 1

    def get_land_quality(self, village):
        return village.land_by_id[self.location].soil
    

    def get_land_max_capacity(self, village):
        return village.land_by_id[self.id].max_capacity
    

    def produce_food(self, village, vec1, prod_multiplier, fishing_discount, work_scale, climate, total_food_needed_standard):
        
        village.farms_by_owner = defaultdict(list)
        for land in village.land_by_id.values():   # or village.lands
            if land.occupied == "farm" and land.owner == self.id:
                village.farms_by_owner[land.owner].append(land)
        farm_cells = village.farms_by_owner[self.id] 

        if not farm_cells:
            return  # no farm lands for this household
        self.farmers = []
        self.tech_labors = []
        labor_accum = 0
        for agent in sorted(self.members, key=lambda x: x.productivity, reverse=True):
            if labor_accum < total_food_needed_standard:
                self.farmers.append(agent)
                labor_accum += agent.work(vec1, work_scale)
            else:
                self.tech_labors.append(agent)

        total_work_output = sum(member.work(vec1, work_scale) for member in self.farmers)
        total_work_output += sum(agent.work(vec1, work_scale) for agent in self.tech_labors) # remaining labor from tech
        total_production = 0.0
        total_land_quality = []
        for cell in farm_cells:
            if getattr(cell, "fallow", False):
                production = total_work_output * fishing_discount
                land_quality = 0 # should this be 0 or its original quality?
            else:
                land_quality = cell.soil
                max_cap = cell.max_capacity or 1

                scaled_work_output = total_work_output / (total_work_output + max_cap)
                production = scaled_work_output * land_quality * prod_multiplier

                # update land attributes
                cell.farming_intensity = scaled_work_output
                cell.farming_counter = getattr(cell, "farming_counter", 0) + 1

            total_production += production
            total_land_quality.append(land_quality)

        self.add_food(total_production*climate)
        self.update_food_storage()
        tool_multiplier = 1.0 # need to recount per year
        if self.resources['stone'] > 0:      tool_multiplier += 0.1
        if self.resources['obsidian'] > 0:   tool_multiplier += 0.3
        productivity = total_work_output * tool_multiplier * (sum(total_land_quality)/len(farm_cells))
        self.productivity = productivity

        
    
    def remove_food(self, amount):
       
        for i in range(len(self.food_storage)):
            removed = 0
            if self.food_storage[i][0] > amount:
                
                self.food_storage[i] = (self.food_storage[i][0] - amount, self.food_storage[i][1])
                removed += amount
                break
            else:
                amount -= self.food_storage[i][0]
                removed += self.food_storage[i][0]
                self.food_storage[i] = (0, 0)
        self.food_storage = list((x, y) for x, y in self.food_storage if x > 0)
        return removed


    def get_distance(self, location1, location2):
        x1, y1 = location1
        x2, y2 = location2
        return abs(x1 - x2) + abs(y1 - y2)

    def extend(self, new_member):
        self.members.append(new_member)
        # print(f"Household {self.id} has a newborn.")

    def remove_member(self, member):
        if member in self.members:
            self.members.remove(member)
            # print(f"Household {self.id} removed member {member.household_id}.")
        else:
            # print(f"Member {member.household_id} in Household {self.id} died.")
            pass
    
    def split_household(self, village, food_expiration_steps): # split the household if it is too large
        
        empty_land_cells = [land for land in village.lands if land.occupied == None and not land.fallow]
        
        if len(empty_land_cells) > 100:
            new_household_members_ids = set()
            random.shuffle(self.members)
            members_to_leave = len(self.members) // 2
            count = 0
            for agent in self.members:
                if count < members_to_leave and agent.marital_status == 'single':
                    new_household_members_ids.add(agent.id)
                    count += 1
                    
                if count < members_to_leave and agent.marital_status == 'married' and agent.partner_id not in new_household_members_ids:
                    new_household_members_ids.add(agent.id)
                    new_household_members_ids.add(agent.partner_id)
                    count += 2 

            new_household_members = []
            for member in self.members:
                if member.id in new_household_members_ids:
                    new_household_members.append(member)
            
            for member in new_household_members:
                if member in self.members:
                    self.remove_member(member)

                new_household_members_ids.remove(member.id)
                        
            if len(new_household_members_ids) > 0:
                raise BaseException('Agent to split not in household {}!'.format(self.id))

            new_food_storage = [(f/2, y) for (f, y) in self.food_storage]
            self.food_storage = new_food_storage

            new_luxury_good_storage = self.luxury_good_storage // 2
            self.luxury_good_storage -= new_luxury_good_storage
            
            new_household = Household(
                food_storage=[(new_food_storage, 0)],
                luxury_good_storage=new_luxury_good_storage,
                members=new_household_members,
                location = None,
                home = None,
                farmlands=None,
                food_expiration_steps = food_expiration_steps
            )
            new_household.parents.append(self.id) # track for kin
            new_household.parents + self.parents
            for m in new_household.members:
                m.household_id = new_household.id

            random_ch = random.choice(empty_land_cells)
            new_location = random_ch.location
            random_ch.owner = new_household.id
            from utils import allocate_household_land
            land_by_id = village.land_by_id
            new_farmlands = allocate_household_land(
                            home_location=new_location,
                            num_farm_pixels=100,
                            land_by_id=land_by_id,
                            weights=None
                            )

            random_ch.occupied = "house"
            for land in new_farmlands:
                land.occupied = "farm"
                land.owner = new_household.id
            new_household.home = random_ch
            new_household.location = new_location
            new_household.farmlands = new_farmlands
            for i in new_farmlands:
                i.owner = new_household.id

            village.households.append(new_household)

            new_household.create_network_connectivity(village, village.network, True,
                lambda x, y:1/village.get_distance(x.location, y.location))
            new_household.create_network_connectivity(village, village.network_relation, False,
                lambda x, y: 0)
            # print(f'Household {self.id} splitted to {new_household.id}')
        else:
            # print('ops, no empty land cells to split')
            pass

    def emigrate(self, village, food_expiration_steps):
        """Handle the splitting of a household where one part emigrates."""
        new_household_members_ids = set()
        random.shuffle(self.members)
        members_to_leave = len(self.members) // 2

        count = 0
        for agent in self.members:
            if count < members_to_leave and agent.marital_status == 'single':
                new_household_members_ids.add(agent.id)
                count += 1
            if count < members_to_leave and agent.marital_status == 'married' and agent.partner_id not in new_household_members_ids:
                new_household_members_ids.add(agent.id)
                new_household_members_ids.add(agent.partner_id)
                count += 2

        new_household_members = [m for m in self.members if m.id in new_household_members_ids]
        
        for member in new_household_members: # need to make sure it is removed.
            self.remove_member(member)
            village.emigrate[village.time] += 1
        
        self.food_storage = [(f/2, y) for (f, y) in self.food_storage]
        self.luxury_good_storage //= 2  # Reduce by half
            
        # print(f'Household {self.id} split; {len(new_household_members)} members emigrated.')


    def create_network_connectivity(self, village, network, include_luxury_goods, f):
        if self.id not in network:
            new_conn = {'connectivity': {}}
            if include_luxury_goods:
                new_conn['luxury_goods'] = self.luxury_good_storage
            for other_household in village.households:
                if other_household.id != self.id:
                    new_conn['connectivity'][other_household.id] = f(self, other_household)
                    network[other_household.id]['connectivity'][self.id] = f(other_household, self)
            network[self.id] = new_conn

    def reduce_food_from_house(self, village, food_amount):
        still_need = food_amount
        while still_need > 0 and self.food_storage:
            amount, age_added = self.food_storage[0]
            if amount > still_need:
                self.food_storage[0] = (amount - still_need, age_added)
                still_need = 0
            else:
                self.food_storage.pop(0)
                still_need -= amount
        village.add_food_village(food_amount - still_need)
    
    def get_total_food(self):
        return sum(amount for amount, _ in self.food_storage)
    
    def get_total_asset(self):
        total_food = self.get_total_food()
        total_luxury = self.luxury_good_storage
        return total_food + total_luxury
    
    def get_wealth(self, exchange_rate):
        food = sum(amount for amount, _ in self.food_storage)
        total_luxury = sum(self.resources[r] * exchange_rate[r] for r in self.resources)
        luxury = total_luxury
        return food +luxury 

    def get_luxury(self):
        weights = {"stone": 0.1, "obsidian": 0.3, "jade": 1.0}
        total_luxury = sum(self.resources[r] * weights[r] for r in self.resources)
        # luxury = self.luxury_good_storage
        return total_luxury
    
    def discover_resource(self, vec1, work_scale, neighbors): # technology

        if neighbors: # social diffusion
            neighbor_resource_sum = sum(
                (n.resources["stone"] +
                n.resources["obsidian"] +
                n.resources["jade"])
                for n in neighbors
            )

            boost = 1 + min(1.0, (neighbor_resource_sum / 5) * 0.10) # chances, improve the def
        else:
            boost = 1.0

        for patch in self.farmlands:
            # regenerate resources each year with small probability
            if patch.has_stone:
                patch.has_stone = random.random() < 0.7 * boost
            if patch.has_obsidian:
                patch.has_obsidian = random.random() < 0.5 * boost
            if patch.has_jade:
                patch.has_jade = random.random() < 0.5 * boost
            # attempt discovery
            for resource, has_resource in [('stone', patch.has_stone),
                                        ('obsidian', patch.has_obsidian),
                                        ('jade', patch.has_jade)]:
                if has_resource:
                    labor_needed = 1  # unit of labor per resource
                    while labor_needed > 0 and self.tech_labors:
                        agent = self.tech_labors[0]
                        # ensure each agent has remaining work
                        if not hasattr(agent, "remaining_work"):
                            agent.remaining_work = agent.work(vec1, work_scale)
                        if agent.remaining_work >= labor_needed:
                            agent.remaining_work -= labor_needed
                            self.resources[resource] += 1
                            labor_needed = 0
                        else:
                            labor_needed -= agent.remaining_work
                            agent.remaining_work = 0
                            self.tech_labors.pop(0)  # exhausted agent
                        # increase prestige if jade discovered
                        if resource == 'jade':
                            self.prestige += 1  # or scale with quantity if needed