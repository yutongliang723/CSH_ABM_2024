import random
from agent import Agent
import itertools
# from main import idh_count


class Household:
    _id_iter = itertools.count(start = 1)
    def __init__(self, members, location, food_storage, luxury_good_storage,food_expiration_steps):
        self.id = next(Household._id_iter)
        # print('New household: {}'.format(self.id))
        self.members = members
        self.location = location  
        self.food_storage = []
        self.food_storage_timestamps = []
        self.luxury_good_storage = luxury_good_storage
        self.current_step = 0
        self.food_expiration_steps = food_expiration_steps
        
        
    
    def clean_up(self):
        self.members.clear()  
        self.location = None
    
    def add_food(self, amount):
        """Add food with the current step count."""
        self.food_storage.append((amount, self.current_step))
        # print(f"Added {amount:.2f} units of food to Household {self.id}.")
    
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
        return village.land_types[self.location]['quality']

    def get_land_max_capacity(self, village):
        return village.land_types[self.location].get('max_capacity', 1.0)
    

    def produce_food(self, village, vec1, prod_multiplier, fishing_discount, work_scale):
        """Simulate food production based on land quality and the work done by household members."""
        land_data = village.land_types[self.location]
        if land_data['fallow']:
            production_amount = 0
            for member in self.members:
                # if member.is_alive:
                if 1 == 1:
                    work_output = member.work(vec1, work_scale) 
            
                    production_amount += work_output * fishing_discount
            # print(f"Household {self.id} cannot farm land plot {self.location} because it is fallow.")
        
        else:
            land_quality = village.land_types[self.location]['quality']
            production_amount = 0
            total_work_output = 0
            for member in self.members:
                total_work_output += member.work(vec1, work_scale)

            scaled_work_output = total_work_output / (total_work_output + village.land_types[self.location]['max_capacity'])
            production_amount = scaled_work_output * land_quality * prod_multiplier
            village.land_types[self.location]['farming_intensity'] = scaled_work_output
            village.land_types[self.location]['farming_counter'] += 1
            # print(f"Household {self.id} produced {production_amount} units of food. Land quality: {land_quality}")
        self.add_food(production_amount)
        self.update_food_storage()
        
    
    def remove_food(self, amount):
        """
        Remove the given amount of food from this household.
        Does not keep track of the expiry of the removed food.
        Returns the actual amount of food removed (can be less than amount, if storage is too low).
        """
        # print(self.food_storage)
        for i in range(len(self.food_storage)):
            removed = 0
            if self.food_storage[i][0] > amount:
                # note: tuples are immutable, so we cannot do self.food_storage[i][0] -= amount
                self.food_storage[i] = (self.food_storage[i][0] - amount, self.food_storage[i][1])
                removed += amount
                break
            else:
                amount -= self.food_storage[i][0]
                removed += self.food_storage[i][0]
                self.food_storage[i] = (0, 0)
        self.food_storage = list((x, y) for x, y in self.food_storage if x > 0)
        return removed

    # def consume_food(self, total_food_needed, village):
    #     """Simulate food consumption by household members."""
    #     # total_food_needed = sum(member.vec1.rho[member.get_age_group_index()] for member in self.members)
    #     self.food_storage.sort(key=lambda x: x[1])
    #     self.update_food_storage()
    #     total_available_food = sum(amount for amount, _ in self.food_storage)
    #     if not len(self.food_storage) == 0:

    #         consumed = self.remove_food(total_food_needed)
    #         # print('Household total food need: ', total_food_needed, '\n', 'Household total available food: ', total_available_food, '\nFood consumed: ', consumed)
    #     else: 
    #         village.remove_household(self)


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
    
    def split_household(self, village, food_expiration_steps):
        """Handle the splitting of a household when it grows too large."""
        
        empty_land_cells = [loc for loc, data in village.land_types.items() if data['occupied'] == False and data['fallow'] == False]
        
        if empty_land_cells:
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
                food_expiration_steps = food_expiration_steps
            )
            for m in new_household.members:
                m.household_id = new_household.id

            new_location = random.choice(empty_land_cells)
            village.land_types[new_location]['occupied'] = True
            # village.land_types[new_location]['household_id'] = new_household.id
            new_household.location = new_location

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
        luxury = self.luxury_good_storage
        return food + exchange_rate * luxury # 10

    def get_luxury(self):
        luxury = self.luxury_good_storage
        return luxury
    