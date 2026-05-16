def fetch_data(map_key):
    """
    Fetch VIIRS active fire data from the NASA FIRMS API
    build URL from its components and uses requests.get()
    to retrieve the CSV data.

    Parameters
    ----------
    map_key : str
        my NASA FIRMS API key.
    sensor : str
        sensor product: 'VIIRS_SNPP_NRT'.
    area : str
        'world' 
    days : int
        nr of past days to retrieve: 5

    Returns
    --------
    DataFrame
        Raw fire detections 
    """
    url_api = f"https://firms.modaps.eosdis.nasa.gov/api/area/csv/{map_key}/VIIRS_SNPP_NRT/world/5"

    response = requests.get(url_api)
    print(response.status_code)
    print(response.text[:200]) 
    
    fires_df = pd.read_csv(url_api)
    return fires_df


def clean_data(df):