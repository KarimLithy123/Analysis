import sqlite3
from tkinter import Tk, Label, OptionMenu, Button, StringVar, Text, Scrollbar, Entry
conn = sqlite3.connect('database.sqlite')
cursor = conn.cursor()
def get_options(table_name, column_name, condition=""):
    query = f"SELECT DISTINCT {column_name} FROM {table_name} {condition};"
    cursor.execute(query)
    options = cursor.fetchall()
    options = [option[0] for option in options]
    return options

def show_matches():
    selected_season = season_var.get()
    selected_league = league_var.get()

    query = f"""
    SELECT id, date, home_team_goal, away_team_goal, home_team_api_id, away_team_api_id
    FROM Match
    WHERE season = '{selected_season}' AND league_id IN (SELECT id FROM League WHERE name = '{selected_league}');
    """

    cursor.execute(query)
    matches = cursor.fetchall()

    result_text.config(state='normal')
    result_text.delete('1.0', 'end')

    result_text.insert('1.0', "Matches Played:\n")
    for match in matches:
        match_date = match[1].split()[0]  # Extract only the date
        home_team = cursor.execute(f"SELECT team_long_name FROM Team WHERE team_api_id = {match[4]}").fetchone()[0]
        away_team = cursor.execute(f"SELECT team_long_name FROM Team WHERE team_api_id = {match[5]}").fetchone()[0]
        result_text.insert('end', f"{match_date} - {home_team} {match[2]}-{match[3]} {away_team}\n")

    result_text.config(state='disabled')

def calculate_matches_per_season():
    query = """
    SELECT COUNT(*) as Number_of_matches, season
    FROM Match
    GROUP BY season;
    """

    cursor.execute(query)
    matches_per_season = cursor.fetchall()

    result_text.config(state='normal')
    result_text.delete('1.0', 'end')  # Clear previous results

    result_text.insert('1.0', "Matches Per Season:\n")
    for match_count, season in matches_per_season:
        result_text.insert('end', f"Season {season}: {match_count} matches\n")

    result_text.config(state='disabled')

def calculate_teams_per_league():
    query = """
    SELECT League.name AS league_name, COUNT(DISTINCT Team.team_api_id) AS num_teams
    FROM Match
    JOIN League ON League.id = Match.league_id
    JOIN Team ON Team.team_api_id = Match.home_team_api_id OR Team.team_api_id = Match.away_team_api_id
    GROUP BY league_name
    ORDER BY league_name;
    """

    cursor.execute(query)
    teams_per_league = cursor.fetchall()

    result_text.config(state='normal')
    result_text.delete('1.0', 'end')  # Clear previous results

    result_text.insert('1.0', "Teams Per League:\n")
    for league_name, num_teams in teams_per_league:
        result_text.insert('end', f"{league_name}: {num_teams} teams\n")

    result_text.config(state='disabled')

def get_team_statistics():
    selected_team = team_entry.get()

    query = f"""
    SELECT
        Team.team_long_name AS team_name,
        League.name AS league_name,
        COUNT(Match.id) AS total_matches,
        SUM(Match.home_team_goal + Match.away_team_goal) AS total_goals_scored,
        SUM(CASE WHEN Match.home_team_api_id = Team.team_api_id AND Match.home_team_goal > Match.away_team_goal THEN 1
                 WHEN Match.away_team_api_id = Team.team_api_id AND Match.away_team_goal > Match.home_team_goal THEN 1
                 ELSE 0 END) AS total_wins,
        SUM(CASE WHEN Match.home_team_api_id = Team.team_api_id AND Match.home_team_goal < Match.away_team_goal THEN 1
                 WHEN Match.away_team_api_id = Team.team_api_id AND Match.away_team_goal < Match.home_team_goal THEN 1
                 ELSE 0 END) AS total_losses,
        ROUND(AVG(Match.home_team_goal + Match.away_team_goal),2) AS average_goals_per_match
    FROM
        Team
    JOIN
        Match ON Team.team_api_id = Match.home_team_api_id OR Team.team_api_id = Match.away_team_api_id
    JOIN
        League ON League.id = Match.league_id
    WHERE
        Team.team_api_id IS NOT NULL AND Team.team_long_name = '{selected_team}'
    GROUP BY
        Team.team_long_name, League.name
    ORDER BY
        total_wins DESC, total_goals_scored DESC;
    """

    cursor.execute(query)
    team_statistics = cursor.fetchall()

    result_text.config(state='normal')
    result_text.delete('1.0', 'end')  # Clear previous results

    result_text.insert('1.0', "Team Statistics:\n")
    for team_name, league_name, total_matches, total_goals, total_wins, total_losses, avg_goals_per_match in team_statistics:
        result_text.insert('end', f"{team_name} ({league_name}) - Matches: {total_matches}, Goals: {total_goals}, Wins: {total_wins}, Losses: {total_losses}, Avg Goals: {avg_goals_per_match}\n")

    result_text.config(state='disabled')

def on_dropdown_select(*args):
    show_matches_button.config(state='normal')
    calculate_matches_button.config(state='normal')
    calculate_teams_button.config(state='normal')
    calculate_team_stats_button.config(state='normal')
    result_text.config(state='normal')
    result_text.delete('1.0', 'end')
    result_text.config(state='disabled')

root = Tk()
root.title("Football Match Analyzer")
root.geometry("700x600")
Label(root, text="Select a Season:").grid(row=0, column=0, padx=10, pady=5)
Label(root, text="Select a League:").grid(row=0, column=1, padx=10, pady=5)
season_var = StringVar(root)
season_var.set("Select a Season")
season_options = ["2008/2009", "2009/2010", "2010/2011", "2011/2012", "2012/2013", "2013/2014", "2014/2015", "2015/2016", "2016/2017", "2017/2018"]
season_dropdown = OptionMenu(root, season_var, *season_options)
season_dropdown.grid(row=1, column=0, padx=10, pady=5)
season_var.trace("w", on_dropdown_select)

league_var = StringVar(root)
league_var.set("Select a League")
league_options = get_options("League", "name")
league_dropdown = OptionMenu(root, league_var, *league_options)
league_dropdown.grid(row=1, column=1, padx=10, pady=5)
league_var.trace("w", on_dropdown_select)

Label(root, text="Enter Team Name:").grid(row=2, column=0, padx=10, pady=5)
team_entry = Entry(root)
team_entry.grid(row=2, column=1, padx=10, pady=5)

result_text = Text(root, height=20, width=80, wrap='word')
result_text.grid(row=3, column=0, columnspan=2, padx=10, pady=5)

scrollbar = Scrollbar(root, command=result_text.yview)
scrollbar.grid(row=3, column=2, sticky='ns')
result_text.config(yscrollcommand=scrollbar.set)

show_matches_button = Button(root, text="Show Matches", command=show_matches, state='disabled')
show_matches_button.grid(row=4, column=0, columnspan=2, pady=5)

calculate_matches_button = Button(root, text="Calculate Matches Per Season", command=calculate_matches_per_season, state='disabled')
calculate_matches_button.grid(row=5, column=0, columnspan=2, pady=5)

calculate_teams_button = Button(root, text="Calculate Teams Per League", command=calculate_teams_per_league, state='disabled')
calculate_teams_button.grid(row=6, column=0, columnspan=2, pady=5)

calculate_team_stats_button = Button(root, text="Get Team Statistics", command=get_team_statistics, state='disabled')
calculate_team_stats_button.grid(row=7, column=0, columnspan=2, pady=5)

root.mainloop()
conn.close()