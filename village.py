from household import Household
import matplotlib.pyplot as plt
import pandas as pd
import numpy as np
import matplotlib.cm as cm
from IPython.display import display
import ipywidgets as widgets
import random
import time
from agent import Agent
import statistics
import scipy.special as sp
import scipy.linalg as sl
import warnings
import matplotlib.pyplot as plt
from matplotlib import cm
import copy
import statistics
import time
import matplotlib
warnings.filterwarnings("ignore")

class Village:
    def __init__(self, households, lands, land_by_id, food_expiration_steps, fallow_period, luxury_goods_in_village):
        self.households = households
        self.lands = lands
        self.land_by_id = land_by_id
        self.time = 0
        self.population_over_time = []
        self.land_capacity_over_time = []
        self.land_capacity_over_time_all = []
        self.food_storage_over_time = []
        self.luxury_goods_over_time = []
        self.land_usage_over_time = []
        self.average_fertility_over_time = []
        self.average_life_span = [0]
        self.num_households = []
        self.num_migrated = []
        self.network = {}
        self.network_relation = {}
        self.spare_food = []
        self.luxury_goods_in_village = luxury_goods_in_village # inital values in the village
        self.food_expiration_steps = food_expiration_steps
        self.population = []
        self.num_house = []
        self.average_age = []
        self.gini_coefficients = []
        self.gini_coefficients_food = []
        self.gini_coefficients_luxury = []
        self.networks = []
        self.fallow_cycle = fallow_period
        self.population_accumulation = []
        self.failure_baby = {}
        self.failure_marry = {}
        self.emigrate = {}
        self.male = {}
        self.female = {}
        self.new_born = {}
        self.migrate_priority = []
        self.migrate_counter = 0
        self.tempreture = None
        self.empty_land_ids = None
        self.avg_productivity = 0
        self.avg_prestige = 0

    matplotlib.rcParams.update({'text.usetex': False,
                            'text.latex.preamble': r"\usepackage{amsmath}\usepackage{siunitx}\usepackage{textcomp}\usepackage{gensymb}"})
    matplotlib.rcParams.update({'font.size': 18, 'font.style': 'normal', 'font.family':'serif'})

    def initialize_network(self):
        
        for household in self.households:
            self.network[household.id] = {
                'connectivity': {}
                #,'luxury_goods': household.luxury_good_storage
            }
        
        for household in self.households:
            for other_household in self.households:

                if household != other_household:
                    distance = self.get_distance(household.location, other_household.location)
                    if distance == 0:
                        print(household.id, other_household.id)
                        print(household.location, other_household.location)
                    self.network[household.id]['connectivity'][other_household.id] = 1/distance


    def initialize_network_relationship(self):
        for household in self.households:
            self.network_relation[household.id] = {
                'connectivity': {}
            }
        
        for household in self.households:
            for other_household in self.households:
                if household.id != other_household.id:
                    self.network_relation[household.id]['connectivity'][other_household.id] = 0
    
    

    def combined_network(self, exchange_rate):
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
            self.network_relation[key]['wealth'] = household.get_wealth(exchange_rate)
            self.network_relation[key]['num_member'] = len(household.members)
            result[key] = {'connectivity': merged_conn, 'num_member': len(household.members), 'wealth': household.get_wealth(exchange_rate)} 

        return result

    def update_network_connectivity(self):
        """Updates connectivity based on trading and distance."""

        for household_id in list(self.network.keys()):
            # if household_id in valid_households:
                
            household = self.get_household_by_id(household_id)
            self.network[household.id]['luxury_goods'] = household.luxury_good_storage
            connectivity = self.network[household_id]['connectivity']

            for other_id in list(connectivity.keys()):
                # if other_id in valid_households:
                other_household = self.get_household_by_id(other_id)
                if household.id != other_household.id:
                    distance = self.get_distance(household.location, other_household.location)
                    connectivity[other_id] = 1 / distance
                    
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
        return food_amount - still_need
    
    def manage_luxury_goods(self, exchange_rate, excess_food_ratio, vec1_instance):
        for household in self.households:
            food_storage_needed = sum(vec1_instance.rho[member.get_age_group_index(vec1_instance)] for member in household.members)
            total_available_food = sum(amount for amount, _ in household.food_storage)
            excess_food = total_available_food - excess_food_ratio * food_storage_needed
            
        self.update_spare_food_expiration() #TODO: can move it to the main loop
    
    def update_spare_food_expiration(self):
        current_time = self.time  
        self.spare_food = [(amount, age_added) for amount, age_added in self.spare_food if current_time - age_added < self.food_expiration_steps]


    def trading(self, exchange_rate):
        # determine intentions for each household
        want_trade = {}  #desired resource
        have_trade = {}  # available resource to trade

        for hh in self.households:
            total_food = sum(amount for amount, _ in hh.food_storage)
            total_resources = hh.resources  # dict: stone, obsidian, jade

            # decide what they want
            if hh.prestige < self.avg_prestige and total_resources.get('jade', 0) < 1:
                want_trade[hh] = 'jade'
            elif hh.productivity < self.avg_productivity: # pick tool they have least
                if total_resources.get('obsidian', 0) < 1:
                    want_trade[hh] = 'obsidian'
                else:
                    want_trade[hh] = 'stone'
            else:
                # no urgent need, can still trade food for minor gains
                want_trade[hh] = 'food'

            offer = [] # decide what they have to offer
            if total_food > 1: # they can trade anything they have more than 1 unit
                offer.append('food')
            for r, amt in total_resources.items():
                if amt > 0:
                    offer.append(r)
            have_trade[hh] = offer

        network = self.combined_network(exchange_rate) # combined network for matching

        # matching households
        matched = set()
        for hh in self.households:
            if hh in matched:
                continue
            best_partner = None
            best_connectivity = -1
            desired = want_trade[hh]
            for partner in self.households:
                if partner == hh or partner in matched:
                    continue
                if desired in have_trade[partner]:
                    conn = network[hh.id]['connectivity'][partner.id]
                    if conn > best_connectivity:
                        best_connectivity = conn
                        best_partner = partner
            if best_partner:
                self.execute_trade(hh, best_partner, desired, exchange_rate)
                matched.add(hh)
                matched.add(best_partner)

    def execute_trade(self, requester, partner, resource, exchange_rate):

        # determine how much requester can give in exchange
        if resource != 'food':
            # requester trades food for the resource
            food_available = sum(amount for amount, _ in requester.food_storage) - 1.5 * len(requester.members)
            resource_available = partner.resources.get(resource, 0)
            units_to_trade = min(resource_available, food_available / exchange_rate[resource])

            if units_to_trade > 0:
                
                requester.deduct_food(units_to_trade * exchange_rate[resource]) # deduct food from requester
                requester.resources[resource] = requester.resources.get(resource, 0) + units_to_trade # transfer resource
                partner.resources[resource] -= units_to_trade

        else:
            # requester wants food, trades any available resources
            # pick the first available resource to trade
            trade_resource = None
            for r, amt in partner.resources.items():
                if amt > 0:
                    trade_resource = r
                    break

            if trade_resource:
                resource_available = partner.resources[trade_resource]
                # amount of food requester can get
                food_needed = sum(amount for amount, _ in requester.food_storage) - 1.5 * len(requester.members)
                units_to_trade = min(resource_available, food_needed / exchange_rate[trade_resource])

                if units_to_trade > 0:
                    # deduct resource from partner
                    partner.resources[trade_resource] -= units_to_trade
                    requester.resources[trade_resource] = requester.resources.get(trade_resource, 0) + units_to_trade
                    requester.add_food(units_to_trade * exchange_rate[trade_resource]) # transfer food

        # Update connectivity
        self.network_relation[requester.id]['connectivity'][partner.id] += 1
        self.network_relation[partner.id]['connectivity'][requester.id] += 1


    def get_household_by_id(self, household_id):
        for household in self.households:
            if household.id == household_id:
                return household
        return None
    

    def drop_worst_land(self, household, max_farmland_count):
        """Drop the worst-quality lands until household has at most max_farmland_count farmlands."""

        if len(household.farmlands) <= max_farmland_count:
            print("nothing to drop")
            return  # nothing to drop

        farmland_scores = [] # calculate land quality for each farmland
        for land in household.farmlands:
            # weighted score: soil and water both matter, add another function to calculate this later
            quality = land.soil * 0.7 + land.water * 0.3
            farmland_scores.append((land, quality))

        farmland_scores.sort(key=lambda x: x[1], reverse=True)

        dropped_farmlands = [fid for fid, _ in farmland_scores[max_farmland_count:]]

        for land in dropped_farmlands:
            land.occupied = None
            land.owner = None
            household.farmlands.remove(land)

    def  migrate_household(self, household, storage_ratio_low):
        empty_land_cells = [(cell_id, land_data) for cell_id, land_data in self.land_by_id.items() if land_data.occupied == None]
        
        if empty_land_cells:
            print("migration happened")
            sorted_land_cells = sorted(
                                        empty_land_cells,
                                        key=lambda x: self.get_distance(household.location, x[1].location) - 0.5 * x[1].soil
                                    )
            best_lands = sorted_land_cells[:10]   
            for land_id, _ in best_lands:
                self.land_by_id[land_id].occupied = "farm"
                household.farmlands.append(self.land_by_id[land_id])
            self.drop_worst_land(household, 5)
            migrate_cost = sum(amount for amount, _ in household.food_storage) * storage_ratio_low
            # pay for the migration           
            household.deduct_food(migrate_cost)
            if household.id in self.migrate_priority:
                self.migrate_priority.remove(household.id) # if it was in the priority list, then remove after successfully migrated.
        else:
            if not household.id in self.migrate_priority:
                self.migrate_priority.append(household.id)
            # print(f"Household {household.id} failed moving because there is no more space.")
            pass
    

    def check_migration(self):
        """Return True if there is at least one available (non-fallow, non-occupied) land."""
        return bool(self.empty_land_ids)


    def get_distance(self, location1, location2):
        x1, y1 = location1
        x2, y2 = location2
        return abs(x1 - x2) + abs(y1 - y2)

    def is_land_available(self):
        return any(not data.occupied and not data.fallow for data in self.land_by_id.values())


    def find_closest_kind(self, household):
        if household.spouses:
            return household.spouses[-1]
        elif household.parents:
            return household.parents[-1]
        else:
            return None
                
    def remove_empty_household(self):
        empty_households = [h for h in self.households if len(h.members) == 0]
        for household in empty_households:
            for i in household.farmlands:
                i.owner = None
                i.occupied = None
            household.farmlands = []
            print(f"Household {household.id} is empty.")
            self.remove_household(household)
            if household.id in self.migrate_priority:
                self.migrate_priority.remove(household.id)

    def remove_household(self, household):
        kin = self.find_closest_kind(household)
        if kin:
            # print("found kin")
            for r in household.resources:
                kin.resources[r] += household.resources[r]
            kin.food_storage.extend(household.food_storage)

        if household.food_storage:
            self.spare_food.extend(household.food_storage)
        household.home.occupied = None # free up land. Here I changed the location to id.
        household.home.owner = None
        self.households = [h for h in self.households if h != household] # remove from households

        if household.id in self.network: # remove from network
            del self.network[household.id]
        for c in self.network.values():
            c['connectivity'].pop(household.id, None)

        if household.id in self.network_relation: # remove from network relations
            del self.network_relation[household.id]
        for c in self.network_relation.values():
            c['connectivity'].pop(household.id, None)

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
            # total_food += amount_get
            # print(f"Household {household.id} gets {amount_get} from the Village.")

    def get_neighbors(self, household, distance=50): # todo: put distance to parameter
        hx, hy = household.location
        neighbors = []
        for other in self.households:
            if other is household:
                continue
            ox, oy = other.location
            if ((hx - ox)**2 + (hy - oy)**2)**0.5 <= distance:
                neighbors.append(other)
        return neighbors


    def run_simulation_step(self, vec1_instance, prod_multiplier, fishing_discount, fallow_period, food_expiration_steps, marriage_from, marriage_to, bride_price_ratio, exchange_rate, storage_ratio_low, storage_ratio_high, land_capacity_low, max_member, excess_food_ratio, trade_back_start, lux_per_year, land_depreciate_factor, fertility_scaler, work_scale, conditions, prob_emigrate, bride_price, farming_counter_max, climate, emigrate_enabled = False, spare_food_enabled=False, fallow_farming = False, trading_enabled = False):
        """Run a single simulation step (year) with timing diagnostics."""

        print(f"\nSimulation Year {self.time}")
        
        start_total = time.perf_counter()
        timings = {}
        self.empty_land_ids = {
                lid for lid, land in self.land_by_id.items() if not land.occupied and not land.fallow
            }
        #  1. update connectivity 
        t0 = time.perf_counter()
        self.update_network_connectivity()
        timings['update_network_connectivity'] = time.perf_counter() - t0

        longevities = []
        self.population_accumulation.append(self.population_accumulation[-1])


        #  2. yearly tracking 
        t0 = time.perf_counter()
        if self.time not in self.failure_baby:
            self.failure_baby[self.time] = {'fertility': 0, 'gender': 0, 'marriage': 0, 'land': 0, 'household': 0}
        if self.time not in self.failure_marry:
            self.failure_marry[self.time] = 0
        if self.time not in self.emigrate:
            self.emigrate[self.time] = 0
        if self.time not in self.male:
            male_count = sum(1 for household in self.households for member in household.members if member.gender == 'male')
            self.male[self.time] = male_count
        if self.time not in self.female:
            female_count = sum(1 for household in self.households for member in household.members if member.gender == 'female')
            self.female[self.time] = female_count
        if self.time not in self.new_born:
            self.new_born[self.time] = 0
        timings['init_tracking'] = time.perf_counter() - t0
        if self.time == 1:
            if any(land.owner is None and land.occupied for land in self.lands):
                print("Found unowned land! Step 3")


        #  3. household loop 
        t0 = time.perf_counter()
        total_new_born = 0
        households = self.households[:]
        random.shuffle(households)
        
        for household in households:

            total_food_needed_standard = sum(vec1_instance.rho[agent.get_age_group_index(vec1_instance)] for agent in household.members)
            hh_start = time.perf_counter()
            household.produce_food(self, vec1_instance, prod_multiplier, fishing_discount, work_scale, climate, total_food_needed_standard)
            neighbors = self.get_neighbors(household)
            if neighbors:
                household.discover_resource(vec1_instance, work_scale, neighbors) # jade, stone, obsidian

            dead_agents = []
            newborn_agents = []

            total_food = sum(x for x, _ in household.food_storage)
            total_food_needed = sum(vec1_instance.rho[agent.get_age_group_index(vec1_instance)] for agent in household.members)
            total_food_needed_standard = total_food_needed

            if spare_food_enabled:
                self.take_spare_food_for_poor(household, total_food, total_food_needed)

            total_food = sum(x for x, _ in household.food_storage)
            
            for agent in household.members:
                age_index = agent.get_age_group_index(vec1_instance)
                self.productivity = vec1_instance.phi[age_index]
                agent_food_needed = vec1_instance.rho[age_index]
                z = total_food * agent_food_needed / total_food_needed
                agent.age_survive_reproduce(household, self, z, max_member, fertility_scaler, vec1_instance, conditions)
                
                if not agent.is_alive:
                    dead_agents.append(agent)
                    # print(f"one agent from house {household.id} died.")
                else:
                    if agent.newborn_agents:
                        # print(f"Newborn: one agent from house {household.id}.")
                        newborn_agents.extend(agent.newborn_agents)
                        agent.newborn_agents = []

            total_new_born += len(newborn_agents)
            self.new_born[self.time] = total_new_born
            self.population_accumulation[-1] += len(newborn_agents)

            for agent in dead_agents:
                longevities.append(agent.age)
                household.remove_member(agent)

            for child in newborn_agents:
                household.extend(child)

            household.food_storage.sort(key=lambda x: x[1])
            household.update_food_storage()
            if household.food_storage:
                household.remove_food(total_food_needed)

            hh_duration = time.perf_counter() - hh_start
            if 'per_household' not in timings:
                timings['per_household'] = []
            timings['per_household'].append(hh_duration)

        timings['household_loop'] = time.perf_counter() - t0
        # if self.time == 1:
        #     if any(land.owner is None and land.occupied for land in self.lands):
        #         print("Found unowned land! Step 4")

        #  4. remove empty households 
        t0 = time.perf_counter()
        self.remove_empty_household()
        timings['remove_empty_household'] = time.perf_counter() - t0

        #  5. average life span 
        t0 = time.perf_counter()
        if longevities:
            self.average_life_span.append(sum(longevities) / len(longevities))
        else:
            self.average_life_span.append(self.average_life_span[-1])
        timings['life_span_update'] = time.perf_counter() - t0

        #  6. migration 
        t0 = time.perf_counter()
        # print("self.migrate_priority", self.migrate_priority) #TODO find out why not in priority. Is it only because still empty lands? Perhaps need to track the migration activities
        for hh_id in self.migrate_priority:
            hh = self.get_household_by_id(hh_id)
            self.migrate_household(hh, storage_ratio_low)
        timings['migrate_priority'] = time.perf_counter() - t0


        # 7. split and emigrate 
        t0 = time.perf_counter()
        for household in households:
            total_food_needed = sum(vec1_instance.rho[member.get_age_group_index(vec1_instance)] for member in household.members)
            # land_quality = self.land_by_id[household.id].soil
            if household.farmlands:
                land_quality = sum(land.soil for land in household.farmlands) / len(household.farmlands)
            else:
                land_quality = 0
            print("land quality", land_quality)
            total_food_storage = sum(amount for amount, _ in household.food_storage)

            # if total_food_storage < storage_ratio_high * total_food_needed and total_food_storage > storage_ratio_low * total_food_needed and land_quality < land_capacity_low:
            if land_quality < land_capacity_low:
                self.migrate_household(household, storage_ratio_low)

            if len(household.members) > max_member:
                if emigrate_enabled and random.random() < prob_emigrate:
                    household.emigrate(self, food_expiration_steps)
                else:
                    household.split_household(self, food_expiration_steps)

            household.advance_step()
        timings['post_household_actions'] = time.perf_counter() - t0

        #  8. marraige 
        t0 = time.perf_counter()
        for household in households:
            self.propose_marriage(household, marriage_from, marriage_to, bride_price_ratio, bride_price, exchange_rate)
            household.advance_step()
        self.remove_empty_household()
        timings['marriage'] = time.perf_counter() - t0

        #  9. updates and tracking 
        t0 = time.perf_counter()
        self.update_tracking_variables(exchange_rate)
        self.track_land_usage()
        self.update_land_capacity(land_depreciate_factor)
        timings['updates'] = time.perf_counter() - t0

        #  10. trading and fallow land 
        t0 = time.perf_counter()
        trade_timings = {}

        if trading_enabled:
            t1 = time.perf_counter()
            self.manage_luxury_goods(exchange_rate, excess_food_ratio, vec1_instance)
            trade_timings['manage_luxury_goods'] = time.perf_counter() - t1

            t2 = time.perf_counter()
            # self.trading(excess_food_ratio, trade_back_start, exchange_rate, vec1_instance)
            self.trading(exchange_rate)
            trade_timings['trading'] = time.perf_counter() - t2

        if fallow_farming:
            t3 = time.perf_counter()
            self.update_fallow_land(fallow_period, storage_ratio_low, farming_counter_max)
            trade_timings['update_fallow_land'] = time.perf_counter() - t3

        timings['trade_fallow'] = time.perf_counter() - t0
        timings.update(trade_timings)

        #  11. 
        t0 = time.perf_counter()
        self.update_network_connectivity()
        self.time += 1
        self.luxury_goods_in_village += lux_per_year
        timings['final_wrapup'] = time.perf_counter() - t0
        

        total_time = time.perf_counter() - start_total
        timings['total'] = total_time
        

        # print("\n running time summary ")
        # for k, v in timings.items():
        #     if isinstance(v, list):
        #         print(f"{k:25s}: avg {sum(v)/len(v):.4f}s over {len(v)} households")
        #     else:
        #         print(f"{k:25s}: {v:.4f}s")
        # print("--")

        if self.households:
            self.avg_productivity = sum(h.productivity for h in self.households) / len(self.households)
            self.avg_prestige = sum(h.prestige for h in self.households) / len(self.households)
        else:
            self.avg_productivity = 0
            self.avg_prestige = 0
        return timings
            
        
    def update_land_capacity(self, land_depreciate_factor):
        """Update the land quality for each land cell in the village."""
        for location, land in self.land_by_id.items():
            land_quality = land.soil
            land_max_capacity = land.max_capacity
            land_recovery_rate = land.recovery_rate
            farming_intensity = land.farming_intensity    

            new_quality = (
                        land_quality +
                        land_recovery_rate * (land_max_capacity - land_quality) 
                        - farming_intensity * land_quality * land_depreciate_factor # 0.01 # this 0.01 is an important factor that influence everything, can be changed
                    )
            land.soil = max(0, min(new_quality, land_max_capacity))
            # print(f"Land at {location} updated to quality {land['quality']:.2f}.")
    
    
    def track_land_usage(self):
        """Track the land usage and quality over time."""
        land_snapshot = {}

        for loc, land_data in self.land_by_id.items():
            # make a deep copy so later modifications won't affect this snapshot
            land_snapshot[loc] = {'land': copy.deepcopy(land_data)}

        self.land_usage_over_time.append(land_snapshot)

        #  tracking population stats 
        self.population.append(sum(len(household.members) for household in self.households))
        self.num_house.append(len(self.households))

        all_ages = [member.age for household in self.households for member in household.members]
        self.average_age.append(statistics.mean(all_ages) if all_ages else 0)

    

    def update_tracking_variables(self, exchange_rate):
        population = sum(len(household.members) for household in self.households)
        # print("population", population)
        land_capcity_all = sum(self.land_by_id[key].soil for key in self.land_by_id)
        land_capacity = sum(self.land_by_id[key].soil for key in self.land_by_id if self.land_by_id[key].occupied == "farm")
        amount_used = len([self.land_by_id[key].soil for key in self.land_by_id if self.land_by_id[key].occupied == "farm"])

        total_food = sum(
        sum(amount for amount, _ in household.food_storage)  # Sum the amounts in each tuple
        for household in self.households)

        weights = {"stone": 0.1, "obsidian": 0.3, "jade": 1.0}
        total_luxury = sum(
            sum(household.resources[r] * weights[r] for r in household.resources)
            for household in self.households
        )

        self.population_over_time.append(population)
        self.land_capacity_over_time.append(land_capacity)
        self.food_storage_over_time.append(total_food)
        self.luxury_goods_over_time.append(total_luxury)
        self.land_capacity_over_time_all.append(land_capcity_all)
        self.track_inequality_over_time(exchange_rate)
        self.networks.append(self.combined_network(exchange_rate))
        self.num_households.append(len(self.households))
        self.num_migrated.append(self.migrate_counter)
        house_num = sum(len(household.members) for household in self.households)
        if house_num != 0:
            self.average_fertility_over_time.append(
                sum(member.fertility for household in self.households for member in household.members) / 
                house_num
            )
        else:self.average_fertility_over_time.append(0)


    def get_eigen_value(self, vec1_instance):
            p0 = vec1_instance.pstar.values  # survival probabilities
            m0 = vec1_instance.mstar.values  # fertility rates
            N = len(p0)  # number of age groups
            m1 = np.zeros((N, N))  # initialize N x N matrix
            m1[0, :] = m0  # set fertility rates in the first row

            for i in range(N - 1):
                m1[i + 1, i] = p0[i]  # set survival probabilities in sub-diagonal

            eigvals, eigvecs = sl.eig(m1)  # sompute eigenvalues and eigenvectors
            lambda_max = np.max(eigvals.real)  # sargest eigenvalue (real part)
            return str(round(lambda_max, 2))
    

    

    def get_agent_by_id(self, agent_id):
        for household in self.households:
            for agent in household.members:
                if agent.id == agent_id:
                    return agent
        return None

    def propose_marriage(self, household, marriage_from, marriage_to, bride_price_ratio, bride_price, exchange_rate):
        """Handle the marriage proposals and household merging."""
        eligible_agents = [agent for agent in household.members if agent.is_alive and agent.age >= marriage_from and agent.age <= marriage_to and agent.gender == 'female' and agent.marital_status == 'single']

        if not eligible_agents:
            return
        
        combined_network = self.combined_network(exchange_rate)
        agent_network = combined_network[household.id]
        # print('\nAgent network:')
        # print(agent_network)
        for agent in eligible_agents:
            # print('Eligible agent {}, household: ({}, {})'.format(agent.id, agent.household_id, household.id))
            potential_spouses = self.find_potential_spouses(agent, marriage_from, marriage_to, bride_price)
            
            max_connect = 0
            best_agent = None 
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
                    
                    self.marry_agents(agent, chosen_spouse, bride_price_ratio)
                else:
                    self.failure_marry[self.time] += 1
            else:
                self.failure_marry[self.time] += 1

    def find_potential_spouses(self, agent, marriage_from, marriage_to, bride_price):
        """Find potential spouses for an agent from other households."""
        potential_spouses = []
        for household in self.households:
            if household.get_total_food() > bride_price: # need to be able to pay bride price #TODO: add to parameter
                for member in household.members:
                    if member.gender != agent.gender and member.household_id != agent.household_id and member.is_alive and  member.age >= marriage_from  and member.age <= marriage_to and member.marital_status == 'single':
                        
                        potential_spouses.append(member)
        return potential_spouses
    
    def marry_agents(self, female_agent, male_agent, bride_price_ratio): # admin process. not condition check
        old_household = self.get_household_by_id(female_agent.household_id)
        female_agent.marry(male_agent) # change the agent state
        
        new_household = self.get_household_by_id(male_agent.household_id)
        bride_price = sum(amount for amount, _ in new_household.food_storage) * bride_price_ratio
        male_luxury_goods = new_household.luxury_good_storage / 2
        price_to_pay = bride_price 
        new_household.deduct_food(bride_price)
        old_household.add_food(bride_price - price_to_pay)

        old_household.luxury_good_storage += male_luxury_goods
        new_household.luxury_good_storage -= male_luxury_goods
        
        # women move to men's household after marriage.
        new_household.extend(female_agent)
        old_household.remove_member(female_agent)
        female_agent.household_id = new_household.id
        old_household.spouses.append(new_household)
        new_household.spouses.append(old_household) # track for kin

        # print(f"Marriage: {female_agent.id} (female) moved to {male_agent.id} (male) household {new_household.id}.")
    
    def calculate_wealth(self, exchange_rate):
        wealths = [household.get_wealth(exchange_rate) for household in self.households if household in self.households]
        return wealths
    

    def calculate_food(self):
        food = [household.get_total_food() for household in self.households if household in self.households]
        return food
    
    def calculate_luxury(self):
        luxury = [household.get_luxury() for household in self.households if household in self.households]
        return luxury

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
        food = self.calculate_food()
        luxury = self.calculate_luxury()
        gini_coefficient = self.calculate_gini_coefficient(wealths)
        gini_coefficient_food = self.calculate_gini_coefficient(food)
        gini_coefficient_lxury = self.calculate_gini_coefficient(luxury)
        
        if gini_coefficient is not None:
            self.gini_coefficients.append(gini_coefficient)
        else:
            self.gini_coefficients.append(0)
        
        if gini_coefficient_food is not None:
            self.gini_coefficients_food.append(gini_coefficient_food)
        else:
            self.gini_coefficients_food.append(0)
        
        if gini_coefficient_lxury is not None:
            self.gini_coefficients_luxury.append(gini_coefficient_lxury)
        else:
            self.gini_coefficients_luxury.append(0)
    

    def notify_household_to_migrate(self, land_id, storage_ratio_low):
        """Notify the household occupying the land to migrate."""
        # print(f"Household on land plot {land_id} must migrate because the land is now fallow.")
        
        for household in self.households:
            if household.location == land_id:
                self.migrate_household(household, storage_ratio_low)
                self.migrate_counter += 1 # record how many people migrated
                  # force the household to migrate
                break

    

    def update_fallow_land(self, fallow_period, storage_ratio_low, farming_counter_max):

        start_total = time.perf_counter()
        timings = {}

        if self.time < fallow_period:
            return {"skipped": True}

        land_by_id = self.land_by_id
        check_migration = self.check_migration
        notify_migrate = self.notify_household_to_migrate

        t0 = time.perf_counter()

        if not hasattr(self, "_lands_with_high_counter"):
            self._lands_with_high_counter = set()

        # add new candidates that might exceed threshold
        # instead of scanning all, use previously stored active ones if possible
        new_candidates = []
        for land_id, land_data in land_by_id.items():
            if (not land_data.fallow) and (land_data.farming_counter >= farming_counter_max):
                new_candidates.append((land_id, land_data))
                self._lands_with_high_counter.add(land_id)

        timings["select_lands"] = time.perf_counter() - t0

        t1 = time.perf_counter()
        count_fallow = count_migrate = 0

        check_time = notify_time = attr_time = 0.0

        for land_id, land_data in new_candidates:
            tcheck = time.perf_counter()
            migrate_ok = check_migration()
            check_time += time.perf_counter() - tcheck

            if migrate_ok:
                tattr = time.perf_counter()
                land_data.fallow = True
                land_data.fallow_timer = fallow_period
                land_data.farming_counter = 0
                attr_time += time.perf_counter() - tattr

                if land_data.occupied:
                    tnotify = time.perf_counter()
                    notify_migrate(land_id, storage_ratio_low)
                    notify_time += time.perf_counter() - tnotify
                    count_migrate += 1
            else:
                tnotify = time.perf_counter()
                notify_migrate(land_id, storage_ratio_low)
                notify_time += time.perf_counter() - tnotify
                count_migrate += 1
                count_fallow += 1

        timings["apply_fallow"] = time.perf_counter() - t1
        timings["check_migration_calls"] = check_time
        timings["notify_migrate_calls"] = notify_time
        timings["attr_update"] = attr_time
        timings["apply_fallow_candidates"] = len(new_candidates)

        # print(f"[apply_fallow] {len(new_candidates)} lands → "
        #     f"check={check_time:.3f}s, notify={notify_time:.3f}s, attr={attr_time:.3f}s, total={timings['apply_fallow']:.3f}s")

        t2 = time.perf_counter()

        possible_fallow_ids = [
            land_id for land_id in self._lands_with_high_counter
            if land_id in land_by_id
        ]
        expired_fallow = []

        for land_id in possible_fallow_ids:
            land_data = land_by_id[land_id]
            if land_data.fallow:
                land_data.fallow_timer -= 1
                if land_data.fallow_timer <= 0:
                    land_data.fallow = False
                    expired_fallow.append(land_id)

        # remove expired entries from the “active” list
        for lid in expired_fallow:
            self._lands_with_high_counter.discard(lid)

        timings["update_fallow_timers"] = time.perf_counter() - t2
        timings["total"] = time.perf_counter() - start_total

        # print(
        #     f"[update_fallow_land] Year {self.time}: "
        #     f"select={timings['select_lands']:.4f}s, "
        #     f"apply={timings['apply_fallow']:.4f}s, "
        #     f"timers={timings['update_fallow_timers']:.4f}s, "
        #     f"total={timings['total']:.4f}s"
        # )

        return timings