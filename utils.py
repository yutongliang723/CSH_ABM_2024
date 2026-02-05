import random
from agent import Agent
from household import Household
from village import Village
from clock import Clock
from land import Land
from vec import Vec1
import scipy.special as sp
import math
import uuid
import time
import warnings
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.animation as animation
from PIL import Image, ImageFont, ImageDraw
warnings.filterwarnings("ignore")

# random.seed(10)
def generate_random_agent(household_id, vec1_instance):
    m0 = vec1_instance.mstar * sp.gdtr(1.0 / vec1_instance.fertscale, vec1_instance.fertparm, 1)
    age = random.randint(1, 20)
    gender = random.choice(['male', 'female'])
    fertility = m0[age]
    age_index = min(age, len(vec1_instance.phi) - 1)
    productivity = vec1_instance.phi[age_index]
    agent = Agent(age, gender, household_id, fertility, productivity)
    agent.productivity = productivity
    return agent

def generate_random_household(num_members, location, home, farmlands, vec1_instance, food_expiration_steps, resources, clock, fish):
    new_household = Household([], location, home, resources, food_expiration_steps, clock, fish)
    new_household.farmlands = farmlands
    new_household.members = [generate_random_agent(new_household.id, vec1_instance) for _ in range(num_members)]
    return new_household


def generate_random_village(
    num_households,
    num_land_cells,
    vec1_instance,
    food_expiration_steps,
    land_recovery_rate,
    land_max_capacity,
    fallow_period,
    resources,
    clock,
    fish
    ):
    
    grid_size = math.ceil(math.sqrt(num_land_cells))
    print(f"   Grid size = {grid_size}")

    lands = []
    land_by_id = {}
    for land_id in range(num_land_cells):
        land = Land(
            index=land_id,
            grid_size=grid_size,
            max_capacity=land_max_capacity,
            recovery_rate=land_recovery_rate
        )
        lands.append(land)
        land_by_id[land_id] = land

    print("Land cells generated.")

    households = []
    new_village = Village(
        households=households,
        lands=lands,                   # changed from land_types
        land_by_id=land_by_id,         # new fast lookup
        food_expiration_steps=food_expiration_steps,
        fallow_period=fallow_period,
        clock = Clock()
    )

    new_village.population_accumulation.append(0)
    print("Village object created.")
    print(f"Allocating {num_households} households...")
    available_lands = lands
    random.shuffle(available_lands)

    if len(available_lands) < num_households:
        print(f"Only {len(available_lands)} available plots for {num_households} households.")
        num_households = len(available_lands)

    # allocate households
    for i in range(num_households):
        if not available_lands:
            break
        
        home_land = available_lands.pop() # in the future add more functions to choose the home land
        home_land.occupied = "house"
        location = home_land.location
        home = home_land
        
        # allocate farmland
        start = time.perf_counter()
        farmlands = allocate_household_land(
            home_location=location,
            num_farm_pixels=50,
            land_by_id=land_by_id,   # can pass dict of land_id → Land
            weights=None
        )

        household = generate_random_household(
            random.randint(1, 5),
            location,
            home, #home_id
            farmlands,
            vec1_instance,
            food_expiration_steps,
            resources,
            clock,
            fish
        )
        
        for land_c in household.farmlands:
            land_c.owner = household.id
            land_c.occupied = "farm"
            
        home_land.owner = household.id
        home_land.occupied = "house"
        households.append(household)
        
        new_village.population_accumulation[0] += len(household.members)
    
    print("All households allocated.")
    new_village.lands = lands
    new_village.land_by_id = land_by_id
    new_village.households = households
    print("villlage household", [hs.id for hs in households])
    return new_village


def print_village_summary(village):
    print(f"Village has {len(village.households)} households.")
    
    for household in village.households:
        land = village.land_types[household.location]
        land_quality = land['quality']
        print(f"Household ID: {household.id}, Location: {household.location}, Land Quality: {land_quality}")
        food = sum(amount for amount, _ in household.food_storage)
        need = sum(member.vec1_instance.rho[member.get_age_group_index()] for member in household.members)
        print(f"  Food Storage: {food}, Luxury Good Storage: {household.luxury_good_storage}, Needs: {need}")
        print(f"Household ID: {household.members}, Location: {household.location}, Land Quality: {household.land_quality}")
        
        if household.members:
            print(f"  Members:")
            for member in household.members:

                print(f"    Agent - Age: {member.age}, Gender: {member.gender}, Alive: {member.is_alive}, Fertility Prob: {member.fertility}， Marital Status: {member.marital_status}")
                pass
        else:
            print(f"  No members in this household.")



