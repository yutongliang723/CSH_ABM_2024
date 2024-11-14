# Agent-Based Model 2024 Version
**Author**: Yutong Liang  
**Supervisor**: Dániel Kondor​  
**Topic**: Investigating Social Dynamics and Inequality in Neolithic Societies Through Agent-Based Modelling
### Introduction
The project aims to study the social dynamics in the neolithic time with Agent-Based Model.

### Current Progress
Agents (villagers) can farm, eat, involves birth and death, marriage, splitting out of their current household. On the household level, they can migrate to different area. Households can also trade with other households in exchange for longer-storage value instead of easily expired food. On the village level, it is possible to establish crop rotation system which requires each land to be fallowed every certain years. It is also possible to convert to fishing when a household's land is currently on fallow.

### Usage Manual
- Branch in the use: `main`
- Run the main.py after configuring the parameters

- Interface usage: so far, a simple simulation interface can be used locally. Please run the `interaction.py` and access the interface.

### Object Classes

- `Agent`
- `Household`
- `Village`

Additionally, the `utils.py` file contains functions primarily for initialization and printing, while `demog_vectors.csv` provides parameters for age-structured population data such as *age-group based survival probablies, fertility rates, consumption needs, work capabilities (Y/N), etc.*