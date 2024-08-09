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
        # self.time = 0
        self.current_step = 0
        self.food_expiration_steps = 3
    
    def add_food(self, amount):
        """Add food with the current step count."""
        self.food_storage.append((amount, self.current_step))
        print(f"Added {amount:.2f} units of food to Household {self.id}.")

    def update_food_storage(self):
        """Remove expired food from storage based on the current step."""
        self.food_storage = [(amount, age_added) for amount, age_added in self.food_storage
                             if self.current_step - age_added < self.food_expiration_steps]
        print(f"Updated food storage for Household {self.id}.")

    def advance_step(self):
        """Advance the step count."""
        self.current_step += 1

    def get_land_quality(self, village):
        return village.land_types[self.location]['quality']

    def get_land_max_capacity(self, village):
        return village.land_types[self.location].get('max_capacity', 1.0)
    

    def produce_food(self, village):
        """Simulate food production based on land quality and the work done by household members."""
        land_quality = village.land_types[self.location]['quality']
        production_amount = 0
        for member in self.members:
            if member.is_alive:
                work_output = member.work() 
                production_amount += work_output * land_quality * 20

        # self.food_storage += production_amount
        self.add_food(production_amount)
        # self.food_storage_timestamps.append((self.food_storage, self.time))
        print(f"Household {self.id} produced {production_amount:.2f} units of food.")
    
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
            for amount, age_added in self.food_storage:
                if food_to_consume <= amount:
                    self.food_storage[0] = (amount - food_to_consume, age_added)
                    break
                else:
                    self.food_storage.pop(0)
                    food_to_consume -= amount
            print(f"Household {self.id} consumed {total_food_needed:.2f} units of food.")
        else:
            print(f"Household {self.id} does not have enough food. Consuming all available food.")
            self.food_storage = []

    def get_distance(self, location1, location2):
        x1, y1 = map(int, location1.split(','))
        x2, y2 = map(int, location2.split(','))
        return abs(x1 - x2) + abs(y1 - y2)

    def extend(self, new_member):
        self.members.append(new_member)
        print(f"Household {self.id} has a newborn.")

    def remove_member(self, member):
        if member in self.members:
            self.members.remove(member)
            print(f"Household {self.id} removed member {member.household_id}.")
        else:
            print(f"Member {member.household_id} in Household {self.id} died.")