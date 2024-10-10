from datetime import datetime
import re
import requests
import pandas as pd
from pprint import pprint
import streamlit as st
from streamlit_echarts import st_echarts


class PlayerRatings:
    def __init__(self):
        self.base_url = "https://sofascore.com/"
        self.headersList = {"Accept": "*/*", "User-Agent": "Falkirk Ratings"}

    def get_response(self, addToUrl, payload=""):
        response = requests.request(
            "GET", self.base_url + addToUrl, data=payload, headers=self.headersList
        )
        response = response.json()
        return response

    def get_player_ratings(self, match_id, home):
        reqUrl = f"api/v1/event/{match_id}/lineups"

        response = self.get_response(reqUrl)

        player_ratings = {
            player["player"]["name"]: player["statistics"]["rating"]
            for player in response.get(home, {}).get("players", {})
            if (player.get("statistics") and player["statistics"].get("rating"))
        }

        return player_ratings

    def get_falkirk_matches(self):
        reqUrl = "api/v1/team/2363/events/last/0"

        response = self.get_response(reqUrl)

        matches = {
            match["slug"]: (
                match["id"],
                "home" if match["homeTeam"]["name"] == "Falkirk FC" else "away",
                match["time"].get("currentPeriodStartTimestamp"),
            )
            for match in response["events"]
        }
        sorted_matches = dict(sorted(matches.items(), key=lambda item: item[1][2]))
        return sorted_matches

    def format_column_title(self, slug, date):
        slug_normalized = slug.replace("-", " ")

        if slug_normalized.startswith("falkirk fc"):
            team_name = slug_normalized.replace("falkirk fc", "").strip().title()
        else:
            team_name = slug_normalized.split(" falkirk fc")[0].strip().title()

        return f"{team_name} {date}"

    def createDf(self, matches):
        data = {}
        for match in matches:
            player_ratings = self.get_player_ratings(
                matches[match][0], matches[match][1]
            )
            if not player_ratings:
                continue
            # print('='*90)
            # print(match)
            # print(player_ratings)
            match_date = datetime.fromtimestamp(matches[match][2]).strftime("%d/%m/%y")
            column_title = self.format_column_title(match, match_date)
            data[column_title] = player_ratings
        df = pd.DataFrame(data)
        df = df.fillna("0.0")
        return df

    def chart(self, df):
        st.title("Player SofaScore Ratings")
        st.write("By Aiden Lyons")
        st.write("This page updates automatically, via SofaScore API.")

        # Set text color based on the theme
        background_color = "#0f1116"
        text_color = "white"

        # Assuming your DataFrame is already available
        # Replace this with your actual DataFrame object (e.g., ratings_data_filled)
        player_names = df.index  # Player names as row index
        match_dates = df.columns  # Match dates or match labels

        # Extract just the team names by splitting before the first number (date)
        match_labels = [re.split(r"\d", match)[0].strip() for match in match_dates]

        # Multi-select dropdown to choose players
        selected_players = st.multiselect(
            "Select players to display", options=player_names, default="Nicky Hogarth"
        )

        # Filter the DataFrame based on selected players
        filtered_data = df.loc[selected_players]

        chart_height = 400 + len(selected_players) * 20

        # Convert DataFrame into series format for ECharts
        series_data = []
        for i, player in enumerate(filtered_data.index):
            series_data.append(
                {
                    "name": player,
                    "type": "line",
                    "areaStyle": {},
                    "emphasis": {"focus": "series"},
                    "data": filtered_data.loc[
                        player
                    ].tolist(),  # Player's ratings across matches
                }
            )

        # ECharts option setup using your football data
        options = {
            "backgroundColor": background_color,
            "title": {
                "text": "Player Ratings Over Matches",
                "textStyle": {"color": text_color},
            },
            "tooltip": {
                "trigger": "axis",
                "axisPointer": {
                    "type": "shadow",
                    "label": {"backgroundColor": "#6a7985", "color": text_color},
                },
            },
            "legend": {
                "data": filtered_data.index.tolist(),
                "type": "scroll",  # Allow the legend to scroll if too many items
                "orient": "horizontal",  # Legend items placed horizontally
                "bottom": "0%",  # Place the legend at the bottom
                "width": "80%",  # Adjust width so the legend can wrap
                "textStyle": {"color": text_color},
            },
            # "toolbox": {"feature": {"saveAsImage": {}}},
            "grid": {
                "left": "5%",
                "right": "2%",
                "bottom": "10%",
                "containLabel": True,
            },
            "xAxis": [
                {
                    "type": "category",
                    "boundaryGap": False,
                    "data": match_labels,  # Use match dates as x-axis labels
                    "axisLabel": {
                        "color": text_color,
                        "rotate": 45,
                        "fontSize": 10,
                    },  # Dynamic x-axis label text color
                }
            ],
            "yAxis": [
                {
                    "type": "value",
                    "min": 0,
                    "max": 10,
                    "axisLabel": {"color": text_color},
                }
            ],
            "series": series_data,  # Series data generated from DataFrame
        }

        # Render the chart using st_echarts
        st_echarts(options=options, height=f"{chart_height}px")


def main():
    pr = PlayerRatings()
    matches = pr.get_falkirk_matches()
    df = pr.createDf(matches)
    pr.chart(df)


if __name__ == "__main__":
    main()
