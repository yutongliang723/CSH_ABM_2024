import random
import utils
from village import Village # Assuming VillageNetwork and Village are in the village module
from agent import Vec1
class Area:
    def __init__(self, village_list):
        self.villages = village_list
        self.village_network = {}

    def initialize_area_relationship(self):
        for village in self.villages:
            village.initialize_network()
            village.initialize_network_relationship()
            self.village_network[village.id] = {
                'connectivity': {}
            }
        # print(self.village_network)
        for village in self.villages:
            for other_village in self.villages:
                if village.id != other_village.id:
                    self.village_network[village.id]['connectivity'][other_village.id] = 0
        for village in self.villages:
            for household in village.households:
                household.village_id = village.id

    def add_village(self, village):
        """Add a village to the area and update the network."""
        self.villages.append(village)
        self.village_network.add_village(village)

    def run_simulation_step(self, vec1_instance, prod_multiplier=1, spare_food_enabled=False):
        """Run a simulation step for all villages in the area."""
        for village in self.villages:
            print(f'Village {village.id}')
            village.run_simulation_step(vec1_instance, prod_multiplier, self, spare_food_enabled)
    def get_connection_count(self, village1_id, village2_id):
        """Return the number of connections between two villages."""
        return self.village_network.get(village1_id, {}).get('connectivity', {}).get(village2_id, 0)


    def find_other_village(self, current_village):
        """Finds another village for inter-village interactions."""
        other_villages = [v for v in self.villages if v.id != current_village.id]
        if other_villages:
            other_villages = sorted(
                other_villages,
                key=lambda v: self.get_connection_count(current_village.id, v.id),
                reverse=True
            )
            return other_villages[0]
        return None

    def get_villages_sorted_by_connections(self, village_id):
        """Return a list of villages sorted by the number of connections to the specified village."""
        other_villages = [
            (v.id, self.get_connection_count(village_id, v.id)) 
            for v in self.villages 
            if v.id != village_id
        ]
        sorted_villages = sorted(other_villages, key=lambda x: x[1], reverse=True)
        return [v for v, _ in sorted_villages]