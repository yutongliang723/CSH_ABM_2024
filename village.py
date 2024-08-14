from household import Household
import matplotlib.pyplot as plt
import numpy as np
from PIL import Image, ImageDraw, ImageFont
import matplotlib.animation as animation
from IPython.display import display
import ipywidgets as widgets
import random
from agent import Agent
from agent import Vec1

class Village:
    def __init__(self, households, land_types):
        self.households = households
        self.land_types = land_types
        self.time = 0
        self.population_over_time = []
        self.land_capacity_over_time = []
        self.land_capacity_over_time_all = []
        self.food_storage_over_time = []
        self.land_usage_over_time = []
        self.average_fertility_over_time = []
        self.network = {}
        self.spare_food = []
        self.luxury_goods_in_village = 0
        self.food_expiration_steps = 3

    def initialize_network(self):
        for household in self.households:
            self.network[household.id] = {
                'connectivity': 0,
                'luxury_goods': 0  
            }
        self.luxury_goods_in_village = 50  


    def update_network_connectivity(self): # updates connectivity based on trading and distance
        for household_id, data in self.network.items():
            for other_id, other_data in self.network.items():
                if household_id != other_id:
                    id1 = self.get_household_by_id (household_id)
                    id2 = self.get_household_by_id (other_id)
                    distance = self.get_distance(id1.location, id2.location)
                    data['connectivity'] = max(data['connectivity'], 10 - distance)
        for household in self.households:
            if household.id in self.network:
                self.network[household.id]['luxury_goods'] = household.luxury_good_storage

    def manage_luxury_goods(self):
        for household in self.households:
            # food_storage_needed = household.calculate_food_need()
            food_storage_needed = sum(member.vec1.rho[member.get_age_group_index()] for member in household.members)
            total_available_food = sum(amount for amount, _ in household.food_storage)
            excess_food = total_available_food - 2 * food_storage_needed
             
            if excess_food // 10 >= 1:
                max_luxury_goods = min(excess_food // 10, self.luxury_goods_in_village)
                # # print("!!!!!!!!", excess_food // 10)
                household.luxury_good_storage += max_luxury_goods
                self.luxury_goods_in_village -= max_luxury_goods
                food_to_exchange = max_luxury_goods * 10 
                
                for amount, age_added in household.food_storage:
                    if food_to_exchange <= amount:
                        household.food_storage[0] = (amount - food_to_exchange, age_added)
                        break
                    else:
                        household.food_storage.pop(0)
                        food_to_exchange -= amount
            
                self.spare_food.append((max_luxury_goods, self.time))
                # print(f"Household {household.id} exchanged {max_luxury_goods} luxury good from village in year {self.time}")
        self.luxury_goods_in_village += 1
        self.update_spare_food_expiration()
    
    def update_spare_food_expiration(self):
        current_time = self.time  
        self.spare_food = [(amount, age_added) for amount, age_added in self.spare_food if current_time - age_added < self.food_expiration_steps]


    def trade_luxury_goods(self):
        
        for household in self.households:
            food_storage_needed = sum(member.vec1.rho[member.get_age_group_index()] for member in household.members)
            total_available_food = sum(amount for amount, _ in household.food_storage)
            excess_food = total_available_food - 2 * food_storage_needed
            # select randomly
            # loop through families: 2 types of trading -> look through connectivities
            # TODO: give condition of mutual trading
            if self.luxury_goods_in_village == 0 and excess_food // 10 >= 1:
                best_trade = None
                best_connectivity = -1
                for other_household_id, data in self.network.items():
                    if other_household_id != household.id and data['luxury_goods'] > 0:
                        if self.network[household.id]['connectivity'] < self.network[other_household_id]['connectivity']:
                            if self.network[household.id]['connectivity'] > best_connectivity:
                                best_trade = other_household_id
                                best_connectivity = self.network[household.id]['connectivity']
                
                if best_trade:
                    other_household = self.get_household_by_id(best_trade)
                    food_needed = sum(member.vec1.rho[member.get_age_group_index()] for member in household.members)
                    if other_household.luxury_good_storage > 0 and household.food_storage < 2 * food_needed:
                        household.luxury_good_storage += 1
                        other_household.luxury_good_storage -= 1

                        food_to_exchange = 10 
                        new_food_storage_household = []
                        remaining_food_to_exchange = food_to_exchange
                        for amount, age_added in household.food_storage:
                            if remaining_food_to_exchange <= amount:
                                if amount - remaining_food_to_exchange > 0:
                                    new_food_storage_household.append((amount - remaining_food_to_exchange, age_added))
                                break
                            else:
                                remaining_food_to_exchange -= amount
                        
                        household.food_storage = new_food_storage_household
                        
                        other_household_food_storage = other_household.food_storage[:]
                        food_added = []
                        while remaining_food_to_exchange > 0:
                            if not other_household_food_storage:
                                break
                            amount, age_added = other_household_food_storage.pop()
                            if remaining_food_to_exchange <= amount:
                                food_added.append((remaining_food_to_exchange, age_added))
                                if amount - remaining_food_to_exchange > 0:
                                    other_household_food_storage.append((amount - remaining_food_to_exchange, age_added))
                                remaining_food_to_exchange = 0
                            else:
                                food_added.append((amount, age_added))
                                remaining_food_to_exchange -= amount
                        other_household.food_storage.extend(food_added)

                        self.network[household.id]['connectivity'] += 1
                        self.network[best_trade]['connectivity'] += 1
                        # print(f"Household {household.id} traded with Household {best_trade}.")

    def get_household_by_id(self, household_id):
        """Retrieve a household by its ID."""
        for household in self.households:
            if household.id == household_id:
                return household
        return None
    
    def migrate_household(self, household):
        """Handle the migration of a household to a new land cell if necessary."""
        empty_land_cells = [(cell_id, land_data) for cell_id, land_data in self.land_types.items() if not land_data['occupied']]
        total_food_needed = sum(member.vec1.rho[member.get_age_group_index()] for member in household.members) / 100
        land_quality = self.land_types[household.location]['quality']
        total_food_storage = sum(amount for amount, _ in household.food_storage)

        if total_food_storage < 1.5 * total_food_needed and land_quality < 0.5:
            if empty_land_cells:
                best_land = min(empty_land_cells, key=lambda x: (self.get_distance(household.location, x[0]), -x[1]['quality']))
                self.land_types[household.location]['occupied'] = False
                household.location = best_land[0]
                self.land_types[household.location]['occupied'] = True
                # print(f"Household {household.id} migrated to {household.location}.")

    def get_distance(self, location1, location2):
        x1, y1 = map(int, location1.split(','))
        x2, y2 = map(int, location2.split(','))
        return abs(x1 - x2) + abs(y1 - y2)
    
    def update_household(self, household):
        """Update the household status, including reproduction and splitting."""
        new_agents = []

        for agent in household.members:
            if agent.is_alive:
                agent.age_and_die(self.land_types)
                if agent.is_alive and agent.gender == 'female' and agent.fertility > 0:
                    if len(household.members) < 5 or self.is_land_available():
                        new_agents.append(self.reproduce_agent(household, agent))
                    else:
                        # print(f"Agent {agent.household_id} cannot reproduce due to lack of available land.")
                        pass
        
        household.members.extend(new_agents)

        if len(household.members) > 5 and self.is_land_available(): # shouldn't pass till this line
            self.split_household(household)

    def is_land_available(self):
        return any(not data['occupied'] for data in self.land_types.values())

    def reproduce_agent(self, household, parent_agent): # try not import
        """Create a new agent as the child of an existing agent."""
        new_agent = Agent(
            household_id=household.id,
            age=0,
            gender=random.choice(['male', 'female']),
            vec1=parent_agent.vec1
        )
        # print(f"New agent born in Household {household.id}.")
        return new_agent

    # def split_household(self, household):
    #     """Handle the splitting of a household when it grows too large."""
    #     empty_land_cells = [loc for loc, data in self.land_types.items() if not data['occupied']]
    #     if empty_land_cells:

    #         num_members_to_split = len(household.members) // 2
    #         new_members = household.members[:num_members_to_split]
    #         household.members = household.members[num_members_to_split:]
    #         total_food_storage = sum(amount for amount, _ in household.food_storage)
    #         new_household_id = f"{household.id}->"
    #         new_food_storage = total_food_storage
    #         new_luxury_good_storage = household.luxury_good_storage / 2

    #         new_household = Household(
    #             id=new_household_id,
    #             members=new_members,
    #             location = None,  # new_location below
    #             food_storage=[(new_food_storage, 0)],
    #             luxury_good_storage=new_luxury_good_storage
    #         )

    #         new_location = random.choice(empty_land_cells)
    #         self.land_types[new_location]['occupied'] = True
    #         self.land_types[new_location]['household_id'] = new_household.id
    #         new_household.location = new_location
    #         self.households.append(new_household)
    #         self.network[new_household.id] = {'connectivity': 0, 'luxury_goods': 0}
    #         self.update_network_connectivity()
    #         # print(f"Household {household.id} split into Household {new_household_id} at location {new_location}.")
    #     else:
    #         # print(f"No available land for splitting Household {household.id}. New household not created.")
    #         pass


    def run_simulation_step(self, vec1):
        """Run a single simulation step (year)."""
        self.time += 1
        # print(f"\nSimulation Year {self.time}")
        # print(self.land_types)
        for household in self.households:
            household.produce_food(self, vec1)
            household.consume_food()
            # household.update_food_storage() # clean the expired food
            self.migrate_household(household)

            dead_agents = []
            newborn_agents = []

            for agent in household.members:
                agent.age_and_die()  

                if not agent.is_alive:
                    dead_agents.append(agent)
                else:
                    if agent.newborn_agents:
                        newborn_agents.extend(agent.newborn_agents)
                        agent.newborn_agents = []

            for agent in dead_agents:
                household.remove_member(agent)
            # print(f"Household {household.id} had {len(dead_agents)} members die.")

            for child in newborn_agents:
                household.extend(child)
            # print(f"Household {household.id} had {len(newborn_agents)} newborns.")

            if len(household.members) > 5:
                household.split_household(self)

            household.advance_step()
        
        self.update_tracking_variables()
        self.track_land_usage()
        self.update_land_capacity()
        # # print(self.luxury_goods_in_village)
        # print(self.network)
        self.manage_luxury_goods()
        self.trade_luxury_goods()
        self.update_network_connectivity()
       
    
    def update_land_capacity(self):
        """Update the land quality for each land cell in the village."""
        for location, land in self.land_types.items():
            land_quality = land['quality']
            land_max_capacity = land['max_capacity']
            land_recovery_rate = land['recovery_rate']
            farming_intensity = 0
            # check if there's a household at this location
            household = next((hh for hh in self.households if hh.location == location), None)
            
            if household is not None:
                farming_intensity = len(household.members)

                if farming_intensity == 0:
                    land['occupied'] = False
                    land['household_id'] = None
                    # print(f"Land at {location} is now unoccupied.")
                
            else:
                # If no household is found, land remains unoccupied
                land['occupied'] = False
                land['household_id'] = None
                # # print(f"Land at {location} remains unoccupied.")            
            new_quality = (
                        land_quality +
                        land_recovery_rate * (land_max_capacity - land_quality) -
                        farming_intensity * 0.1 * land_quality
                    )
            land['quality'] = max(0, min(new_quality, land_max_capacity))
            # # print(f"Land at {location} updated to quality {land['quality']:.2f}.")

    def track_land_usage(self):
        """Track the land usage and quality over time."""
        land_snapshot = {}
        for loc, land_data in self.land_types.items():
            land_snapshot[loc] = {
                'quality': land_data['quality'],
                'occupied': land_data['occupied'],
                'household_id': None,
                'num_members':None
            }
            for household in self.households:
                if household.location == loc:
                    land_snapshot[loc]['household_id'] = household.id
                    land_snapshot[loc]['num_members'] = len(household.members)
        self.land_usage_over_time.append(land_snapshot)
    


    def generate_animation(self, grid_dim):
        """Generate an animation of land usage over time."""
        if not self.land_usage_over_time:
            # print("Error: No land usage data available for animation.")
            return

        cmap = plt.get_cmap('OrRd')
        try:
            font = ImageFont.truetype("arial.ttf", 20)  # Use a TrueType font
        except IOError:
            font = ImageFont.load_default()  

        def render_animation(year):
            """Render the animation for a given year."""
            year_data = self.land_usage_over_time[year]

            image = Image.new('RGBA', (grid_dim * 100, grid_dim * 100), color=(255, 255, 255, 0))
            draw = ImageDraw.Draw(image)

            for loc, land_data in year_data.items():
                x, y = map(int, loc.split(','))
                x *= 100
                y *= 100

                quality = land_data['quality']
                color = tuple(int(255 * c) for c in cmap(quality/2)[:3])

                draw.rectangle([(x, y), (x + 100, y + 100)], fill=color)

                if land_data['occupied']:
                    quality = land_data['quality']
                    household_id = land_data['household_id']
                    household = self.get_household_by_id(household_id) 
                    agent_num = land_data['num_members']
                    text = f"{household_id}: # {agent_num}. Q: {round(quality, 2)}"

                    bbox = draw.textbbox((x, y), text, font=font)
                    text_width = bbox[2] - bbox[0]
                    text_height = bbox[3] - bbox[1]

                    text_x = x + (100 - text_width) // 2
                    text_y = y + (100 - text_height) // 2
                    
                    text_x = max(x + 5, min(text_x, x + 100 - text_width - 5))
                    text_y = max(y + 5, min(text_y, y + 100 - text_height - 5))
                    
                    draw.text((text_x, text_y), text, fill=(0, 0, 0), font=font)

            draw.text((10, 10), f"Year: {year + 1}", fill=(0, 0, 0), font=font)
            return image

        animation_frames = []
        for year in range(len(self.land_usage_over_time)):
            image = render_animation(year)
            animation_frames.append(image)

        if not animation_frames:
            # print("Error: No animation frames generated.")
            return

        # print(f"Generated {len(animation_frames)} frames for animation.")

        # save to gif
        animation_frames[0].save('village_simulation.gif', format='GIF', append_images=animation_frames[1:], save_all=True, duration=200, loop=0, optimize=True)
        display(widgets.Image(value=open('village_simulation.gif', 'rb').read()))

    def update_tracking_variables(self):
        population = sum(len(household.members) for household in self.households)
        # land_capacity = sum(household.get_land_quality(self) for household in self.households)
        land_capcity_all = sum(self.land_types[key]['quality'] for key in self.land_types)
        land_capacity = sum(self.land_types[key]['quality'] for key in self.land_types if self.land_types[key]['occupied'] == True)
        # total_food = sum(household.food_storage for household in self.households)
        total_food = sum(
        sum(amount for amount, _ in household.food_storage)  # Sum the amounts in each tuple
        for household in self.households)

        self.population_over_time.append(population)
        self.land_capacity_over_time.append(land_capacity)
        self.food_storage_over_time.append(total_food)
        self.land_capacity_over_time_all.append(land_capcity_all)
        house_num = sum(len(household.members) for household in self.households)
        if house_num != 0:
            self.average_fertility_over_time.append(
                sum(member.fertility for household in self.households for member in household.members) / 
                house_num
            )
        else:self.average_fertility_over_time.append(0)
        # print(self.land_types)
        # # print(self.average_fertility_over_time)


    def plot_simulation_results(self, file_name):
        plt.figure(figsize=(12, 12))
        plt.subplot(4, 1, 1)
        plt.plot(self.population_over_time, label='Population')
        plt.xlabel('Time Step')
        plt.ylabel('Population')
        plt.legend()
        plt.subplot(4, 1, 2)
        plt.plot(self.land_capacity_over_time, label='Occupied Land Capacity')
        plt.plot(self.land_capacity_over_time_all, label='All Land Capacity', linestyle='--') 
        plt.xlabel('Time Step')
        plt.ylabel('Land Capacity')
        plt.legend()
        plt.subplot(4, 1, 3)
        plt.plot(self.food_storage_over_time, label='Food Storage')
        plt.xlabel('Time Step')
        plt.ylabel('Food Storage')
        plt.legend()
        plt.subplot(4, 1, 4)
        plt.plot(self.average_fertility_over_time, label='Avg. Fertility')
        plt.xlabel('Time Step')
        plt.ylabel('Average Household Fertility')
        plt.legend()
        plt.tight_layout()
        plt.savefig(file_name)
        plt.show()
        plt.close()