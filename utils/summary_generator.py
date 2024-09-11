# summary_generator.py

from espn_api.football import League
from yfpy.query import YahooFantasySportsQuery
from sleeper_wrapper import League as SleeperLeague
from utils import espn_helper, yahoo_helper, sleeper_helper, helper
import openai  # Update: Use openai package directly
import logging
import datetime  # Fix: Missing import
import streamlit as st
from streamlit.logger import get_logger

LOGGER = get_logger(__name__)

def moderate_text(text):
    try:
        # Use the openai package directly
        response = openai.Moderation.create(input=text)
        
        # Extract the first result
        result = response['results'][0]
        
        # Return True if the content is not flagged, otherwise False
        return not result['flagged']
        
    except Exception as e:
        print(f"An error occurred: {str(e)}")
        return False  # Assume text is inappropriate in case of an error

LOGGER = logging.getLogger(__name__)

def generate_gpt4_summary_streaming(summary, character_choice, trash_talk_level):
    # Construct the instruction for GPT-4 based on user inputs
    instruction = f"You will be provided a summary below containing the most recent weekly stats for a fantasy football league. \
    Create a weekly recap in the style of {character_choice}. You should include trash talk with a level of {trash_talk_level}. \
    Here is the provided weekly fantasy summary: {summary}"

    try:
        # Correct API call with required arguments
        response = openai.completions.create(
            model="gpt-4",  # Correct model
            prompt=instruction,  # Using prompt instead of messages
            max_tokens=800,  # Limit the token count for brevity
            stream=True  # Enable streaming
        )

        # Processing the stream response
        for chunk in response:
            if chunk.get('choices') and chunk['choices'][0].get('text'):
                yield chunk['choices'][0]['text']
            else:
                LOGGER.error("Unexpected chunk structure or empty response")
                break

    except Exception as e:
        LOGGER.error(f"Error while generating GPT-4 summary: {str(e)}")
        return "Failed to get response from GPT-4"

        
@st.cache_data(ttl=3600)
def generate_sleeper_summary(league_id):
    league = SleeperLeague(league_id)
    current_date_today = datetime.datetime.now()  # Fix: datetime was not imported
    week = helper.get_current_week(current_date_today) - 1  # Force to always be the most recent completed week

    rosters = league.get_rosters()
    users = league.get_users()
    matchups = league.get_matchups(week)
    standings = league.get_standings(rosters, users)

    players_url = "https://raw.githubusercontent.com/jeisey/commish/main/players_data.json"
    players_data = sleeper_helper.load_player_data(players_url)

    user_team_mapping = league.map_users_to_team_name(users)
    roster_owner_mapping = league.map_rosterid_to_ownerid(rosters)

    scoreboards = sleeper_helper.calculate_scoreboards(matchups, user_team_mapping, roster_owner_mapping)

    highest_scoring_team_name, highest_scoring_team_score = sleeper_helper.highest_scoring_team_of_week(scoreboards)
    top_3_teams_result = sleeper_helper.top_3_teams(standings)
    highest_scoring_player_week, weekly_score, highest_scoring_player_team_week = sleeper_helper.highest_scoring_player_of_week(matchups, players_data, user_team_mapping, roster_owner_mapping)
    lowest_scoring_starter, lowest_starter_score, lowest_scoring_starter_team = sleeper_helper.lowest_scoring_starter_of_week(matchups, players_data, user_team_mapping, roster_owner_mapping)
    highest_scoring_benched_player, highest_benched_score, highest_scoring_benched_player_team = sleeper_helper.highest_scoring_benched_player_of_week(matchups, players_data, user_team_mapping, roster_owner_mapping)
    blowout_teams, point_differential_blowout = sleeper_helper.biggest_blowout_match_of_week(scoreboards)
    close_teams, point_differential_close = sleeper_helper.closest_match_of_week(scoreboards)
    hottest_streak_team, longest_streak = sleeper_helper.team_on_hottest_streak(rosters, user_team_mapping, roster_owner_mapping)

    summary = (
        f"The highest scoring team of the week: {highest_scoring_team_name} with {round(highest_scoring_team_score, 2)} points\n"
        f"Standings; Top 3 Teams:\n"
        f"  1. {top_3_teams_result[0][0]} - {top_3_teams_result[0][3]} points ({top_3_teams_result[0][1]}W-{top_3_teams_result[0][2]}L)\n"
        f"  2. {top_3_teams_result[1][0]} - {top_3_teams_result[1][3]} points ({top_3_teams_result[1][1]}W-{top_3_teams_result[1][2]}L)\n"
        f"  3. {top_3_teams_result[2][0]} - {top_3_teams_result[2][3]} points ({top_3_teams_result[2][1]}W-{top_3_teams_result[2][2]}L)\n"
        f"Highest scoring player of the week: {highest_scoring_player_week} with {weekly_score} points (Team: {highest_scoring_player_team_week})\n"
        f"Lowest scoring player of the week that started: {lowest_scoring_starter} with {lowest_starter_score} points (Team: {lowest_scoring_starter_team})\n"
        f"Highest scoring benched player of the week: {highest_scoring_benched_player} with {highest_benched_score} points (Team: {highest_scoring_benched_player_team})\n"
        f"Biggest blowout match of the week: {blowout_teams[0]} vs {blowout_teams[1]} (Point Differential: {round(point_differential_blowout, 2)})\n"
        f"Closest match of the week: {close_teams[0]} vs {close_teams[1]} (Point Differential: {round(point_differential_close, 2)})\n"
        f"Team on the hottest streak: {hottest_streak_team} with a {longest_streak} game win streak"
    )

    return summary