def land_score(cell, home_location, allocated_cells=None, weights=None):
    """
    Compute a score for a land pixel for allocation to a household.
    allocated_cells: list of already allocated land pixels for this household
    """
    if weights is None:
        weights = {
            'distance_home': 1.0,   # distance to home
            'distance_cluster': 2.0,  # distance to existing allocated pixels
            'quality': 2.0,
            'water': 2.0,
            'max_capacity': 1.0,
            'recovery_rate': 1.0
        }
    
    # distance to home
    distance_home = math.sqrt((cell.location[0]-home_location[0])**2 + (cell.location[1]-home_location[1])**2)
    distance_home_score = 1 / (1 + distance_home)

    # distance to existing allocated pixels (cluster factor)
    if allocated_cells:
        distances = [math.sqrt((cell.location[0]-loc[0])**2 + (cell.location[1]-loc[1])**2) 
                     for loc in allocated_cells]
        min_distance = min(distances)
        distance_cluster_score = 1 / (1 + min_distance)
    else:
        distance_cluster_score = 0  # no cluster yet

    # resource factors
    water_score = 1 if cell.water else 0
    quality_score = cell.soil
    max_cap_score = cell.max_capacity
    recovery_score = cell.recovery_rate

    # weighted sum
    score = (weights['distance_home'] * distance_home_score +
             weights['distance_cluster'] * distance_cluster_score +
             weights['quality'] * quality_score +
             weights['water'] * water_score +
             weights['max_capacity'] * max_cap_score +
             weights['recovery_rate'] * recovery_score)
    
    return score


def allocate_household_land(
    home_location,
    land_by_id,
    weights=None,
    num_farm_pixels=100,
):
    if weights is None:
        weights = {
            "distance_home": 1.0,
            "distance_cluster": 2.0,
            "quality": 2.0,
            "water": 2.0,
            "max_capacity": 1.0,
            "recovery_rate": 1.0,
        }

    # 1. extract free cells 
    free_cells = [cell for cell in land_by_id.values() if cell.occupied is None]
    if not free_cells:
        return []

    n = len(free_cells)
    free_locs = np.array([cell.location for cell in free_cells], dtype=float)
    water = np.array([1 if c.water else 0 for c in free_cells], dtype=float)
    quality = np.array([c.soil for c in free_cells], dtype=float)
    max_cap = np.array([c.max_capacity for c in free_cells], dtype=float)
    recovery = np.array([c.recovery_rate for c in free_cells], dtype=float)

    # 2. compute static suitability score 
    dx = free_locs[:, 0] - home_location[0]
    dy = free_locs[:, 1] - home_location[1]
    dist_home = np.sqrt(dx**2 + dy**2)
    dist_home_score = 1 / (1 + dist_home)  # closer = better

    static_score = (
        weights["distance_home"] * dist_home_score
        + weights["quality"] * quality
        + weights["water"] * water
        + weights["max_capacity"] * max_cap
        + weights["recovery_rate"] * recovery
    )

    #  3. iteratively allocate nearby land 
    allocated = []
    free_mask = np.ones(n, dtype=bool)
    cluster_bonus = np.zeros(n, dtype=float)

    for _ in range(num_farm_pixels):
        combined_score = np.where(
            free_mask,
            static_score + weights["distance_cluster"] * cluster_bonus,
            -np.inf,
        )

        idx = np.argmax(combined_score)
        if not np.isfinite(combined_score[idx]):
            break  # no valid free cell left

        best_cell = free_cells[idx]
        allocated.append(best_cell)

        # mark as occupied (updates global land_by_id immediately)
        # mark in mask so we skip it later
        free_mask[idx] = False

        # update clustering effect around this new farm - neighboring effects
        if len(allocated) < num_farm_pixels:
            bx, by = best_cell.location
            dx = free_locs[:, 0] - bx
            dy = free_locs[:, 1] - by
            dist = np.sqrt(dx**2 + dy**2)
            cluster_bonus = np.where(free_mask, 1 / (1 + dist), -np.inf)
    # print("allocated", len(allocated))
    return allocated


