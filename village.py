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
import statistics

# from utils import reduce_food_from_house

class Village:
    def __init__(self, households, land_types, food_expiration_steps, fallow_period):
        self.households = households
        self.land_types = land_types
        self.time = 0
        self.population_over_time = []
        self.land_capacity_over_time = []
        self.land_capacity_over_time_all = []
        self.food_storage_over_time = []
        self.land_usage_over_time = []
        self.average_fertility_over_time = []
        self.average_life_span = [0]
        self.network = {}
        self.network_relation = {}
        self.spare_food = []
        self.luxury_goods_in_village = 0
        self.food_expiration_steps = food_expiration_steps
        self.population = []
        self.num_house = []
        self.average_age = []
        self.gini_coefficients = []
        self.networks = []
        self.fallow_cycle = fallow_period
        self.population_accumulation = []

    def initialize_network(self):
        
        for household in self.households:
            self.network[household.id] = {
                'connectivity': {},  
                'luxury_goods': household.luxury_good_storage
            }
        
        for household in self.households:
            for other_household in self.households:
                id1 = self.get_household_by_id(household.id)
                id2 = self.get_household_by_id(other_household.id)
                if id1 != id2:
                    distance = self.get_distance(id1.location, id2.location)
                    # print('Distance: ', id1.location, id2.location)
                    self.network[household.id]['connectivity'][other_household.id] = max(0, 1/distance)
                    # print(other_household.id)
        self.luxury_goods_in_village = 50


    def initialize_network_relationship(self):
        for household in self.households:
            self.network_relation[household.id] = {
                'connectivity': {}
            }
        
        for household in self.households:
            for other_household in self.households:
                if household.id != other_household.id:
                    self.network_relation[household.id]['connectivity'][other_household.id] = 0
    
    

    def combined_network(self):
        result = {}
        for key in self.network.keys():
            merged_conn = {}

            if 'connectivity' in self.network[key]:
                merged_conn.update(self.network[key]['connectivity'])
            
            if 'connectivity' in self.network_relation.get(key, {}):
                for id_key, value in self.network_relation[key]['connectivity'].items():
                    if id_key in merged_conn:
                        merged_conn[id_key] += value  
                    else:
                        merged_conn[id_key] = value  
            household = self.get_household_by_id(key)
            result[key] = {'connectivity': merged_conn, 'num_member': len(household.members)}

        return result

    def update_network_connectivity(self):
        """Updates connectivity based on trading and distance."""
        valid_households = [household.id for household in self.households]
        # print(self.network)

        for household_id in list(self.network.keys()):
            if household_id in valid_households:
                
                household = self.get_household_by_id(household_id)
                self.network[household.id]['luxury_goods'] = household.luxury_good_storage
                connectivity = self.network[household_id]['connectivity']

                for other_id in list(connectivity.keys()):
                    if other_id in valid_households:
                        other_household = self.get_household_by_id(other_id)
                        if household.id != other_household.id:
                            distance = self.get_distance(household.location, other_household.location)
                            # print('distance', distance)
                            connectivity[other_id] = max(0, 1 / distance)
            else:
                # print('household not valid')
                pass
                    
    def add_food_village(self, amount):
        """Add food with the current step count."""
        self.spare_food.append((amount, self.time))

    def reduce_food_from_village(self, house, food_amount):
        still_need = food_amount
        while still_need > 0 and self.spare_food:
            amount, age_added = self.spare_food[0]
            if amount > still_need:
                self.spare_food[0] = (amount - still_need, age_added)
                still_need = 0
            else:
                self.spare_food.pop(0)
                still_need -= amount
        
        house.add_food(food_amount - still_need)
        return food_amount - still_need
    
    def manage_luxury_goods(self, exchange_rate, excess_food_ratio):
        for household in self.households:
            # food_storage_needed = household.calculate_food_need()
            food_storage_needed = sum(member.vec1.rho[member.get_age_group_index()] for member in household.members)
            total_available_food = sum(amount for amount, _ in household.food_storage)
            excess_food = total_available_food - excess_food_ratio * food_storage_needed
             
            if excess_food // exchange_rate >= 1 and self.luxury_goods_in_village > 0:
                max_luxury_goods = min(excess_food // exchange_rate, self.luxury_goods_in_village)
                household.luxury_good_storage += max_luxury_goods
                self.luxury_goods_in_village -= max_luxury_goods
                food_to_exchange = max_luxury_goods * exchange_rate 
                
                household.reduce_food_from_house(self, food_to_exchange)

                # print(f"Household {household.id} exchanged {max_luxury_goods} luxury good from village in year {self.time}")
        
        self.update_spare_food_expiration()
    
    def update_spare_food_expiration(self):
        current_time = self.time  
        # print('food in the loop check', self.spare_food)
        self.spare_food = [(amount, age_added) for amount, age_added in self.spare_food if current_time - age_added < self.food_expiration_steps]

    def trading(self, excess_food_ratio, trade_back_start):
        food_for_luxury = []
        luxury_for_food = []

        # Determine trading intentions for each household
        for household in self.households:
            food_needed = sum(member.vec1.rho[member.get_age_group_index()] for member in household.members)
            total_available_food = sum(amount for amount, _ in household.food_storage)
            
            if total_available_food > excess_food_ratio * food_needed and self.luxury_goods_in_village == 0: 
                """ Too much food - Wants to trade for luxury goods"""
                # print(f"Qualify to get more luxury {household.id}")
                food_for_luxury.append(household)
            if total_available_food < 50 * food_needed and household.luxury_good_storage > 0:
                """ Not enough food - Wants to trade for food """
                luxury_for_food.append(household)
                # print(f"Qualify to get more food {household.id}")
            # elif total_available_food < 1.5 * food_needed and household.luxury_good_storage == 0:
            #     charity.append(household)
            # this has been moved to run_simulation_step func

        combined_network = self.combined_network()
        for food_household in food_for_luxury:
            best_match = None
            best_connectivity = -1

            for luxury_household in luxury_for_food:
                if food_household.id != luxury_household.id:
                    connectivity = combined_network[food_household.id]['connectivity'][luxury_household.id]
                    if connectivity > best_connectivity:
                        best_connectivity = connectivity
                        best_match = luxury_household

            if best_match:
                self.execute_trade(food_household, best_match)
                luxury_for_food.remove(best_match)

    def execute_trade(self, food_household, luxury_household):
        #  Get the smaller portion household
        food_to_trade = sum(amount for amount, _ in food_household.food_storage) - 1.5 * sum(
            member.vec1.rho[member.get_age_group_index()] for member in food_household.members)

        luxury_goods_to_trade = min(luxury_household.luxury_good_storage, food_to_trade / 10)
        
        if luxury_goods_to_trade > 0:
            remaining_food_to_trade = food_to_trade # to get more luxury goods
            while remaining_food_to_trade > 0 and food_household.food_storage: # food_household: with too much food
                amount, age_added = food_household.food_storage[0]
                if remaining_food_to_trade <= amount:
                    food_household.food_storage[0] = (amount - remaining_food_to_trade, age_added)
                    remaining_food_to_trade = 0
                else:
                    food_household.food_storage.pop(0)
                    remaining_food_to_trade -= amount

            food_household.luxury_good_storage += luxury_goods_to_trade
            luxury_household.luxury_good_storage -= luxury_goods_to_trade

            # luxury_household.food_storage.append((food_to_trade, self.time))

            luxury_household.add_food(food_to_trade)

            self.network_relation[food_household.id]['connectivity'][luxury_household.id] += 1
            self.network_relation[luxury_household.id]['connectivity'][food_household.id] += 1

            # print(f"Household {food_household.id} traded {food_to_trade} units of food "
            #       f"for {luxury_goods_to_trade} luxury goods with Household {luxury_household.id}.")

    def get_household_by_id(self, household_id):
        """Retrieve a household by its ID."""
        for household in self.households:
            if household.id == household_id:
                return household
        return None
    

    """ shifting cultivation: field rotation, not crops""" #https://www.sciencedirect.com/topics/agricultural-and-biological-sciences/shifting-cultivation#:~:text=According%20to%20archaeological%20evidence%2C%20shifting,occurred%20(Sharma%2C%201976).


    def migrate_household(self, household):
        """Handle the migration of a household to a new land cell if necessary."""
        empty_land_cells = [(cell_id, land_data) for cell_id, land_data in self.land_types.items() if land_data['occupied'] == False and land_data['fallow'] == False]
        # total_food_needed = sum(member.vec1.rho[member.get_age_group_index()] for member in household.members)
        # land_quality = self.land_types[household.location]['quality']
        # total_food_storage = sum(amount for amount, _ in household.food_storage)

        # if total_food_storage < 1.5 * total_food_needed and total_food_storage > 0.2 * total_food_needed and land_quality < 1:
        #     print(f'Poor - Migration qualify for {household.id}')
        if empty_land_cells:
            # print("There are empty land to migrate")
            sorted_land_cells = sorted(empty_land_cells, key=lambda x: (self.get_distance(household.location, x[0]), -x[1]['quality']))
            best_land = sorted_land_cells[0]   
            self.land_types[household.location]['occupied'] = False
            household.location = best_land[0]
            self.land_types[household.location]['occupied'] = True
            migrate_cost = sum(amount for amount, _ in household.food_storage) * 0.2
            """ Pay for the migration """
            still_pay = migrate_cost
            while still_pay > 0 and household.food_storage:
                amount, age_added = household.food_storage[0]
                if amount > still_pay:
                    household.food_storage[0] = (amount - still_pay, age_added)
                    still_pay = 0
                else:
                    household.food_storage.pop(0)
                    still_pay -= amount
            # print(f"Household {household.id} migrated to {household.location}.")
        else:
            # print(f"Household {household.id} failed moving because there is no more space.")
            pass

    def get_distance(self, location1, location2):
        x1, y1 = location1
        x2, y2 = location2
        return abs(x1 - x2) + abs(y1 - y2)

    def is_land_available(self):
        return any(not data['occupied'] and not data['fallow'] for data in self.land_types.values())

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

    def remove_empty_household(self, household):
        if household in self.households:
            if len(household.members) == 0:
                # print('check check', [member.id for member in household.members])

                luxury_good_to_donate = household.luxury_good_storage
                food_to_donate = household.food_storage
                self.luxury_goods_in_village += luxury_good_to_donate
                if len(food_to_donate) != 0:
                    self.spare_food.extend(food_to_donate)

                self.land_types[household.location]['occupied'] = False
                self.households.remove(household)
                # print('empty household', household.id)
                del self.network[household.id]
                for c in self.network.values():
                    del c['connectivity'][household.id]
                del self.network_relation[household.id]
                for c in self.network_relation.values():
                    del c['connectivity'][household.id]
    def remove_household(self,household):
        luxury_good_to_donate = household.luxury_good_storage
        food_to_donate = household.food_storage
        self.luxury_goods_in_village += luxury_good_to_donate
        if len(food_to_donate) != 0:
            self.spare_food.extend(food_to_donate)

        self.land_types[household.location]['occupied'] = False
        self.households.remove(household)
        # print('empty household', household.id)
        del self.network[household.id]
        for c in self.network.values():
            del c['connectivity'][household.id]
        del self.network_relation[household.id]
        for c in self.network_relation.values():
            del c['connectivity'][household.id]
    def check_consistency(self):
        """
        Check that all components are consistent (i.e. no errors introduced)
        """

        all_agents = set() # keep track of all agent IDs encountered
        all_households = set() # all household IDs

        # 1. check all households and agents
        for household in self.households:
            if household.id in all_households:
                raise BaseException('Duplicate household ID: {}!\n'.format(household.id))
            all_households.add(household.id)
            for agent in household.members:
                # check that agent is alive (dead agents should be removed in run_simulaton_step() before running this check)
                if not agent.is_alive:
                    raise BaseException('Agent {} (household {}) is not alive!\n'.format(agent.id, household.id))
                # check that agent does not have children stored (they should be moved out as household member in run_simulaton_step() before running this check)
                if len(agent.newborn_agents) != 0:
                    raise BaseException('Agent {} (household {}) has unprocessed children!\n'.format(agent.id, household.id))
                if agent.id in all_agents:
                    raise BaseException('Duplicate agent ID: {} (in household {})!\n'.format(agent.id, household.id))
                all_agents.add(agent.id)
                # check that household ID is consistent
                if agent.household_id != household.id:
                    raise BaseException('Household ID does not match for agent {} ({} != {})!\n'.format(agent.id, agent.household_id, household.id))
                # check that marital status is consistent
                if agent.marital_status == 'married':
                    partner_id = agent.partner_id
                    if partner_id is None:
                        raise BaseException('Married agent {} (household {}) does not have a partner!\n'.format(agent.id, household.id))
                    partner = None
                    # find the partner (within the same household)
                    for x in household.members:
                        if x.id == partner_id:
                            partner = x
                            break
                    if partner is None:
                        raise BaseException('Cannot find partner (ID: {}) of agent {} in household {}!\n'.format(partner_id, agent.id, household.id))
                    if partner.marital_status != 'married' or partner.partner_id is None or partner.partner_id != agent.id:
                        raise BaseException('Marriage status inconsistent between agents {} and {} (household {})!\n'.format(agent.id, partner_id, household.id))
                    # note: we could also check that both agents meet the criteria for being married (>= 14 years old, different gender),
                    # but these are ensured by a simple condition when finding marriage partners, so it should be OK
                elif agent.marital_status != 'single':
                    raise BaseException('Invalid marital status for agent {} (household {})!\n'.format(agent.id, household.id))

        # 2. check network connections
        # we want to ensure that all household_id pairs are in both the networks and also that no invalid IDs are in the networks
        # 2.1. check that all household pairs are in both networks
        for id1 in all_households:
            for id2 in all_households:
                if id1 < id2:
                    # we check both ways in this case (note that this will also throw an exception if id1 
                    # is not in the network)
                    if id2 not in self.network[id1]['connectivity']:
                        raise BaseException('Network is missing {} -> {} link!\n'.format(id1, id2))
                    if id1 not in self.network[id2]['connectivity']:
                        raise BaseException('Network is missing {} -> {} link!\n'.format(id2, id1))
                    if id2 not in self.network_relation[id1]['connectivity']:
                        raise BaseException('Relation network is missing {} -> {} link!\n'.format(id1, id2))
                    if id1 not in self.network_relation[id2]['connectivity']:
                        raise BaseException('Relation network is missing {} -> {} link!\n'.format(id2, id1))

        # 2.2. check that all IDs in the networks are valid households
        for id1 in self.network:
            if id1 not in all_households:
                raise BaseException('Household ID {} is in the network, but does not exist!\n'.format(id1))
            for id2 in self.network[id1]['connectivity']:
                if id2 not in all_households:
                    raise BaseException('Household ID {} is in the network, but does not exist!\n'.format(id2))
        for id1 in self.network_relation:
            if id1 not in all_households:
                raise BaseException('Household ID {} is in the relation network, but does not exist!\n'.format(id1))
            for id2 in self.network_relation[id1]['connectivity']:
                if id2 not in all_households:
                    raise BaseException('Household ID {} is in the relation network, but does not exist!\n'.format(id2))

    def take_spare_food_for_poor(self, household, total_food, total_food_needed):
        """Take spare food from the village for households that need it."""
        
        if total_food < total_food_needed and len(self.spare_food) != 0:
            food_need = total_food_needed - total_food
            amount_get = self.reduce_food_from_village(household, food_need)
            household.add_food(amount_get)
            total_food += amount_get
            # print(f"Household {household.id} gets {amount_get} from the Village.")

    def run_simulation_step(self, vec1, pars, spare_food_enabled=False, fallow_farming = False):
    
        """Run a single simulation step (year)."""
        
        
        print(f"\nSimulation Year {self.time}")
        # print(self.land_types)
        self.update_network_connectivity()
        longevities = []
        print(f"Last year:{self.population_accumulation[-1]}")
        self.population_accumulation.append(self.population_accumulation[-1])
        

        total_new_born = 0
        for household in self.households:
            household.produce_food(self, vec1, pars.prod_multiplier, pars.fishing_discount)
            
            dead_agents = []
            newborn_agents = []

            total_food = sum(x for x, _ in household.food_storage)
            total_food_needed = sum(agent.vec1.rho[agent.get_age_group_index()] for
            	agent in household.members)
            if spare_food_enabled:
                self.take_spare_food_for_poor(household, total_food, total_food_needed)

            # z = total_food * total_food_needed

            for agent in household.members:
                # agent_food_needed= agent.vec1.rho[agent.get_age_group_index()]
                agent_food_needed = agent.vec1.rho[agent.get_age_group_index()]
                z = total_food * agent_food_needed / total_food_needed
                z = 1
                agent.age_and_die(household, self, z, pars.max_member, pars.fertility_scaler)
                
                if not agent.is_alive:
                    dead_agents.append(agent)
                else:
                    if agent.newborn_agents:
                        newborn_agents.extend(agent.newborn_agents)
                        agent.newborn_agents = []
                total_new_born += len(newborn_agents)
            self.population_accumulation[-1] += len(newborn_agents)
        
            for agent in dead_agents:
                longevities.append(agent.age)
                household.remove_member(agent)
            
            # print(f"Household {household.id} had {len(dead_agents)} members die.")

            for child in newborn_agents:
                household.extend(child)
            # print(f"Household {household.id} had {len(newborn_agents)} newborns.")
        
            # household.consume_food()
            household.consume_food(total_food_needed, self)
            self.remove_empty_household(household)
        print(f"village has {total_new_born} new born.")
        if longevities:
            self.average_life_span.append(sum(longevities)/len(longevities))
        else:
            # print('average_life_span', self.average_life_span)
            self.average_life_span.append(self.average_life_span[-1])

        for household in self.households:
            total_food_needed = sum(member.vec1.rho[member.get_age_group_index()] for member in household.members)
            land_quality = self.land_types[household.location]['quality']
            total_food_storage = sum(amount for amount, _ in household.food_storage)

            if total_food_storage < pars.storage_ratio_high * total_food_needed and total_food_storage > pars.storage_ratio_low * total_food_needed and land_quality < pars.land_capacity_low:
                # print(f'Poor - Migration qualify for {household.id}')

                self.migrate_household(household)
            self.propose_marriage(household, pars.marriage_from, pars.marriage_to, pars.bride_price_ratio) # if choose to comment out this line, please also comment out 

            if len(household.members) > pars.max_member:
                household.split_household(self, pars.food_expiration_steps)
            else: 
                pass
            self.remove_empty_household(household)
            household.advance_step()
            
        self.update_tracking_variables(pars.exchange_rate)
        self.track_land_usage()
        self.update_land_capacity(pars.land_depreciate_factor)        
        self.manage_luxury_goods(pars.exchange_rate, pars.excess_food_ratio)
        self.trading(pars.excess_food_ratio, pars.trade_back_start)
        if fallow_farming:
            self.update_fallow_land(pars.fallow_ratio, pars.fallow_period)
        self.update_network_connectivity()
        self.time += 1
        self.luxury_goods_in_village += pars.lux_per_year        
    
    def update_land_capacity(self, land_depreciate_factor):
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
                    # land['household_id'] = None
                    # print(f"Land at {location} is now unoccupied.")
                
            else:
                # If no household is found, land remains unoccupied
                land['occupied'] = False
                # land['household_id'] = None
                # # print(f"Land at {location} remains unoccupied.")            

            new_quality = (
                        land_quality +
                        land_recovery_rate * (land_max_capacity - land_quality) 
                        - farming_intensity ** 2 * land_quality * land_depreciate_factor # 0.01 # this 0.01 is an important factor that influence everything, can be changed
                    )
            land['quality'] = max(0, min(new_quality, land_max_capacity))
            # print(f"Land at {location} updated to quality {land['quality']:.2f}.")

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
                # print("len(household.members)", len(household.members))
        self.land_usage_over_time.append(land_snapshot)
        self.population.append(sum(len(household.members) for household in self.households))
        self.num_house.append(len(self.households))
        all_ages = []
        for household in self.households:
            all_ages.extend([member.age for member in household.members])

        if not len(all_ages):
            self.average_age.append(0)
        else:
            self.average_age.append(statistics.mean(all_ages))
    

    from PIL import Image, ImageDraw, ImageFont
    import matplotlib.pyplot as plt
    import matplotlib.cm as cm

    def generate_animation(self, file_path, grid_dim):
        """Generate an animation of land usage over time."""
        if not self.land_usage_over_time:
            # No data available to create animation
            return

        # Load color map and font
        cmap = plt.get_cmap('OrRd')
        try:
            font = ImageFont.truetype("arial.ttf", 20)  # TrueType font
        except IOError:
            font = ImageFont.load_default()  # Fallback to default if TTF font is unavailable

        cell_size = 100  # Each cell will be 100x100 pixels
        image_size = grid_dim * cell_size  # Ensures a square grid layout

        def render_animation(year):
            """Render the animation for a given year."""
            year_data = self.land_usage_over_time[year]
            
            # Create a new RGBA image
            image = Image.new('RGBA', (image_size, image_size), color=(255, 255, 255, 0))
            draw = ImageDraw.Draw(image)

            for (loc, land_data) in year_data.items():
                x, y = loc
                x *= cell_size
                y *= cell_size

                # Calculate color based on land quality
                quality = land_data['quality'] * 0.2
                color = tuple(int(255 * c) for c in cmap(quality / 2)[:3])
                
                # Draw land cell
                draw.rectangle([(x, y), (x + cell_size, y + cell_size)], fill=color)

                if land_data['occupied']:
                    # Occupied cell: add text with household and land info
                    household_id = land_data['household_id']
                    agent_num = land_data['num_members']
                    text = f"{household_id}: # {agent_num}. Q: {round(quality, 2)}"
                    
                    # Calculate text position and center it within the cell
                    bbox = draw.textbbox((0, 0), text, font=font)
                    text_width = bbox[2] - bbox[0]
                    text_height = bbox[3] - bbox[1]
                    
                    text_x = x + (cell_size - text_width) // 2
                    text_y = y + (cell_size - text_height) // 2

                    # Adjust to prevent clipping
                    text_x = max(x + 5, min(text_x, x + cell_size - text_width - 5))
                    text_y = max(y + 5, min(text_y, y + cell_size - text_height - 5))
                    
                    draw.text((text_x, text_y), text, fill=(0, 0, 0), font=font)
            
            # Add year and population information
            draw.text((10, 10), f"Year: {year + 1}; Population: {self.population[year]}; # Houses: {self.num_house[year]}", fill=(0, 0, 0), font=font)
            return image

        # Generate frames for each year
        animation_frames = [render_animation(year) for year in range(len(self.land_usage_over_time))]

        # Save as a GIF
        animation_frames[0].save(file_path, format='GIF', append_images=animation_frames[1:], save_all=True, duration=200, loop=0, optimize=True)

        # Display in notebook (if using Jupyter or IPython environment)
        # display(widgets.Image(value=open(file_path, 'rb').read()))

    

    def update_tracking_variables(self, exchange_rate):
        population = sum(len(household.members) for household in self.households)
        land_capcity_all = sum(self.land_types[key]['quality'] for key in self.land_types)
        land_capacity = sum(self.land_types[key]['quality'] for key in self.land_types if self.land_types[key]['occupied'] == True)
        amount_used = len([self.land_types[key]['quality'] for key in self.land_types if self.land_types[key]['occupied'] == True])
        # print('Amount Lands Occupied', amount_used)
        # print('Amout of Households', len(self.households))
        if amount_used != len(self.households):
            raise BaseException('Inconsistent land usage ({}, {})!\n'.format(amount_used, len(self.households)))
        total_food = sum(
        sum(amount for amount, _ in household.food_storage)  # Sum the amounts in each tuple
        for household in self.households)

        self.population_over_time.append(population)
        self.land_capacity_over_time.append(land_capacity)
        self.food_storage_over_time.append(total_food)
        self.land_capacity_over_time_all.append(land_capcity_all)
        self.track_inequality_over_time(exchange_rate)
        self.networks.append(self.combined_network())
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
        
        # plt.legend()
        
        # plt.tight_layout()
        # plt.savefig('static/gini_overtime.png')
        # plt.show()
        # plt.close()
        
        plt.figure(figsize=(18, 12))

        # Plot 1: Population over time
        plt.subplot(2, 4, 1)
        plt.plot(self.population_over_time, label='Population')
        plt.xlabel('Time Step', size = 20)
        plt.ylabel('Population', size = 20)
        # plt.xticks(size = 20)
        plt.yticks(size = 20)
        plt.legend()
        plt.title('Population Over Time',size = 20)

        # Plot 2: Land Capacity over time
        plt.subplot(2, 4, 2)
        plt.plot(self.land_capacity_over_time, label='Occupied Land Capacity')
        plt.plot(self.land_capacity_over_time_all, label='All Land Capacity', linestyle='--')
        plt.xlabel('Time Step', size = 20)
        plt.ylabel('Land Capacity', size = 20)
        # plt.xticks(size = 20)
        plt.yticks(size = 20)
        plt.legend(fontsize = 15)
        plt.title('Land Capacity Over Time', size = 20)

        # Plot 3: Food Storage over time
        plt.subplot(2, 4, 3)
        plt.plot(self.food_storage_over_time, label='Food Storage')
        plt.xlabel('Time Step', size = 20)
        plt.ylabel('Food Storage', size = 20)
        # plt.xticks(size = 20)
        plt.yticks(size = 20)
        plt.legend(fontsize = 15)
        plt.title('Food Storage Over Time', size = 20)

        # Plot 4: Average Fertility over time
        plt.subplot(2, 4, 4)
        plt.plot(self.average_fertility_over_time, label='Avg. Fertility')
        plt.xlabel('Time Step', size = 20)
        plt.ylabel('Average Household Fertility', size = 20)
        # plt.xticks(size = 20)
        plt.yticks(size = 20)
        plt.legend(fontsize = 15)
        plt.title('Average Fertility Over Time', size = 20)

        # Plot 5: Average Age over time
        plt.subplot(2, 4, 5)
        plt.plot(self.average_age, label='Avg. Age')
        plt.xlabel('Time Step',size = 20)
        plt.ylabel('Average Age', size = 20)
        # plt.xticks(size = 20)
        plt.yticks(size = 20)
        plt.legend(fontsize = 15)
        plt.title('Average Age Over Time', size = 20)

        # Plot 6: Average Life Span over time
        plt.subplot(2, 4, 6)
        plt.plot(self.average_life_span, label='Avg. Life Span')
        plt.xlabel('Time Step', size = 20)
        plt.ylabel('Average Life Span', size = 20)
        # plt.xticks(size = 20)
        plt.yticks(size = 20)
        plt.legend(fontsize = 15)
        plt.title('Average Life Span Over Time', size = 20)

        plt.subplot(2, 4, 7)
        plt.plot(self.population_accumulation, label='Accumulated Population', color='orange')
        plt.xlabel('Time Step', size=20)
        plt.ylabel('Accumulated Population', size=20)
        plt.yticks(size=20)
        plt.legend()
        plt.title('Accumulated Population', size=20)

        plt.subplot(2, 4, 8)
        plt.plot(self.gini_coefficients)
        plt.xlabel('Time Step', size = 20)
        plt.ylabel('Gini Coefficient', size = 20)
        plt.yticks(size = 20)
        plt.title('Inequality Over Time', size = 20)

        plt.tight_layout()
        plt.savefig(file_name)
        plt.show()
        plt.close()
        # with open(f'networks{self.time}.txt', 'w') as output:
        #     output.write(str(self.networks))
        

    def get_agent_by_id(self, agent_id):
        for household in self.households:
            for agent in household.members:
                if agent.id == agent_id:
                    return agent
        return None

    def propose_marriage(self, household, marriage_from, marriage_to, bride_price_ratio):
        """Handle the marriage proposals and household merging."""
        eligible_agents = [agent for agent in household.members if agent.is_alive and agent.age >= marriage_from and agent.age <= marriage_to and agent.gender == 'female' and agent.marital_status == 'single']
        # print('agent household_id', household.id)
        # print(eligible_agents)
        if not eligible_agents:
            return
        
        combined_network = self.combined_network()
        agent_network = combined_network[household.id]
        # print('\nAgent network:')
        # print(agent_network)
        for agent in eligible_agents:
            # print('Eligible agent {}, household: ({}, {})'.format(agent.id, agent.household_id, household.id))

            potential_spouses = self.find_potential_spouses(agent, marriage_from, marriage_to)
            
            max_connect = 0
            best_agent = None # solve here
            richest_asset = 0
            if potential_spouses:
                for potential in potential_spouses:
                    potential_household = self.get_household_by_id(potential.household_id)
                    potential_asset = potential_household.get_total_food()
                    # print('potential.household_id', potential.household_id)
                    mutual_connection = agent_network['connectivity'][potential.household_id]
                    if mutual_connection > max_connect and potential_asset > richest_asset:
                        max_connect = mutual_connection
                        richest_asset = potential_asset
                        best_agent = potential
                if best_agent:
                    chosen_spouse = best_agent
                    # agent.marry(chosen_spouse) 
                    # print('marry agent ({}, {})'.format(agent.household_id, household.id))
                    self.marry_agents(agent, chosen_spouse, bride_price_ratio)

    def find_potential_spouses(self, agent, marriage_from, marriage_to):
        """Find potential spouses for an agent from other households."""
        potential_spouses = []
        for household in self.households:
            if household.get_total_food() > 100: # need to be able to pay bride price
                for member in household.members:
                    if member.gender != agent.gender and member.household_id != agent.household_id and member.is_alive and marriage_from <= member.age <= marriage_to and member.marital_status == 'single':
                        # print(agent.household_id == member.household_id)
                        # print(agent.household_id, member.household_id)
                        potential_spouses.append(member)
        return potential_spouses
    
    def marry_agents(self, female_agent, male_agent, bride_price_ratio):
        """Handle the marriage process, ensuring the female moves to the male's household."""
        old_household = self.get_household_by_id(female_agent.household_id)
        female_agent.marry(male_agent)
        
        new_household = self.get_household_by_id(male_agent.household_id)
        bride_price = sum(amount for amount, _ in new_household.food_storage) * bride_price_ratio
        male_luxury_goods = new_household.luxury_good_storage
        price_to_pay = bride_price 
        while price_to_pay > 0 and new_household.food_storage: 
            amount, age_added = new_household.food_storage[0]
            if price_to_pay <= amount:
                new_household.food_storage[0] = (amount - price_to_pay, age_added)
                price_to_pay = 0
            else:
                new_household.food_storage.pop(0)
                price_to_pay -= amount
        old_household.luxury_good_storage += male_luxury_goods
        new_household.luxury_good_storage -= male_luxury_goods
        
        old_household.add_food(bride_price - price_to_pay)
        # women move to men's household after marriage.
        new_household.extend(female_agent)
        old_household.remove_member(female_agent)
        
        female_agent.household_id = new_household.id

        # print(f"Marriage: {female_agent.id} (female) moved to {male_agent.id} (male) household {new_household.id}.")
    
    

    def calculate_wealth(self, exchange_rate):
        wealths = [household.get_wealth(exchange_rate) for household in self.households if household in self.households]
        return wealths

    def calculate_gini_coefficient(self, wealths):
        if len(wealths) == 0:
            return None  
        wealths = sorted(wealths)
        n = len(wealths)
        mean_wealth = np.mean(wealths)
        
        if mean_wealth == 0:
            return 0
        
        cumulative_diff_sum = sum([sum([abs(w_i - w_j) for w_j in wealths]) for w_i in wealths])
        gini_coefficient = cumulative_diff_sum / (2 * n**2 * mean_wealth)
        
        return gini_coefficient
    
    def track_inequality_over_time(self, exchange_rate):
        wealths = self.calculate_wealth(exchange_rate)
        gini_coefficient = self.calculate_gini_coefficient(wealths)
        # print('gini', gini_coefficient)
        if gini_coefficient is not None:
            self.gini_coefficients.append(gini_coefficient)
        else:
            self.gini_coefficients.append(0)
    
    
    def update_fallow_land(self, fallow_ratio, fallow_period):
        """Update land plots every year to manage the fallow cycle."""
        if self.time < fallow_period:
            return
        # decide how many lands to fallow
        total_land = len(self.land_types)
        num_lands_to_fallow = max(1, total_land // fallow_ratio)

        #sort lands by quality
        available_lands = [(land_id, land_data) for land_id, land_data in self.land_types.items() if not land_data['fallow']]
        sorted_lands = sorted(available_lands, key=lambda x: x[1]['quality'])  
        
        # select lands to fallow
        lands_to_fallow = [land_id for land_id, _ in sorted_lands[:num_lands_to_fallow]]

        for land_id in lands_to_fallow:
            self.land_types[land_id]['fallow'] = True
            self.land_types[land_id]['fallow_timer'] = fallow_period  # 5 years of fallow period
            # print(f"Land plot {land_id} (quality: {self.land_types[land_id]['quality']}) is now fallow.")
        
            # If the land is occupied, notify the household to migrate
            if self.land_types[land_id]['occupied']:
                self.notify_household_to_migrate(land_id)

        # reduce timers for lands that are already fallow and restore them if the timer expires
        for land_id, land_data in self.land_types.items():
            if land_data['fallow']:
                land_data['fallow_timer'] -= 1
                if land_data['fallow_timer'] <= 0:
                    land_data['fallow'] = False
                    # print(f"Land plot {land_id} is no longer fallow.")
        # print('land types', self.land_types)

    def notify_household_to_migrate(self, land_id):
        """Notify the household occupying the land to migrate."""
        # print(f"Household on land plot {land_id} must migrate because the land is now fallow.")
        
        for household in self.households:
            if household.location == land_id:
                self.migrate_household(household)
                # print(f"{household.id} are forced migrate to another land")
                  # force the household to migrate
                break