def generate_espn_summary(league, cw):
    """
    Generate a human-friendly summary based on the league stats.
    
    Args:
    - league (League): The league object.
    
    Returns:
    - str: A human-friendly summary.
    """
    # Extracting required data using helper functions
    start_time = datetime.datetime.now()
    top_teams = espn_helper.top_three_teams(league)
    print(f"Time for top_three_teams: {(datetime.datetime.now() - start_time).total_seconds()} seconds")
    
    start_time = datetime.datetime.now()
    top_scorer_week = espn_helper.top_scorer_of_week(league, cw)
    print(f"Time for top_scorer_of_week: {(datetime.datetime.now() - start_time).total_seconds()} seconds")
    
    start_time = datetime.datetime.now()
    worst_scorer_week = espn_helper.worst_scorer_of_week(league, cw)
    print(f"Time for worst_scorer_of_week: {(datetime.datetime.now() - start_time).total_seconds()} seconds")
    
    start_time = datetime.datetime.now()
    top_scorer_szn = espn_helper.top_scorer_of_season(league)
    print(f"Time for top_scorer_of_season: {(datetime.datetime.now() - start_time).total_seconds()} seconds")
    
    start_time = datetime.datetime.now()
    worst_scorer_szn = espn_helper.worst_scorer_of_season(league)
    print(f"Time for worst_scorer_of_season: {(datetime.datetime.now() - start_time).total_seconds()} seconds")
    
    start_time = datetime.datetime.now()
    most_trans = espn_helper.team_with_most_transactions(league)
    print(f"Time for team_with_most_transactions: {(datetime.datetime.now() - start_time).total_seconds()} seconds")
    
    start_time = datetime.datetime.now()
    most_injured = espn_helper.team_with_most_injured_players(league)
    print(f"Time for team_with_most_injured_players: {(datetime.datetime.now() - start_time).total_seconds()} seconds")
    
    start_time = datetime.datetime.now()
    highest_bench = espn_helper.highest_scoring_benched_player(league, cw)
    print(f"Time for highest_scoring_benched_player: {(datetime.datetime.now() - start_time).total_seconds()} seconds")
    
    start_time = datetime.datetime.now()
    lowest_start = espn_helper.lowest_scoring_starting_player(league, cw)
    print(f"Time for lowest_scoring_starting_player: {(datetime.datetime.now() - start_time).total_seconds()} seconds")
    
    start_time = datetime.datetime.now()
    biggest_blowout = espn_helper.biggest_blowout_match(league, cw)
    print(f"Time for biggest_blowout_match: {(datetime.datetime.now() - start_time).total_seconds()} seconds")
    
    start_time = datetime.datetime.now()
    closest_game = espn_helper.closest_game_match(league, cw)
    print(f"Time for closest_game_match: {(datetime.datetime.now() - start_time).total_seconds()} seconds")
    
    start_time = datetime.datetime.now()
    top_scoring_team_Week = espn_helper.highest_scoring_team(league, cw)
    print(f"Time for top_scoring_team_string: {(datetime.datetime.now() - start_time).total_seconds()} seconds")
    
    # Formatting the summary
    summary = f"""
    - Top scoring fantasy team this week: {top_scoring_team_Week} 
    - Top 3 fantasy teams: {espn_helper.clean_team_name(top_teams[0].team_name)}, {espn_helper.clean_team_name(top_teams[1].team_name)}, {espn_helper.clean_team_name(top_teams[2].team_name)}
    - Top scoring NFL player of the week: {top_scorer_week[0].name} with {top_scorer_week[1]} points.
    - Worst scoring NFL player of the week: {worst_scorer_week[0].name} with {worst_scorer_week[1]} points.
    - Top scoring NFL player of the season: {top_scorer_szn[0].name} with {top_scorer_szn[1]} points.
    - Worst scoring NFL player of the season: {worst_scorer_szn[0].name} with {worst_scorer_szn[1]} points.
    - Fantasy Team with the most transactions: {espn_helper.clean_team_name(most_trans[0].team_name)} ({most_trans[1]} transactions)
    - Fantasy Team with the most injured players: {espn_helper.clean_team_name(most_injured[0].team_name)} ({most_injured[1]} players: {', '.join(most_injured[2])})
    - Highest scoring benched player: {highest_bench[0].name} with {highest_bench[0].points} points (Rostered by {espn_helper.clean_team_name(highest_bench[1].team_name)})
    - Lowest scoring starting player of the week: {lowest_start[0].name} with {lowest_start[0].points} points (Rostered by {espn_helper.clean_team_name(lowest_start[1].team_name)})
    - Biggest blowout match of the week: {espn_helper.clean_team_name(biggest_blowout.home_team.team_name)} ({biggest_blowout.home_score} points) vs {espn_helper.clean_team_name(biggest_blowout.away_team.team_name)} ({biggest_blowout.away_score} points)
    - Closest game of the week: {espn_helper.clean_team_name(closest_game.home_team.team_name)} ({closest_game.home_score} points) vs {espn_helper.clean_team_name(closest_game.away_team.team_name)} ({closest_game.away_score} points)
    """
    
    return summary.strip()

