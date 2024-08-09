# Agent-Based Model 2024

### Current Progress

Added a animation gif showing land capacity change and migration;
Added migration logic and family splitting;
Initialized social network connectivity and added distance calculation;
Initialized luxury good exchanging with the village but not with families.
TODO: finish trading and implement marriage.

### Usage Manual
Run the main.py or can create a jupyter notebook and copy-paste the main.py code. If using jupyter notebook, restarting the kernal is sometimes required.

### Object Classes

- `Agent`
- `Household`
- `Village`

Additionally, the `utils.py` file contains functions primarily for initialization and printing, while `demog_vectors.csv` provides parameters for age-structured population data such as *age-group based survival probablies, fertility rates, consumption needs, work capabilities (Y/N), etc.*