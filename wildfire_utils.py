"""
Functions for my  Wildfire project
"""
import requests
import pandas as pd
import geopandas as gpd
import matplotlib.pyplot as plt
import numpy as np
import folium
from folium.plugins import MarkerCluster
from folium.plugins import HeatMaps
import branca.colormap as cm
import matplotlib.patches as mpatches

def fetch_data(map_key):
    """
    Fetch VIIRS active fire data from the NASA FIRMS API
    build URL from its components and uses requests.get()
    to retrieve the CSV data and returns GeoDataFrame

    Parameters
    ----------
    map_key : str
        my NASA FIRMS API key

    Returns
    --------
    ged.GeoDataFrame
        Raw fire detections with point geometries in EPSG:4326
    """
    
    url_api = f"https://firms.modaps.eosdis.nasa.gov/api/area/csv/{map_key}/VIIRS_SNPP_NRT/world/2"

    response = requests.get(url_api)
    print(response.status_code)
    print()
    print(response.text[:200]) 
    
    fires_df = pd.read_csv(url_api)

    print(fires_df.info())
    print()
    print(fires_df.head())
    
    fires_gdf = gpd.GeoDataFrame(
        fires_df,
        geometry = gpd.points_from_xy(fires_df['longitude'],fires_df['latitude']),
        crs= 'EPSG:4326')
        
    return fires_gdf


def prepare_fires(fires_gdf, madagascar, ecoregions):
    """
    Checks and cleans data 
    Filtering global fire detection to Madagascar and add derived variables:
    
    Perfom spatial join to keep only fires within Madagascar (polygon) and
    calculate 3 "new" columns:
    temp_diff: brightness temperature difference (bright_ti4 - bright_ti5)
    datetime: combined acq_time and acq_date as datetime object
    ecoregion/biome: island divided into ecoregions/biomes 

    Parameters
    ----------
    fires_gdf: gpd.GeoDataFrame
        from fetch_data()raw global fire detection
        
    madagascar: gpd.GeoDataFrame
        Madagascar polygon from Natural earth shapefile
        containing 'geometry' and 'NAME' for spatial join
        
    ecoregions gpd.GeoDataFrame
        ecoregion polygons from bachelore thesis of Moritz Wissmann 
        containing 'geometry', 'ECO_NAME', 'BIOME_NAME'
        
    Returns
    -------
    gpd.GeoDataFrame
        cleaned and adjusted for Madagascar
        containing columns: latitude, longitude,temp_diff,
        bright_ti4,bright_ti5, frp, daynight, datetime, ecoregion,
        biome,geometry
    """
    
    ##spatial join
    fires= gpd.sjoin(
        fires_gdf,
        madagascar[['geometry', 'NAME']],
        #only matching points are kept that are in madagascar polygon
        how='inner', 
        #point must be fully inside the polygon
        predicate='within') 

    ##clean data
    print()
    print(fires.isnull().sum())
    
    fires = fires.dropna()
    
    ##derived variables
    
    #temperature difference
    # ti4 = flame temperature, ti5 = background surface temperature
    # temp_diff = how much hotter the fire is compared to its sorroundings 
    fires['temp_diff'] = fires['bright_ti4']- fires['bright_ti5']

    #date + time into single column for datetime analysis
    fires['acq_time'] = fires['acq_time'].astype(str).str.zfill(4) #zfill: "0954"
    
    fires['datetime'] = pd.to_datetime( 
    fires['acq_date'] + ' ' + #' ' = space -> besseren überblick
    fires['acq_time'].str[:2] + ':' + # first 2 spaces : hours
    fires['acq_time'].str[2:], # last 2 minutes
    format='%Y-%m-%d %H:%M')

    #ecoregion subdivision
    fires = gpd.sjoin(
        #drop leftover of first join
        fires.drop(columns =['index_right'], errors=['ignore']),
        ecoregions[['geometry', 'ECO_NAME', 'BIOME_NAME']].reset_index(drop=True),
        how='left', 
        predicate='within'
        #drop the "new" one leftover
    ).drop(columns =['index_right'], errors=['ignore'])
        
    fires = fires.rename(columns={'ECO_NAME': 'ecoregion', 'BIOME_NAME': 'biome'})
    fires['ecoregion'] = fires['ecoregion'].fillna('Unknown')

    #keep only relevant columns
    fires = fires[[
        'latitude', 'longitude',
        'temp_diff', 'bright_ti4', 'bright_ti5',
        'frp', 'daynight', 'datetime', 'ecoregion', 'biome','geometry']]
    
    print(f"Fires within Madagascar: {len(fires)} detections.\n")
    return fires

    
