# MADAGASCAR WILDFIRE INTENSITY ANALYSIS
Analyzing active fire detections from NASA FIRMS VIIRS satellite to explore where the most intense wildfires occur across the island's 7 ecoregions and using brightness temperature difference (ΔT) and Fire Radiative Power (FRP).

## Research Question
Where are the most intense wildfires in Madagascar, and does the brightness temperature difference together with FRP intensity reveal spatial distribution in fire behaviour?

## Key Variables
#Variable | Meaning
- FRP (MW) | Fire Radiative Power: total energy (power) released by the fire
- ΔT (K) | Ti4 - Ti5: how much hotter the fire is compared to its sorrounding land surface
- Ti 4 | VIIRS band I4: fire brightness temperature
- Ti5 | VIIRS band I5: background land surface temperature

## Data Sources
#Dataset | Source | Path  
-Active fire detection from last 2 days (VIIRS SNPP NRT)| [NASA FIRMS API]| fetched via API

-Country boundaries | [Natural Earth]| 'data/ne_10m_admin_0_countries/'

-Ecoregions 2017 | from a peer student Moritz .... that did his bachelor thesis on Madagascar | 'data/data/ne_10m_admin_0_countries/'

## Project Structure
'''
.
├── environment.yml                  # conda environement
├── notebooks
│   ├── 01_wildfire_project.ipynb    # main analysis
│   ├── 02_wildfire_temp_diff.ipynb
│   ├── 03_wf_daynight.ipynb
│   └── 04_wf_duration.ipynb
├── outputs
│   └── wildfire_map.html            # interactice map
├── README.md
└── wildfire_utils.py                # reusable functions
'''

## How to Run
1. Clone Repertory
2. Recreate enveronement
```bash
   conda env create -f environment.yml
   conda activate sds-env
```
3. Download data
  - Natural Earth to get country boundaries : https://www.naturalearthdata.com/downloads/
  - Ecoregions: https://ecoregions.appspot.com
4. Get a NASA FIRMS API key: https://firms.modaps.eosdis.nasa.gov/
5. Add your key to an '.env' file in project root for safety
