# HealthUp Session Management Guide

## Overview

HealthUp now uses **httpOnly cookies** for secure session management with **2-week login sessions** and **30-day refresh tokens**. This provides better security than localStorage tokens and prevents XSS attacks.

## Architecture

### Backend (FastAPI)
- **Access Token**: 2 weeks (20160 minutes) - stored in httpOnly cookie
- **Refresh Token**: 30 days - stored in httpOnly cookie
- **Automatic Refresh**: Backend handles token refresh transparently
- **Secure Cookies**: httpOnly, secure (in production), SameSite protection

### Frontend (React)
- **No Token Storage**: Tokens are automatically handled by cookies
- **Automatic Refresh**: API client automatically refreshes expired tokens
- **Seamless UX**: Users stay logged in for 2 weeks without re-authentication

## Configuration

### Environment Variables

#### Backend (.env)
```bash
# Session Duration
ACCESS_TOKEN_EXPIRE_MINUTES=20160  # 2 weeks
REFRESH_TOKEN_EXPIRE_DAYS=30       # 30 days

# Cookie Security
COOKIE_SECURE=true                 # true for production, false for development
COOKIE_DOMAIN=your-domain.com      # your domain for production
COOKIE_SAMESITE=lax               # lax, strict, or none
```

#### Frontend (.env)
```bash
VITE_API_URL=http://your-domain.com/api
```

### Production Settings

For EC2 deployment, ensure these settings:

```bash
# Production cookie settings
COOKIE_SECURE=true
COOKIE_DOMAIN=your-actual-domain.com
COOKIE_SAMESITE=lax

# CORS settings for your domain
CORS_ORIGINS=https://your-domain.com
```

## Authentication Flow

### 1. Login
```
User submits credentials → Backend validates → Sets httpOnly cookies → Returns user data
```

### 2. API Requests
```
Frontend makes request → Cookies automatically included → Backend validates token → Returns data
```

### 3. Token Refresh
```
Access token expires → Frontend gets 401 → Automatically calls /auth/refresh → New cookies set → Retry original request
```

### 4. Logout
```
User clicks logout → Frontend calls /auth/logout → Backend clears cookies → User redirected to login
```

## Security Features

### httpOnly Cookies
- **XSS Protection**: Tokens cannot be accessed by JavaScript
- **CSRF Protection**: SameSite attribute prevents cross-site requests
- **Secure Transport**: HTTPS-only in production

### Automatic Refresh
- **Seamless UX**: Users don't see login prompts during active sessions
- **Background Refresh**: Happens automatically before token expiry
- **Graceful Degradation**: Falls back to login if refresh fails

### Session Duration
- **2-Week Sessions**: Long enough for convenience, short enough for security
- **30-Day Refresh**: Extended sessions for trusted devices
- **Automatic Cleanup**: Expired cookies are automatically removed

## API Endpoints

### Authentication
- `POST /auth/login` - Login and set cookies
- `POST /auth/refresh` - Refresh tokens (automatic)
- `POST /auth/logout` - Clear cookies
- `GET /auth/me` - Get current user info

### Cookie Names
- `access_token` - JWT access token (2 weeks)
- `refresh_token` - JWT refresh token (30 days)

## Frontend Integration

### AuthContext
```typescript
const { user, isAuthenticated, login, logout, loading } = useAuth();
```

### API Client
```typescript
// All requests automatically include cookies
const response = await apiClient.get('/dashboard');
```

### Automatic Handling
- **Token Refresh**: Handled automatically by API client
- **Session Expiry**: Redirects to login when refresh fails
- **Error Handling**: Graceful fallback for network issues

## Troubleshooting

### Common Issues

#### 1. Cookies Not Set
- Check `COOKIE_SECURE` setting (should be `false` for HTTP in development)
- Verify `COOKIE_DOMAIN` is correct for your domain
- Ensure CORS is configured with `allow_credentials: true`

#### 2. Session Ends Unexpectedly
- Check browser console for CORS errors
- Verify API URL is correct
- Ensure cookies are being sent with requests

#### 3. Production Issues
- Set `COOKIE_SECURE=true` for HTTPS
- Configure proper `COOKIE_DOMAIN`
- Update CORS origins to your production domain

### Debug Commands

#### Check Cookies
```javascript
// In browser console
document.cookie
```

#### Test Authentication
```bash
# Test login
curl -X POST http://localhost:8000/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"test@example.com","password":"password"}' \
  -c cookies.txt

# Test authenticated endpoint
curl -X GET http://localhost:8000/auth/me \
  -b cookies.txt
```

## Migration from localStorage

If migrating from localStorage tokens:

1. **Backend**: Already supports both cookie and header tokens
2. **Frontend**: Updated to use cookies automatically
3. **No Breaking Changes**: API remains compatible

## Best Practices

### Development
- Use `COOKIE_SECURE=false` for HTTP development
- Set `COOKIE_DOMAIN=` (empty) for localhost
- Test with different browsers

### Production
- Always use HTTPS with `COOKIE_SECURE=true`
- Set proper `COOKIE_DOMAIN` for your domain
- Monitor session expiry and user experience
- Consider implementing session analytics

### Security
- Regularly rotate `SECRET_KEY`
- Monitor for suspicious authentication patterns
- Implement rate limiting on auth endpoints
- Consider adding device fingerprinting for additional security

## Monitoring

### Session Metrics
- Track session duration and refresh patterns
- Monitor failed authentication attempts
- Log session expiry events

### User Experience
- Measure time between login and first action
- Track session interruption frequency
- Monitor logout patterns

## Future Enhancements

### Planned Features
- **Remember Me**: Extended sessions for trusted devices
- **Device Management**: Allow users to manage active sessions
- **Session Analytics**: Detailed session usage insights
- **Multi-factor Authentication**: Additional security layer

### Security Improvements
- **Token Blacklisting**: Invalidate specific tokens
- **Geographic Restrictions**: Limit sessions by location
- **Device Fingerprinting**: Enhanced session validation 