# API Quick Reference - Frontend Integration

Base URL: `http://localhost:8000`

## Endpoints

### 0. Root / API Info
```
GET /
```

**Response:**
```json
{
  "message": "EV Betting API",
  "version": "1.0.0",
  "endpoints": {
    "/bets": "Get active EV bets",
    "/bets/stats": "Get betting statistics",
    "/health": "Health check"
  }
}
```

### 1. Get Active Bets
```
GET /bets
```

**Query Parameters:**
| Parameter | Type | Description | Example |
|-----------|------|-------------|---------|
| `bookmaker` | string | `prizepicks` or `underdog` | `?bookmaker=prizepicks` |
| `sport` | string | Sport name (partial match) | `?sport=NFL` |
| `min_ev` | float | Minimum EV % | `?min_ev=5.0` |
| `max_ev` | float | Maximum EV % | `?max_ev=15.0` |
| `player` | string | Player name (partial match) | `?player=mahomes` |
| `market` | string | Market type | `?market=player_pass_yds` |
| `limit` | int | Max results (default: 100, max: 500) | `?limit=50` |

**Response:**
```json
[
  {
    "id": 123,
    "bookmaker": "prizepicks",
    "market": "player_pass_yds",
    "player": "Patrick Mahomes",
    "outcome": "Over",
    "betting_line": 275.5,
    "sharp_mean": 285.3,
    "std_dev": 12.5,
    "implied_means": {"pinnacle": 283.2, "draftkings": 287.4},
    "sample_size": 15,
    "mean_diff": -9.8,
    "ev_percent": 8.45,
    "price": 1.82,
    "true_prob": 0.5954,
    "sport_title": "NFL",
    "home_team": "Kansas City Chiefs",
    "away_team": "Las Vegas Raiders",
    "commence_time": "2025-12-01T18:00:00",
    "created_at": "2025-11-30T12:00:00"
  }
]
```

### 2. Get Bets by Bookmaker
```
GET /bets/by-bookmaker/{bookmaker}
```

**Path Parameters:**
- `bookmaker`: `prizepicks` or `underdog`

**Query Parameters:**
- `limit`: Max results (default: 100, max: 500)

**Example:**
```
GET /bets/by-bookmaker/prizepicks?limit=50
```

### 3. Get Statistics
```
GET /bets/stats
```

**Response:**
```json
{
  "total_bets": 1234,
  "active_bets": 567,
  "avg_ev_percent": 7.85,
  "max_ev_percent": 23.45,
  "oldest_bet": "2025-11-30T10:15:30",
  "newest_bet": "2025-11-30T12:30:45"
}
```

### 4. Get Available Bookmakers
```
GET /bets/bookmakers
```

**Response:**
```json
{
  "bookmakers": [
    {"bookmaker": "prizepicks", "bet_count": 123},
    {"bookmaker": "underdog", "bet_count": 98}
  ]
}
```

### 5. Get Available Markets
```
GET /bets/markets
```

**Response:**
```json
{
  "markets": [
    {"market": "player_pass_yds", "bet_count": 45},
    {"market": "player_receptions", "bet_count": 38}
  ]
}
```

### 6. Health Check
```
GET /health
```

**Response:**
```json
{
  "status": "healthy",
  "database": "connected"
}
```

## Bet Object Fields

| Field | Type | Description |
|-------|------|-------------|
| `id` | int | Unique bet ID |
| `bookmaker` | string | `prizepicks` or `underdog` |
| `market` | string | Bet type (e.g., `player_pass_yds`) |
| `player` | string | Player name |
| `outcome` | string | `Over` or `Under` |
| `betting_line` | float | Line offered by bookmaker |
| `sharp_mean` | float | True mean from sharp books |
| `std_dev` | float (optional) | Standard deviation of sharp book lines |
| `implied_means` | dict (optional) | Individual sharp book implied means |
| `sample_size` | int (optional) | Number of sharp books used |
| `mean_diff` | float | Line - Sharp Mean (negative = value) |
| `ev_percent` | float | Expected Value % |
| `price` | float | Decimal odds |
| `true_prob` | float | True probability (0-1) |
| `sport_title` | string | Sport name (NFL, NBA, etc.) |
| `home_team` | string | Home team |
| `away_team` | string | Away team |
| `commence_time` | datetime | Game start time (ISO 8601) |
| `created_at` | datetime | Bet creation time |

## Common Use Cases

### Get Top EV Bets for PrizePicks
```javascript
fetch('http://localhost:8000/bets?bookmaker=prizepicks&limit=20')
  .then(res => res.json())
  .then(bets => console.log(bets));
```

### Get NFL Bets with 5%+ EV
```javascript
fetch('http://localhost:8000/bets?sport=NFL&min_ev=5.0')
  .then(res => res.json())
  .then(bets => console.log(bets));
```

### Get Bets for Specific Player
```javascript
fetch('http://localhost:8000/bets?player=mahomes')
  .then(res => res.json())
  .then(bets => console.log(bets));
```

### Get Dashboard Stats
```javascript
fetch('http://localhost:8000/bets/stats')
  .then(res => res.json())
  .then(stats => console.log(stats));
```

## React Example

```javascript
import { useState, useEffect } from 'react';

function BetsList() {
  const [bets, setBets] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetch('http://localhost:8000/bets?limit=50')
      .then(res => res.json())
      .then(data => {
        setBets(data);
        setLoading(false);
      })
      .catch(err => console.error(err));
  }, []);

  if (loading) return <div>Loading...</div>;

  return (
    <div>
      {bets.map(bet => (
        <div key={bet.id}>
          <h3>{bet.player} - {bet.market}</h3>
          <p>EV: {bet.ev_percent.toFixed(2)}%</p>
          <p>{bet.outcome} {bet.betting_line}</p>
          <p>{bet.home_team} vs {bet.away_team}</p>
        </div>
      ))}
    </div>
  );
}
```

## Filtering Examples

```javascript
// Multiple filters
const params = new URLSearchParams({
  bookmaker: 'prizepicks',
  sport: 'NFL',
  min_ev: '3.0',
  limit: '100'
});

fetch(`http://localhost:8000/bets?${params}`)
  .then(res => res.json())
  .then(bets => console.log(bets));
```

## Error Handling

```javascript
fetch('http://localhost:8000/bets')
  .then(res => {
    if (!res.ok) throw new Error('API error');
    return res.json();
  })
  .then(bets => console.log(bets))
  .catch(err => console.error('Error:', err));
```

## Notes

- All bets returned are active by default (filtered by `is_active = TRUE` in database)
- Bets are sorted by `ev_percent` descending (highest EV first)
- Times are in ISO 8601 format
- API supports CORS for frontend integration (all origins allowed)
- Optional fields (`std_dev`, `implied_means`, `sample_size`) may be `null` if not available
- Interactive API docs available at: `http://localhost:8000/docs`
- Alternative API docs at: `http://localhost:8000/redoc`


