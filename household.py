import random
from agent import Agent

class Household:
    def __init__(self, id, members, location, food_storage, luxury_good_storage, land_quality, land_max_capacity, land_recovery_rate):
        self.id = id
        self.members = members
        self.location = location
        self.food_storage = food_storage
        self.luxury_good_storage = luxury_good_storage
        self.land_quality = land_quality
        self.land_max_capacity = land_max_capacity
        self.land_recovery_rate = land_recovery_rate

    def produce_food(self):
        """Simulate food production based on land quality."""

        production_amount = random.randint(50, 100) * self.land_quality
        self.food_storage += production_amount
        print(f"Household {self.id} produced {production_amount:.2f} units of food.")

        # Update land capacity based on farming intensity
        farming_intensity = 0.5  # TODO
        self.update_land_capacity(farming_intensity)

    def consume_food(self):
        """Simulate food consumption by household members."""
        total_food_needed = 0
        for member in self.members:
            age_index = member.get_age_group_index() 
            rho = member.vec1.rho[age_index]
            total_food_needed += rho

        total_food_needed /= 100  # Simplified
        
        if self.food_storage >= total_food_needed:
            self.food_storage -= total_food_needed
            print(f"Household {self.id} consumed {total_food_needed:.2f} units of food.")
        else:
            print(f"Household {self.id} does not have enough food. Consuming all available food.")
            self.food_storage = 0

    def update_land_capacity(self, farming_intensity):
        """
        Update the land capacity each year.
        K_{i}^{(t+1)} = K_{i}^{t} + c(K_{\text{max}} - K_{i}^{t}) - x_{i}aK_{i}^{t}
        
        :param farming_intensity: Intensity of farming (proportion of land farmed)
        """
        self.land_quality = (self.land_quality +
                             self.land_recovery_rate * (self.land_max_capacity - self.land_quality) -
                             farming_intensity * self.land_quality)
        
        # Ensure land_quality stays within valid bounds
        self.land_quality = max(0, min(self.land_quality, self.land_max_capacity))
        
        print(f"Household {self.id} updated land quality to {self.land_quality:.2f}.")

    def trade_resources(self):
        """Simulate trading resources with other households."""
        if not self.luxury_good_storage:
            print(f"Household {self.id} has no luxury goods to trade.")
            return
        
        trade_amount = min(self.luxury_good_storage, random.randint(1, 10))
        self.luxury_good_storage -= trade_amount
        print(f"Household {self.id} traded {trade_amount} units of luxury goods.")

    def migrate(self):
        new_location = f"New Location {random.randint(1, 100)}"
        self.location = new_location
        print(f"Household {self.id} migrated to {self.location}.")

    def extend(self, new_member):
        """Add a new agent to the household."""
        self.members.append(new_member)
        print(f"Household {self.id} has a newborn.")
    
    def remove_member(self, member):
        """Remove a member from the household."""
        if member in self.members:
            self.members.remove(member)
            print(f"Household {self.id} removed member {member.household_id}.")
        else:
            print(f"Member {member.household_id} in Household {self.id} died.")
