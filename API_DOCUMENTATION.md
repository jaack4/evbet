# EV Betting API Documentation

## Authentication

All endpoints (except `/` and `/health`) require API key authentication.

**Header:**
```
X-API-KEY: your_api_key_here
```

## Base URL

```
http://localhost:8000  (development)
```

---

## Endpoints

### 1. Root Information
**GET** `/`

Returns basic API information and available endpoints.

**Response:**
```json
{
  "message": "EV Betting API",
  "version": "1.0.0",
  "endpoints": {...}
}
```

---

### 2. Health Check
**GET** `/health`

Check API and database status.

**Response:**
```json
{
  "status": "healthy",
  "database": "connected"
}
```

---

### 3. Get Active Bets
**GET** `/bets`

Retrieve active EV betting opportunities with optional filters.

**Query Parameters:**
| Parameter | Type | Description | Default |
|-----------|------|-------------|---------|
| `bookmaker` | string | Filter by bookmaker: `prizepicks`, `underdog`, `betr`, `pick6` | - |
| `sport` | string | Filter by sport (e.g., `NFL`, `NBA`) | - |
| `min_ev` | float | Minimum EV percentage | - |
| `max_ev` | float | Maximum EV percentage | - |
| `player` | string | Player name (partial match) | - |
| `market` | string | Market type (e.g., `player_pass_yds`) | - |
| `limit` | integer | Max results (1-500) | 100 |

**Response:** Array of bet objects
```json
[
  {
    "id": 123,
    "bookmaker": "prizepicks",
    "market": "player_pass_yds",
    "player": "Patrick Mahomes",
    "outcome": "over",
    "betting_line": 275.5,
    "sharp_mean": 285.3,
    "ev_percent": 12.5,
    "price": 1.91,
    "true_prob": 0.52,
    "sport_title": "NFL",
    "home_team": "Kansas City Chiefs",
    "away_team": "Buffalo Bills",
    "commence_time": "2026-01-15T20:00:00Z",
    "created_at": "2026-01-11T10:30:00Z"
  }
]
```

---

### 4. Get Bets by Bookmaker
**GET** `/bets/by-bookmaker/{bookmaker}`

Get active bets for a specific bookmaker.

**Path Parameters:**
- `bookmaker`: `prizepicks`, `underdog`, `betr`, or `pick6`

**Query Parameters:**
- `limit`: Max results (1-500), default: 100

**Response:** Same as `/bets`

---

### 5. Get Bet Statistics
**GET** `/bets/stats`

Get aggregate statistics for all bets.

**Response:**
```json
{
  "total_bets": 1250,
  "active_bets": 89,
  "avg_ev_percent": 8.3,
  "max_ev_percent": 15.7,
  "oldest_bet": "2026-01-01T12:00:00Z",
  "newest_bet": "2026-01-11T10:30:00Z"
}
```

---

### 6. Get Available Bookmakers
**GET** `/bets/bookmakers`

List all bookmakers with active bets.

**Response:**
```json
{
  "bookmakers": [
    {
      "bookmaker": "prizepicks",
      "bet_count": 45
    },
    {
      "bookmaker": "underdog",
      "bet_count": 32
    }
  ]
}
```

---

### 7. Get Available Markets
**GET** `/bets/markets`

List all markets with active bets.

**Response:**
```json
{
  "markets": [
    {
      "market": "player_pass_yds",
      "bet_count": 28
    },
    {
      "market": "player_points",
      "bet_count": 25
    }
  ]
}
```

---

### 8. Get Historical Bets
**GET** `/bets/historical`

Retrieve completed bets with pagination.

**Query Parameters:**
| Parameter | Type | Description | Default |
|-----------|------|-------------|---------|
| `page` | integer | Page number (min: 1) | 1 |
| `page_size` | integer | Items per page (1-100) | 50 |
| `bookmaker` | string | Filter by bookmaker | - |
| `sport` | string | Filter by sport | - |
| `market` | string | Filter by market | - |
| `win` | boolean | Filter by outcome (true=wins, false=losses) | - |

**Response:**
```json
{
  "bets": [
    {
      "id": 123,
      "bookmaker": "prizepicks",
      "market": "player_pass_yds",
      "player": "Patrick Mahomes",
      "outcome": "over",
      "betting_line": 275.5,
      "sharp_mean": 285.3,
      "ev_percent": 12.5,
      "price": 1.91,
      "true_prob": 0.52,
      "sport_title": "NFL",
      "home_team": "Kansas City Chiefs",
      "away_team": "Buffalo Bills",
      "commence_time": "2026-01-10T20:00:00Z",
      "created_at": "2026-01-09T10:30:00Z",
      "win": true,
      "actual_value": 290.0,
      "prediction_diff": 4.7
    }
  ],
  "total_count": 150,
  "page": 1,
  "page_size": 50,
  "total_pages": 3
}
```

---

### 9. Get Hit Rate Statistics
**GET** `/bets/hitrate`

Get win/loss statistics broken down by category.

**Query Parameters:**
- `start_date`: Filter from date (ISO 8601 format)
- `end_date`: Filter to date (ISO 8601 format)

**Response:**
```json
{
  "overall": {
    "category": "Overall",
    "total_bets": 150,
    "wins": 82,
    "losses": 68,
    "hit_rate": 54.67
  },
  "by_bookmaker": [
    {
      "category": "prizepicks",
      "total_bets": 75,
      "wins": 43,
      "losses": 32,
      "hit_rate": 57.33
    }
  ],
  "by_sport": [
    {
      "category": "NFL",
      "total_bets": 90,
      "wins": 50,
      "losses": 40,
      "hit_rate": 55.56
    }
  ],
  "by_market": [
    {
      "category": "player_pass_yds",
      "total_bets": 45,
      "wins": 25,
      "losses": 20,
      "hit_rate": 55.56
    }
  ]
}
```

---

## Error Responses

All endpoints may return these error codes:

- **403 Forbidden**: Invalid API key
- **500 Internal Server Error**: Database or server error

**Error Response Format:**
```json
{
  "detail": "Error message here"
}
```

---

## Date Format

All dates use ISO 8601 format: `YYYY-MM-DDTHH:MM:SSZ`

## CORS

Allowed origins are configured via environment variables. Ensure your frontend domain is whitelisted.

