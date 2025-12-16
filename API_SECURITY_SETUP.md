# API Security Setup Instructions

## 1. Add to your .env file

Add these lines to your `.env` file:

```bash
# API Security
API_KEY=9PGAn2wjY2kTI5Jg2spaCkCiRG-AYv3wqhxVMk7-Klo

# CORS Configuration (comma-separated list of allowed origins)
ALLOWED_ORIGINS=http://localhost:3000,https://yourdomain.com
```

**Important:** 
- Replace the API_KEY with a new one if you prefer (generate with: `python -c "import secrets; print(secrets.token_urlsafe(32))"`)
- Update `ALLOWED_ORIGINS` with your actual website domain(s)

## 2. Frontend Implementation

When making requests from your website, include the API key in the headers:

### JavaScript/Fetch Example:
```javascript
fetch('http://your-api-url:8000/bets', {
    headers: {
        'X-API-Key': '9PGAn2wjY2kTI5Jg2spaCkCiRG-AYv3wqhxVMk7-Klo'
    }
})
.then(response => response.json())
.then(data => console.log(data));
```

### Axios Example:
```javascript
axios.get('http://your-api-url:8000/bets', {
    headers: {
        'X-API-Key': '9PGAn2wjY2kTI5Jg2spaCkCiRG-AYv3wqhxVMk7-Klo'
    }
})
.then(response => console.log(response.data));
```

## 3. Protected Endpoints

The following endpoints now require the `X-API-Key` header:
- `/bets`
- `/bets/by-bookmaker/{bookmaker}`
- `/bets/stats`
- `/bets/bookmakers`
- `/bets/markets`

The following endpoints remain public (no API key needed):
- `/` (root)
- `/health`

## 4. Testing

Test the API with curl:

```bash
# Without API key (should fail with 403)
curl http://localhost:8000/bets

# With API key (should succeed)
curl -H "X-API-Key: 9PGAn2wjY2kTI5Jg2spaCkCiRG-AYv3wqhxVMk7-Klo" http://localhost:8000/bets
```

## Security Notes

- Keep your API key secret
- Use HTTPS in production
- Only add trusted domains to ALLOWED_ORIGINS
- Store the API key in environment variables, never commit it to version control

