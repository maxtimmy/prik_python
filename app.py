import streamlit as st
import pandas as pd
import plotly.express as px
import requests
from datetime import datetime

st.set_page_config(page_title="Temperature Monitoring", layout="wide")

st.title("🌍 Анализ температур и мониторинг климата")

uploaded_file = st.file_uploader("Загрузите temperature_data.csv", type="csv")

if uploaded_file:
    df = pd.read_csv(uploaded_file, parse_dates=["timestamp"])

    city = st.selectbox("Выберите город", sorted(df.city.unique()))
    city_df = df[df.city == city]

    city_df["rolling_mean"] = city_df.temperature.rolling(30, min_periods=1).mean()

    season_stats = city_df.groupby("season")["temperature"].agg(["mean", "std"]).reset_index()

    city_df = city_df.merge(season_stats, on="season")
    city_df["is_anomaly"] = (
            (city_df.temperature > city_df["mean"] + 2 * city_df["std"]) |
            (city_df.temperature < city_df["mean"] - 2 * city_df["std"])
    )

    st.subheader("📊 Описательная статистика")
    st.dataframe(season_stats)

    st.subheader("📈 Временной ряд температуры")
    fig = px.line(city_df, x="timestamp", y="temperature", title=city)
    fig.add_scatter(
        x=city_df[city_df.is_anomaly]["timestamp"],
        y=city_df[city_df.is_anomaly]["temperature"],
        mode="markers",
        name="Аномалии"
    )
    st.plotly_chart(fig, use_container_width=True)

    st.subheader("🌦 Сезонные профили")
    fig2 = px.bar(season_stats, x="season", y="mean", error_y="std")
    st.plotly_chart(fig2, use_container_width=True)

    st.subheader("🌡 Текущая температура (OpenWeatherMap)")
    api_key = st.text_input("Введите API Key", type="password")

    if api_key:
        url = "https://api.openweathermap.org/data/2.5/weather"
        params = {"q": city, "appid": api_key, "units": "metric"}
        response = requests.get(url, params=params).json()

        if response.get("cod") == 401:
            st.error(response["message"])
        else:
            current_temp = response["main"]["temp"]
            current_month = datetime.now().month
            season_map = {12: "winter", 1: "winter", 2: "winter", 3: "spring", 4: "spring",
                          5: "spring", 6: "summer", 7: "summer", 8: "summer",
                          9: "autumn", 10: "autumn", 11: "autumn"}
            current_season = season_map[current_month]
            s = season_stats[season_stats.season == current_season].iloc[0]

            status = "Норма ✅"
            if current_temp > s["mean"] + 2 * s["std"]:
                status = "Аномально тепло 🔥"
            elif current_temp < s["mean"] - 2 * s["std"]:
                status = "Аномально холодно ❄️"

            st.metric("Температура сейчас", f"{current_temp} °C", status)