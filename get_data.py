import os
import requests
from dotenv import load_dotenv


load_dotenv()
API_KEY = os.getenv('API_KEY')

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


def get_event_odds(sport, event_id, reigons, markets, odds_format, bookmakers) -> dict:
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
        
        return odds_json

if __name__ == "__main__":
    events_json = get_events('americanfootball_nfl', '2025-11-11T20:00:00Z')
    print(events_json)

    for event in events_json[:1]:
        odds_params = (
            'americanfootball_nfl',
            event['id'],
            'us',
            'player_field_goals,player_kicking_points,player_pass_attempts',
            'decimal',
            'prizepicks,underdog,fanduel,draftkings,betmgm,espnbet,hardrockbet'
        )

        odds_json = get_event_odds(*odds_params)
        print(odds_json)