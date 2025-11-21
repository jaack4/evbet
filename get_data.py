import os
import requests
from dotenv import load_dotenv
from Game import Game
from nfl_data import NFLData

NFL = 'americanfootball_nfl'
NFL_MARKETS = 'player_field_goals,player_pass_attempts,player_pass_completions,player_pass_interceptions,player_pass_tds,player_pass_yds,player_pats,player_receptions,player_reception_tds,player_reception_yds,player_rush_attempts,player_rush_yds,player_rush_tds,player_solo_tackles,player_assists'

load_dotenv()
API_KEY = os.getenv('API_KEY')
nfl_data = NFLData()

def get_events(sport, commence_time_to) -> dict:
    events_response = requests.get(f'https://api.the-odds-api.com/v4/sports/{sport}/events', params={
        'apiKey': API_KEY,
        'commenceTimeTo': commence_time_to
    })

    if events_response.status_code != 200:
        print(f'Failed to get events: status_code {events_response.status_code}, response body {events_response.text}')

    else:
        events_json = events_response.json()
        return events_json


def get_game(sport, event_id, reigons, markets, odds_format, bookmakers) -> Game:
    odds_response = requests.get(f'https://api.the-odds-api.com/v4/sports/{sport}/events/{event_id}/odds', params={
    'apiKey': API_KEY,
    'regions': reigons,
    'markets': markets,
    'oddsFormat': odds_format,
    'bookmakers': bookmakers
    })

    if odds_response.status_code != 200:
        print(f'Failed to get odds: status_code {odds_response.status_code}, response body {odds_response.text}')

    else:
        odds_json = odds_response.json()

        # Check the usage quota
        print('Remaining requests', odds_response.headers['x-requests-remaining'])
        print('Used requests', odds_response.headers['x-requests-used'])
        
        return Game(odds_json['id'], odds_json['sport_key'], odds_json['sport_title'], odds_json['commence_time'], odds_json['home_team'], odds_json['away_team'], odds_json['bookmakers'], markets, bookmakers, nfl_data)

def main():
    events_json = get_events('americanfootball_nfl', '2025-11-26T20:00:00Z')
    print(events_json)
    game = None
    for event in events_json[1:2]:
        odds_params = (
            'americanfootball_nfl',
            event['id'],
            'us',
            NFL_MARKETS,
            #'player_pass_yds,player_rush_yds,player_pass_completions,player_rush_attempts',
            'decimal',
            #'prizepicks,underdog,fanduel,draftkings,betmgm,espnbet,hardrockbet'
            'prizepicks,underdog,fanduel'
        )

        game = get_game(*odds_params)
        print(game)
    
    return game

if __name__ == "__main__":
    main()