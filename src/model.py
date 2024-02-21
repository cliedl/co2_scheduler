import pandas as pd
import joblib

def predict(fetch_data=False):
    # Mock data - replace this with actual weather forecast
    df = pd.read_csv("data/combined_data.csv")
    df = df.iloc[-24*3:] # Take last three days of training data
    
    if fetch_data:
        weather_df = get_weather_df()
        hourly_weather_df = do_interpolation(weather_df)
        hourly_weather_df.to_csv("data/forecast_0.csv")
    else:
        hourly_weather_df = pd.read_csv("data/forecast_0.csv")

    hourly_weather_df.loc[:, "datetime"] = pd.to_datetime(hourly_weather_df["time_unix"], unit='s')
    hourly_weather_df.loc[:, 'month'] = hourly_weather_df['datetime'].dt.month
    hourly_weather_df.loc[:, 'hour'] = hourly_weather_df['datetime'].dt.hour

    features = [key for key in df if "wind" in key] + ["month", "hour"]
    model = joblib.load("models/xgb_1708455353.pkl")
    co2_predictions = model.predict(hourly_weather_df[features])
    time_axis = hourly_weather_df["datetime"]
    df_prediction = pd.DataFrame({'time_axis': time_axis, 'co2_predictions':co2_predictions})

    return df_prediction