def region_analysis(fires_madagascar):
    """
    Computes relationship and regional inensity.
    
    Calculate the correlation between FRP and temp_diff to asses 
    if both intensity meauseres agree. 
    Visualizing mean frp and temp_diff group by ecoregion as histograms and bar charts.

    Parameters
    ---------
    fires_madagascar: gpd.GeoDataFrame
        cleaned data from prepare_fires:
        contains 'frp', 'temp_diff', 'ecregion'

    Returns
    -------
    pd.Dataframe
        Dataframe with mean frp and temp_diff sorted by ecoregion
        
    """
    
    # the correlation shows us how well do frp and temp_diff agree
    # 1 = perfect correlation, 0 = relationship/agreement
    correlation = fires_madagascar['frp'].corr(fires_madagascar['temp_diff'])
    print(f"Correlation btw FRP and temp_diff: {correlation}\n")

    # mean frp: typical (avg.) total fire energy per region 
    # mean temp_diff: typical (avg.) fire intensity above landsurface temperature around the fire
    # = avg. of how much hotter burns fire than the sorrounding land surface temp. per region
    # direct comparison between North and South
    region_stats = fires_madagascar.groupby('ecoregion')[['frp', 'temp_diff']].mean()
    print(region_stats)
    
    ## distribution histogramm
    fig, axes = plt.subplots(1, 2, figsize =(12, 4))

    #distribution frp
    axes[0].hist(fires_madagascar['frp'], 
                 bins = 30, 
                 color = 'coral', 
                 edgecolor = 'black')
    axes[0].set_title('Distribution FRP')
    axes[0].set_xlabel('FRP MW')
    axes[0].set_ylabel('count')

    #distribution temp_diff
    axes[1].hist(fires_madagascar['temp_diff'], 
                 bins = 30, 
                 color = 'Cornflowerblue', 
                 edgecolor = 'black')
    axes[1].set_title('Distribution of ti4 - ti5')
    axes[1].set_xlabel('Temperature difference K')
    axes[1].set_ylabel('count')
    plt.suptitle('Wildfire Intensity Distributions in Madagascar', fontsize=13)
    plt.subplots_adjust(wspace=0.6)
    plt.show()

    ## bar charts regions
    fig, axes = plt.subplots(1, 2, figsize =(16, 6))

    colors= plt.cm.tab10(np.linspace(0,1,len(region_stats)))
    
    region_stats['frp'].plot(
        kind = 'barh', 
        ax= axes[0],
        #slice in case not all 7 colors/region present
        color = colors,
        edgecolor = 'black')
    axes[0].set_title('Avg FRP by ecoregion')
    axes[0].set_ylabel('')
    axes[0].set_xlabel('mean FRP')
    
    region_stats['temp_diff'].plot(
        #horizontal bar charts
        kind = 'barh', 
        ax= axes[1], 
        color = colors, 
        edgecolor = 'black')
    axes[1].set_title('Avg temperature difference by ecoregion')
    axes[1].set_ylabel('')
    axes[1].set_xlabel('mean ti4 - ti5 K')
    plt.suptitle('Fire Intensity by Ecoregion in Madagascar ', fontsize=13)

    plt.tight_layout()
    #more space btw the plots
    plt.subplots_adjust(wspace=0.75)
    plt.show()
    
    return region_stats