def plot_simulation_results_second(self, file_name_second):
        
    plt.figure(figsize=(18, 4))
    # plt.subplot(2, 3, 1)
    time_steps = list(range(self.clock.step))
    # print("time_steps", time_steps)

    plt.subplot(1, 3, 1)
    emigrate_counts = [self.emigrate[t] for t in time_steps]
    plt.plot(time_steps, emigrate_counts, marker='o')
    plt.xlabel('Time Step', size = 20)
    plt.ylabel('Emigrants', size = 20)
    plt.yticks(size = 20)
    plt.title('Emigrants Over Time', size = 20)
    # plt.legend(fontsize=15)

    plt.subplot(1, 3, 2)
    male_counts = [self.male[t] for t in time_steps]
    female_counts = [self.female[t] for t in time_steps]
    plt.plot(time_steps, male_counts, color = 'blue', label='Male')
    plt.plot(time_steps, female_counts, color = 'red', label='Female')
    plt.xlabel('Time Step', size = 20)
    plt.ylabel('Count', size = 20)
    plt.yticks(size = 20)
    plt.title('Gender Distribution Over Time', size = 20)
    plt.legend(fontsize=15)

    new_born_all = [self.new_born[t] for t in time_steps]
    print("new_born_all", new_born_all)
    plt.subplot(1, 3, 3)
    plt.plot(time_steps,new_born_all)
    plt.xlabel('Time Step', size = 20)
    plt.ylabel('Count', size = 20)
    plt.yticks(size = 20)
    plt.title('New Born Over Time', size = 20)
    
    plt.tight_layout()
    # plt.show()
    plt.savefig(file_name_second, format='svg')
    

def plot_simulation_results(self, file_name):
    plt.figure(figsize=(18, 12))

    # Plot 1: Population over time
    plt.subplot(3, 3, 1)
    plt.plot(self.population_over_time, label='Population')
    plt.xlabel('Time Step', size = 20)
    plt.ylabel('Population', size = 20)
    plt.yticks(size = 20)
    plt.title('Population Over Time',size = 20)

    # Plot 2: Land Capacity over time
    plt.subplot(3, 3, 2)
    plt.plot(self.land_capacity_over_time, label='Occupied Land Capacity')
    plt.plot(self.land_capacity_over_time_all, label='All Land Capacity', linestyle='--')
    plt.xlabel('Time Step', size = 20)
    plt.ylabel('Land Capacity', size = 20)
    plt.yticks(size = 20)
    plt.legend(fontsize = 15)
    plt.title('Land Capacity Over Time', size = 20)

    # Plot 3: Food Storage over time
    plt.subplot(3, 3, 3)
    plt.plot(self.food_storage_over_time, label='Food Storage')
    plt.xlabel('Time Step', size = 20)
    plt.ylabel('Food Storage', size = 20)
    plt.yticks(size = 20)
    plt.title('Food Storage Over Time', size = 20)

    plt.subplot(3, 3, 4)
    plt.plot(self.luxury_goods_over_time, label='Luxury Goods')
    plt.xlabel('Time Step', size = 20)
    plt.ylabel('Food Storage', size = 20)
    plt.yticks(size = 20)
    plt.legend(fontsize = 15)
    plt.title('Luxury Goods Over Time', size = 20)


    # Plot 4: Average Fertility over time
    plt.subplot(3, 3, 5)
    plt.plot(self.average_fertility_over_time, label='Avg. Fertility')
    plt.xlabel('Time Step', size = 20)
    plt.ylabel('Average Household Fertility', size = 20)
    plt.yticks(size = 20)
    plt.legend(fontsize = 15)
    plt.title('Average Fertility Over Time', size = 20)

    # Plot 5: Average Age over time
    plt.subplot(3, 3, 6)
    plt.plot(self.average_age, label='Avg. Age')
    plt.xlabel('Time Step',size = 20)
    plt.ylabel('Average Age', size = 20)
    # plt.xticks(size = 20)
    plt.yticks(size = 20)
    # plt.legend(fontsize = 15)
    plt.title('Average Age Over Time', size = 20)

    # Plot 6: Average Life Span over time
    plt.subplot(3, 3, 7)
    plt.plot(self.average_life_span, label='Avg. Life Span')
    plt.xlabel('Time Step', size = 20)
    plt.ylabel('Average Life Span', size = 20)
    plt.yticks(size = 20)
    plt.title('Average Life Span Over Time', size = 20)

    plt.subplot(3, 3, 8)
    plt.plot(self.population_accumulation, label='Accumulated Population', color='orange')
    plt.xlabel('Time Step', size=20)
    plt.ylabel('Accumulated Population', size=20)
    plt.yticks(size=20)
    plt.title('Accumulated Population', size=20)

    plt.subplot(3, 3, 9)
    plt.plot(self.gini_coefficients, color = 'blue',label = "Total Gini")
    plt.plot(self.gini_coefficients_food, color = 'green',label = "Food Gini")
    plt.plot(self.gini_coefficients_luxury, color = 'orange',label = "Luxury Gini")
    plt.xlabel('Time Step', size = 20)
    plt.ylabel('Gini Coefficient', size = 20)
    plt.yticks(size = 20)
    plt.legend(fontsize = 15)
    plt.title('Inequality Over Time', size = 20)
    plt.tight_layout()
    plt.savefig(file_name, format='svg')

