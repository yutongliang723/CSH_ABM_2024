def split_household(self, village):
        """Handle the splitting of a household when it grows too large."""
        
        empty_land_cells = [loc for loc, data in village.land_types.items() if not data['occupied']]
        
        if empty_land_cells:
            new_household_members = []

            # Order the single and married
            order = {"single": 0, "married": 1}
            self.memebers.sort(key=lambda x: order.get(x.marital_status, 2)) 

            members_to_leave = len(self.members)
            
            count = 0

            for agent in self.members:
                if count < members_to_leave and agent.marital_status == 'single':
                    new_household_members.append(agent)
                    count += 1
                    
                if count < members_to_leave and agent.marital_status == 'married':
                    agent_partner = get_agent_by_id(village, agent.partner_id)
                    new_household_members.extend([agent, agent_partner])
                    count += 1

            for member in new_household_members:
                if member in self.members:
                    self.remove_member(member)

            total_food_storage = sum(amount for amount, _ in self.food_storage)
            new_food_storage = [f/2 for (f, y) in total_food_storage]
            self.food_storage = new_food_storage

            new_luxury_good_storage = self.luxury_good_storage // 2
            self.luxury_good_storage -= new_luxury_good_storage
            new_household_id = str(uuid.uuid4())
            
            new_household = Household(
                new_household_id,
                food_storage=[(new_food_storage, 0)],
                luxury_good_storage=new_luxury_good_storage,
                members=new_household_members,
                location = None
            )
            for m in new_household.members:
                m.id = new_household.id
            new_location = random.choice(empty_land_cells)
            village.land_types[new_location]['occupied'] = True
            village.land_types[new_location]['household_id'] = new_household.id
            new_household.location = new_location

            village.households.append(new_household)

            create_network_connectivity_household_distance(village)



def create_network_connectivity_household_distance(self, village):
    if not village.network[self.id]:
            village.network[self.id] = {
            'connectivity': {},
            'luxury_goods': self.luxury_good_storage
        }
    for other_household in village.households:
            if other_household.id != self.id:
                distance = village.get_distance(self.location, other_household.location)
                village.network[self.id]['connectivity'][other_household.id] = max(0, 1/distance)
                village.network[other_household.id]['connectivity'][self.id] = max(0, 1/distance)