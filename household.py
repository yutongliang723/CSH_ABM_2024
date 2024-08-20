import random
from agent import Agent
# from village import Village
class Household:
    def __init__(self, id, members, location, food_storage, luxury_good_storage):
        self.id = id
        self.members = members
        self.location = location  
        self.food_storage = []
        self.food_storage_timestamps = []
        self.luxury_good_storage = 0
        self.current_step = 0
        self.food_expiration_steps = 3
        self.household_id = id
    
    def add_food(self, amount):
        """Add food with the current step count."""
        self.food_storage.append((amount, self.current_step))
        # print(f"Added {amount:.2f} units of food to Household {self.id}.")

    def update_food_storage(self):
        """Remove expired food from storage based on the current step."""
        self.food_storage = [(amount, age_added) for amount, age_added in self.food_storage
                             if self.current_step - age_added < self.food_expiration_steps]
        # self.advance_step()

    def advance_step(self):
        """Advance the step count for food expiration date."""
        self.current_step += 1

    def get_land_quality(self, village):
        return village.land_types[self.location]['quality']

    def get_land_max_capacity(self, village):
        return village.land_types[self.location].get('max_capacity', 1.0)
    

    def produce_food(self, village, vec1):
        """Simulate food production based on land quality and the work done by household members."""
        land_quality = village.land_types[self.location]['quality']
        # print(f'Land quality {land_quality}')
        production_amount = 0
        for member in self.members:
            # print(member)
            if member.is_alive:
                work_output = member.work() 
                # print(f'Agent{self.id}produced{work_output}. Agent work or not: {vec1.phi[member.age]}')
                production_amount += work_output * land_quality
                # production_amount += work_output

        # self.food_storage += production_amount
        self.add_food(production_amount)
        # self.food_storage_timestamps.append((self.food_storage, self.time))
        self.update_food_storage()
        # print(f"Household {self.id} produced {production_amount} units of food.")
    
    def consume_food(self):
        """Simulate food consumption by household members."""
        total_food_needed = sum(member.vec1.rho[member.get_age_group_index()] for member in self.members)
        self.food_storage.sort(key=lambda x: x[1])
        # remove expired food
        self.food_storage = [(amount, age_added) for amount, age_added in self.food_storage
                             if self.current_step - age_added < self.food_expiration_steps]

        # self.food_storage_timestamps = [(amount, timestamp) for amount, timestamp in self.food_storage_timestamps]
        #  if self.time - timestamp < 3
        total_available_food = sum(amount for amount, _ in self.food_storage)
        
        if total_available_food >= total_food_needed:
            food_to_consume = total_food_needed
            for i, (amount, age_added) in enumerate(self.food_storage):
                if food_to_consume <= amount:
                    self.food_storage[i] = (amount - food_to_consume, age_added)
                    break
                else:
                    self.food_storage.pop(i)
                    food_to_consume -= amount
            # print(f"Household {self.id} consumed {total_food_needed:.2f} units of food.")
        else:
            # print(f"Household {self.id} does not have enough food. Consuming all available food.")
            self.food_storage = []
            # print(f'Attention, there is not enough food for familly{self.household_id}')

        # print('Household total food need:', total_food_needed, '\n', 'Household total availabel food', total_available_food)

    def get_distance(self, location1, location2):
        x1, y1 = map(int, location1.split(','))
        x2, y2 = map(int, location2.split(','))
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
    
    def split_household(self, village):
        """Handle the splitting of a household when it grows too large."""
        
        empty_land_cells = [loc for loc, data in village.land_types.items() if not data['occupied']]
        
        if empty_land_cells:
            new_household_members = []

            for agent in self.members:
                if agent.marital_status == 'married':
                    # partner = agent.partner_id()
                    partner = village.get_agent_by_id(agent.partner_id)
                    if partner and partner not in new_household_members:
                        new_household_members.extend([agent, partner])
                        
            for member in new_household_members:
                self.remove_member(member)

            remaining_members_to_add = len(self.members) // 2 - len(new_household_members)
            additional_members = self.members[:remaining_members_to_add]
            new_household_members.extend(additional_members)

            for member in new_household_members:
                if member in self.members:
                    self.remove_member(member)

            total_food_storage = sum(amount for amount, _ in self.food_storage)
            new_food_storage = total_food_storage // 2
            self.food_storage = [(total_food_storage - new_food_storage, 0)]

            new_luxury_good_storage = self.luxury_good_storage // 2
            self.luxury_good_storage -= new_luxury_good_storage
            new_household_id = f"{self.id}->"
            
            # Create the new household
            new_household = Household(
                new_household_id,
                food_storage=[(new_food_storage, 0)],
                luxury_good_storage=new_luxury_good_storage,
                members=new_household_members,
                location = None
            )

            new_location = random.choice(empty_land_cells)
            village.land_types[new_location]['occupied'] = True
            village.land_types[new_location]['household_id'] = new_household.id
            new_household.location = new_location

            # Add the new household to the village
            village.households.append(new_household)

            # Update the village network
            village.network[new_household.id] = {
                'connectivity': {},
                'luxury_goods': new_household.luxury_good_storage
            }

            for other_household in village.households:
                if other_household.location != new_household.location and other_household.id != new_household.id:
                    distance = village.get_distance(new_household.location, other_household.location)
                    village.network[new_household.id]['connectivity'][other_household.id] = max(0, 1/distance)
                    village.network[other_household.id]['connectivity'][new_household.id] = max(0, 1/distance)

            village.update_network_connectivity()
            # print(f"Household {self.id} split into Household {new_household.id} at location {new_location}.")
        else:
            # print(f"No available land for splitting Household {self.id}. New household not created.")
            pass