def generate_animation(self, file_path, grid_dim):
        if not self.land_usage_over_time:
            print("No land usage data available.")
            return

        cell_size = 7
        image_size = grid_dim * cell_size

        try:
            font = ImageFont.truetype("arial.ttf", 10)
        except IOError:
            font = ImageFont.load_default()

        frames = []

        # assign consistent random colors to each household
        all_household_ids = set()
        for year_data in self.land_usage_over_time:
            for land_data in year_data.values():
                land = land_data["land"]
                if land.owner is not None:
                    all_household_ids.add(land.owner)

        # build colors for all ever-existing households
        house_colors = {}
        for h_id in all_household_ids:
            random.seed(h_id)  # consistent color across runs
            house_colors[h_id] = tuple(np.random.randint(50, 255, size=3))

        for year, year_data in enumerate(self.land_usage_over_time):
            orphaned_hs = []
            print(f"Rendering year {year + 1}/{len(self.land_usage_over_time)}...")

            img_array = np.zeros((grid_dim, grid_dim, 3), dtype=np.uint8)

            # fill land colors
            for _, land_data in year_data.items():
                
                land = land_data["land"]
                x, y = land.location
                owner_id = getattr(land, "owner", None)
                if land.occupied == "house":
                    color = (139, 69, 19)
                elif land.occupied == "farm":
                    color = house_colors.get(owner_id, (180, 180, 180)) ## ISSUES
                    if color == (180, 180, 180) and owner_id not in [hs.id for hs in self.households]:
                        orphaned_hs.append(owner_id)
                        print("this household not in self.housholds", owner_id)
                else:
                    color = (220, 220, 220)  # empty
                img_array[y, x] = color

            # Create image
            img = Image.fromarray(img_array, mode="RGB").resize(
                (image_size, image_size), resample=Image.NEAREST
            )
            draw = ImageDraw.Draw(img)

            # draw grid
            line_color = (150, 150, 150)
            for x in range(0, image_size, cell_size):
                draw.line([(x, 0), (x, image_size)], fill=line_color)
            for y in range(0, image_size, cell_size):
                draw.line([(0, y), (image_size, y)], fill=line_color)

            # draw household IDs only on house cells
            for _, land_data in year_data.items():
                land = land_data["land"]
                if land.occupied == "house" and hasattr(land, "owner"):
                    x, y = land.location
                    draw.text(
                        (x * cell_size + 2, y * cell_size + 2),
                        str(land.owner),
                        fill=(0, 0, 0),
                        font=font,
                    )
                    if str(land.owner) == "None":
                        print("house owner == None")
            # small color legend
            legend_x, legend_y = 10, 10
            draw.text((legend_x, legend_y), f"Year {year + 1}", fill=(0, 0, 0), font=font)
            legend_y += 15
            for hid, color in list(house_colors.items()):  
                draw.rectangle(
                    [legend_x, legend_y, legend_x + 10, legend_y + 10],
                    fill=color,
                    outline=(0, 0, 0),
                )
                draw.text((legend_x + 15, legend_y), str(hid), fill=(0, 0, 0), font=font)
                legend_y += 12

            frames.append(img)
            # print(set(orphaned_hs))

        print("Saving GIF...")
        frames[0].save(
            file_path,
            format="GIF",
            append_images=frames[1:],
            save_all=True,
            duration=200,
            loop=0,
            optimize=False,
        )
        print("Animation saved:", file_path)
    