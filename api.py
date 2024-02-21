import requests
import pandas as pd

from geopy.geocoders import Nominatim
from geopy.extra.rate_limiter import RateLimiter


# with open('API_key.key') as f:
#     API_KEY = f.read()

states = {
    'Hessen': ['Frankfurt am Main', 'Wiesbaden', 'Kassel', 'Darmstadt', 'Offenbach am Main'],
    'Brandenburg': ['Potsdam', 'Cottbus', 'Brandenburg an der Havel', 'Frankfurt', 'Oranienburg'],
    'Niedersachsen': ['Hanover', 'Braunschweig', 'Osnabrück', 'Oldenburg', 'Göttingen'],
    'Bayern': ['Munich', 'Nuremberg', 'Augsburg', 'Regensburg', 'Ingolstadt'],
    'Rheinland-Pfalz': ['Mainz', 'Ludwigshafen am Rhein', 'Koblenz', 'Trier', 'Kaiserslautern'],
    'Mecklenburg-Vorpommern': ['Rostock', 'Schwerin', 'Neubrandenburg', 'Stralsund', 'Greifswald'],
    'Thüringen': ['Erfurt', 'Jena', 'Gera', 'Weimar', 'Gotha'],
    'Berlin': ['Berlin'],
    'Saarland': ['Saarbrücken', 'Neunkirchen', 'Homburg', 'Völklingen', 'Sankt Ingbert'],
    'Nordrhein-Westfalen': ['Cologne', 'Düsseldorf', 'Dortmund', 'Essen', 'Duisburg'],
    'Bremen': ['Bremen'],
    'Sachsen-Anhalt': ['Halle', 'Magdeburg', 'Dessau-Roßlau', 'Lutherstadt Wittenberg', 'Halberstadt'],
    'Schleswig-Holstein': ['Kiel', 'Lübeck', 'Flensburg', 'Neumünster', 'Norderstedt'],
    'Sachsen': ['Leipzig', 'Dresden', 'Chemnitz', 'Zwickau', 'Görlitz'],
    'Baden-Württemberg': ['Stuttgart', 'Mannheim', 'Karlsruhe', 'Freiburg im Breisgau', 'Heidelberg'],
    'Hamburg': ['Hamburg'],
}


def get_lat_long(city_name: str) -> tuple:
    """
    This function takes a city name as input and returns a tuple containing the latitude and longitude of the specified city in Germany.
    Parameters:
        city_name (str): The name of the city for which the latitude and longitude are to be retrieved.
    Returns:
        tuple: A tuple containing the latitude and longitude of the specified city, or None if the location is not found.
    """
    geolocator = Nominatim(user_agent="my_geocoder")
    location = geolocator.geocode(f"{city_name}, {'Germany'}")
    if location:
        return location.latitude, location.longitude
    else:
        return None


def get_weather_for_city(city: str) -> pd.DataFrame:
    """
    Retrieves the weather forecast for a given city.

    Parameters:
        city (str): The name of the city for which to retrieve the weather forecast.

    Returns:
        pd.DataFrame: A DataFrame containing the wind speed forecast for the specified city.
    """
    latitude, longitude = get_lat_long(city)
    url = f"https://api.openweathermap.org/data/2.5/forecast?lat={latitude}&lon={longitude}&appid={API_KEY}"
    response = requests.get(url).json()
    data = {dt['dt']: dt['wind']['speed'] for dt in response['list']}
    df = pd.DataFrame.from_dict(data, columns=[f'wind_speed_{city}'], orient='index')
    return df


def get_weather_for_state(state: str) -> pd.DataFrame:
    """
    Retrieves weather data for a given state and returns the aggregated wind speed for the state as a pandas DataFrame.

    Args:
        state (str): The state for which weather data is to be retrieved.

    Returns:
        pd.DataFrame: The aggregated wind speed for the state.
    """
    df = get_weather_for_city(states[state][0])
    for i in range(1, len(states[state])):
        df = pd.concat([df, get_weather_for_city(states[state][i])], axis=1)
    return df.aggregate(['mean'], axis=1).rename(columns={'mean': f'wind_speed_{state}'})


def get_weather_df() -> pd.DataFrame:
    """
    This function retrieves weather data for each state and concatenates it into a single DataFrame.
    Returns: pd.DataFrame
    """
    for i in states:
        if i == 'Hessen':
            weather_df = get_weather_for_state(i)
        else:
            weather_df = pd.concat([weather_df, get_weather_for_state(i)], axis=1)
    return weather_df


def do_interpolation(df: pd.DataFrame) -> pd.DataFrame:
    """
    This function interpolates the given DataFrame to get hourly data.

    Args:
        df (pd.DataFrame): The input DataFrame to be interpolated.

    Returns:
        pd.DataFrame: The interpolated DataFrame.
    """
    new_indices = []
    for i in df.index:
        new_indices.append(i + (3600))
        new_indices.append(i + (7200))

    temp_df = pd.DataFrame(columns=df.columns, index=new_indices)
    df = pd.concat([df, temp_df], axis=0).sort_index(axis=0)
    df['time_unix'] = df.index
    return df.interpolate(method='linear', axis=0)


if __name__ == '__main__':

    # hourly_weather_df = do_interpolation(get_weather_df())

    weather_df = get_weather_df()
    hourly_weather_df = do_interpolation(weather_df)