def build_map(fires_madagascar, madagascar, ecoregions):
    """
    Builds interactive folium map of wildfire intensity in Madagascar

    Creates 4 switchables layers map:
    -layer 0: Ecoregion polygons
    -layer 1 CircleMarkers: Fire are shown as circles 
    Size represents frp using min-max normalization (large circle = higher frp)
    Color shows temp_diff using sequential colormap (lightyellow = low diff.,
    dark red = high diff.)
    Sorted fires to get small circles on top of larger ones.
    -layer 3 Heatmap: Fire density surface weighted by FRP
    shows where the intense fire activity is concentrated.
    -layer 2 MarkerClusters: overview of fire locations

    To get map center:
    Computes Madagascar polygon centroid, first reprojected to EPSG:32738 (calculation with
    meters) after back to EPSG:4326 for Folium

    Parameters
    ---------
    fires_madagascar: gpd.GeoDataFrame
        cleaned data from prepare_fires:
        contains: 'frp', 'temp_diff', 'region', 'latitude', 'longitude'
        
    madagascar: gpd.GeoDataFrame
        Polygon to calculate map center 
        at the end needs to be EPSG:4326

    ecoregions: gpd.GeoDataFrame 
        containing 'geometry', 'ECO_NAME', 'BIOME_NAME'
    
    Returns
    -------
    folium.Map
        Interactive map with all 4 layers

    """

    ##calculate center of Madagascar
    #to get series so can select the element needed:.iloc[0] 
    #gets the first & here single point-> so can use x and y
    madagascar_projected= madagascar.to_crs(epsg=32738)
    center_projected= madagascar_projected.geometry.centroid.iloc[0]

    center = gpd.GeoSeries([center_projected], crs=32738).to_crs(epsg=4326).iloc[0]
    center_lat = center.y
    center_lon = center.x 
    print(f"Center of Madagascar:{center_lat, center_lon}")
    print()

    #Basemap
    #Esri map shows vegetation and terrain, helps explain why fire in certain areas
    m = folium.Map(
        location=[center_lat, center_lon],
        zoom_start=6,
        tiles="Esri.WorldImagery")

    #ecoregions polyfons layer 0
    fg_eco = folium.FeatureGroup(name = "Ecoregions", show=True).add_to(m)
    legend_html= """
    <div style="
        position: fixed;
        bottom: 30px; left: 30px;
        z-index: 1000;
        background-color: rgba(255,255,255,0.9);
        padding: 12px 16px;
        border-radius: 8px;
        font-family: Arial, sans-serif;
        font-size: 11px;
        box-shadow: 2px 2px 6px rgba(0,0,0,0.3);
        line-height: 1.8;
">
<b style="font-size:13px;">Ecoregions</b><br>
"""
    
    for _, row in ecoregions.iterrows():
        #legend entry
        legend_html+=(
            f'<span style="'
            f'background:{row["COLOR_BIO"]};'
            f'display:inline-block;'
            f'width:12px; height:12px;'
            f'margin-right:6px;'
            f'border:1px solid #aaa;'
            f'vertical-align:middle;'
            f'"></span>'
            f'{row["ECO_NAME"]}<br>'
        )
        #add polygon
        folium.GeoJson(
            row['geometry'].__geo_interface__,
            style_function = lambda feature, color= row['COLOR_BIO']: {
                'fillColor' : color,
                'color':'white',
                'weight':1.5,
                'fillOpacity': 0.6,
            },
        ).add_to(fg_eco)
    
    ##Colormap: color = temp_diff
    #vmin/vmax= quantiles preventing outliers to disturb/distort scale
    td_colormap = cm.LinearColormap(
        colors = ['LightYellow', 'DarkOrange', 'FireBrick'],
        vmin = fires_madagascar['temp_diff'].quantile(0.05),
        vmax = fires_madagascar['temp_diff'].quantile(0.95),
        caption =  'ΔT = Ti4-Ti5 (K)'
    ).add_to(m)

    ##FRP scaling for circle radius
    # clipped to 5%-95%: so that 1 extrem fire does not make all other fires
    # look the same in a smaller size 
    frp_min = fires_madagascar['frp'].quantile(0.05)
    frp_max = fires_madagascar['frp'].quantile(0.95) 
    
    ## layer 1
    fg_main = folium.FeatureGroup(
        name = "Intensity (size= FRP, color= ΔT)", 
        show=True
    ).add_to(m)

    fires_sorted = fires_madagascar.sort_values('frp', ascending=False)

    for _, row in fires_sorted.iterrows():
        #clipped-frp_min)/(frp_max-frp_min)-> min-max normalization: rescale val. btw 0-1
        # +3, * 10 stretches to pixel scale 3-13, so also weakest fire get min. radius 3px 
        radius = 3 + ((np.clip(row['frp'], frp_min, frp_max)-frp_min)/(frp_max-frp_min)) * 10 
                 
        folium.CircleMarker(
            location= [row['latitude'], row['longitude']],
            radius = radius,
            #gives color that corresponds to the specific fire temp_diff value
            fill_color = td_colormap(row['temp_diff']),
            fill_opacity = 0.8,
            fill = True,
            #border same color as fill
            color = td_colormap(row['temp_diff']),
            weight = 0.5,
            #tooltip: hovering over circles see this quick information
            tooltip = folium.Tooltip(
                f"FRP: {row['frp']:.1f} (MW) | ΔT: {row['temp_diff']:.1f} (K)<br>"
                f"Ecoregion: {row['ecoregion']}<br>"),
            #popup: by clicking on circle get full info.: hides complexer/more infos behind the click
            popup = folium.Popup(
                f"FRP: {row['frp']:.1f} (MW)<br>"
                f"Temp. difference: {row['temp_diff']:.1f} (K)<br>"
                f"Ecoregion: {row['ecoregion']}<br>"
                f"Biome: {row['biome']}",
                max_width= 200
            )
        ).add_to(fg_main)

    ##layer 2
    mc = MarkerCluster(name="Wildfire Clusters", show = False).add_to(m)
    # based on screen distance: if 2 fire closer than ~80 pixels in 1 cluster 
    # zooming in cluster split into smaller groups -> till indiviudal fires are visible
    for _, row in fires_sorted.iterrows():
        folium.CircleMarker(
            location= [row['latitude'], row['longitude']],
            radius = radius,
            fill_color = td_colormap(row['temp_diff']),
            #give me the color that corresponds to the specific fire temp_diff value
            fill_opacity = 0.8,
            fill = True,
            color = td_colormap(row['temp_diff']),
            weight = 0.5,
            tooltip = folium.Tooltip(
                f"FRP: {row['frp']:.1f} (MW)<br>"
                f"ΔT: {row['temp_diff']:.1f} (K)<br>"
                f"Ecoregion: {row['ecoregion']}<br>"
                f"Biome: {row['biome']}")   
        ).add_to(mc)
        
    ## layer 3
    # gives fire density from FRP across island
    # changes from layer 1 shows overall pattern not individual fires
    hm_frp = HeatMap(
        fires_madagascar[['latitude', 'longitude', 'frp']].values.tolist(),
        name = "Fire density heatmap",
        min_opacity = 0.45,
        #how far poits spread in px
        radius = 20,
        #how smooth edged btw fire blobs
        blur = 12,
        #at certain zoom heatmap dissapears more and more
        max_zoom = 8,
        #map hidden by default user needs to select first to see it
        show = False
    ).add_to(m) #adding directly to m avoids conflicts

    
    legend_html += "</div>"
    m.get_root().html.add_child(folium.Element(legend_html))
    ##layer control
    # for user to switch layers on/off: add of toggle panel
    # panel opens by default so user can see right away the options (coll.=False)
    folium.LayerControl(collapsed=False).add_to(m)


    return m
    
    
    

    




    
                    



        
    
    
    
    
    