@st.cache_data(ttl=3600)
def get_espn_league_summary(league_id, espn2, SWID):
    # Fetch data from ESPN Fantasy API and compute statistics   
    start_time_league_connect = datetime.datetime.now() 
    league_id = league_id
    year = 2023
    espn_s2 = espn2
    swid = SWID
    # Initialize league & current week
    try:
        league = League(league_id=league_id, year=year, espn_s2=espn_s2, swid=swid)
    except Exception as e:
        return str(e), "Error occurred during validation"
    end_time_league_connect = datetime.datetime.now()
    league_connect_duration = (end_time_league_connect - start_time_league_connect).total_seconds()
    cw = league.current_week-1
    # Generate summary
    start_time_summary = datetime.datetime.now()
    summary = generate_espn_summary(league, cw)
    end_time_summary = datetime.datetime.now()
    summary_duration = (end_time_summary - start_time_summary).total_seconds()
    # Generage debugging information, placeholder for now
    debug_info = "Summary: " + summary + " ~~~Timings~~~ " + f"League Connect Duration: {league_connect_duration} seconds " + f"Summary Duration: {summary_duration} seconds "
    return summary, debug_info

@st.cache_data(ttl=3600)
def get_yahoo_league_summary(league_id, auth_path):    
    league_id = league_id
    LOGGER.info(f"League id: {league_id}")
    auth_directory = auth_path
    sc = YahooFantasySportsQuery(
        auth_dir=auth_directory,
        league_id=league_id,
        game_code="nfl"
    )
    LOGGER.info(f"sc: {sc}")
    mrw = yahoo_helper.get_most_recent_week(sc)
    recap = yahoo_helper.generate_weekly_recap(sc, week=mrw)
    return recap




