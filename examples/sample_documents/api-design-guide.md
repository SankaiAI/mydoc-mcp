# REST API Design Guide

## Overview

This document outlines best practices for designing RESTful APIs that are intuitive, maintainable, and scalable.

## Core Principles

### 1. Resource-Based URLs
- Use nouns, not verbs in endpoints
- Collections: `/api/users`
- Single resource: `/api/users/{id}`
- Nested resources: `/api/users/{id}/orders`

### 2. HTTP Methods
- **GET**: Retrieve resource(s)
- **POST**: Create new resource
- **PUT**: Update entire resource
- **PATCH**: Partial update
- **DELETE**: Remove resource

### 3. Status Codes
- **200 OK**: Successful GET/PUT/PATCH
- **201 Created**: Successful POST
- **204 No Content**: Successful DELETE
- **400 Bad Request**: Client error
- **401 Unauthorized**: Authentication required
- **404 Not Found**: Resource doesn't exist
- **500 Internal Server Error**: Server error

## Best Practices

### Versioning
```
/api/v1/users
/api/v2/users
```

### Pagination
```
GET /api/users?page=2&limit=20
```

### Filtering
```
GET /api/users?status=active&role=admin
```

### Sorting
```
GET /api/users?sort=created_at&order=desc
```

## Authentication

### OAuth 2.0
- Use OAuth 2.0 for third-party integrations
- Implement proper token refresh mechanisms
- Store tokens securely

### API Keys
- Use API keys for server-to-server communication
- Rotate keys regularly
- Implement rate limiting per key

## Error Handling

### Standard Error Response
```json
{
  "error": {
    "code": "INVALID_PARAMETER",
    "message": "The 'email' field is required",
    "details": {
      "field": "email",
      "reason": "missing"
    }
  }
}
```

## Documentation

### OpenAPI Specification
- Document all endpoints with OpenAPI 3.0
- Include request/response examples
- Specify all possible error responses

### Interactive Documentation
- Provide Swagger UI for testing
- Include authentication in docs
- Keep documentation synchronized with code

## Performance

### Caching
- Implement ETag headers
- Use Cache-Control headers
- Support conditional requests

### Rate Limiting
- Return rate limit headers
- Implement exponential backoff
- Provide clear error messages

## Security

### HTTPS Only
- Never allow HTTP in production
- Use proper SSL certificates
- Implement HSTS headers

### Input Validation
- Validate all input data
- Sanitize user inputs
- Use parameterized queries

### CORS
- Configure CORS properly
- Limit allowed origins
- Be specific with allowed methods

## Testing

### Integration Tests
- Test all endpoints
- Verify error scenarios
- Check authentication flows

### Load Testing
- Test under expected load
- Identify bottlenecks
- Plan for scaling

## Monitoring

### Logging
- Log all API requests
- Include correlation IDs
- Monitor error rates

### Metrics
- Track response times
- Monitor usage patterns
- Alert on anomalies

---

*Last Updated: September 2025*
*Version: 2.0*