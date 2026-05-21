# MADAGASCAR WILDFIRE INTENSITY ANALYSIS
Analyzing active fire detections from NASA FIRMS VIIRS satellite to explore where the most intense wildfires occur across the island's 7 ecoregions and using brightness temperature difference and Fire Radiative Power (FRP)

## Research Question
Where are the most intense wildfires in Madagascar, and does the brightness temperature difference (ΔT = Ti5 - Ti4) together with FRP intensity reveal spatial distribution in fire behaviour?

## Data Sources
#Dataset | Source | Path  
-Active fire detection from last 2 days (VIIRS SNPP NRT)| [NASA FIRMS API] https://firms.modaps.eosdis.nasa.gov/ | fetched via API

-Country boundaries | [Natural Earth] https://www.naturalearthdata.com/downloads/ | 'data/ne_10m_admin_0_countries/'

-Ecoregions 2017 | from a pier student that did his bachelor thesis on Madagascar | 'data/data/ne_10m_admin_0_countries/'

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
