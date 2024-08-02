from household import Household
import matplotlib.pyplot as plt

class Village:
    def __init__(self, households, network, land_types):
        self.households = households 
        self.network = network
        self.land_types = land_types
        self.time = 0
        self.population_over_time = []
        self.land_capacity_over_time = []
        self.food_storage_over_time = []
    
    def run_simulation_step(self):
        self.time += 1
        print(f"\nSimulation Year {self.time}")

        for household in self.households:
            household.produce_food()
            household.consume_food()
            household.trade_resources()
            household.migrate()

            dead_agents = []
            newborn_agents = []

            for agent in household.members:
                agent.age_and_die()
                if not agent.is_alive:
                    dead_agents.append(agent)
                if hasattr(agent, 'newborn_agents'):
                    newborn_agents.extend(agent.newborn_agents)
                    del agent.newborn_agents  

            for agent in dead_agents:
                household.remove_member(agent)

            for newborn in newborn_agents:
                household.extend(newborn)

        self.update_tracking_variables()

    def update_tracking_variables(self):
        population = sum(len(household.members) for household in self.households)
        land_capacity = sum(household.land_quality for household in self.households)
        total_food = sum(household.food_storage for household in self.households)

        self.population_over_time.append(population)
        self.land_capacity_over_time.append(land_capacity)
        self.food_storage_over_time.append(total_food)

    def plot_simulation_results(self):
        plt.figure(figsize=(12, 8))

        plt.subplot(3, 1, 1)
        plt.plot(self.population_over_time, label='Population')
        plt.xlabel('Time Step')
        plt.ylabel('Population')
        plt.legend()

        plt.subplot(3, 1, 2)
        plt.plot(self.land_capacity_over_time, label='Land Capacity')
        plt.xlabel('Time Step')
        plt.ylabel('Land Capacity')
        plt.legend()

        plt.subplot(3, 1, 3)
        plt.plot(self.food_storage_over_time, label='Food Storage')
        plt.xlabel('Time Step')
        plt.ylabel('Food Storage')
        plt.legend()

        plt.tight_layout()
        plt.show()