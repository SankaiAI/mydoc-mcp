# API Design Guide

This is a test markdown document for indexing with the mydoc-mcp system.

## Introduction

This guide demonstrates API design best practices for modern web applications.

## Key Principles

1. **Consistency** - Keep APIs consistent across all services
2. **Simplicity** - Make APIs easy to understand and use
3. **Security** - Always implement proper authentication and authorization
4. **Documentation** - Provide comprehensive, up-to-date documentation

## REST API Guidelines

### HTTP Methods
- **GET**: Retrieve data or resources
- **POST**: Create new resources
- **PUT**: Update or replace existing resources
- **DELETE**: Remove resources

### Status Codes
- **200**: OK - Request successful
- **201**: Created - Resource created successfully
- **400**: Bad Request - Invalid request data
- **401**: Unauthorized - Authentication required
- **404**: Not Found - Resource not found
- **500**: Internal Server Error - Server-side error

### Request/Response Format
Always use JSON for request and response bodies:

```json
{
  "status": "success",
  "data": {
    "id": 123,
    "name": "Example Resource"
  },
  "metadata": {
    "timestamp": "2023-12-01T10:00:00Z"
  }
}
```

## Error Handling

Implement consistent error responses:

```json
{
  "status": "error",
  "error": {
    "code": "VALIDATION_ERROR",
    "message": "Invalid input data",
    "details": {
      "field": "email",
      "issue": "Invalid format"
    }
  }
}
```

## Conclusion

Following these guidelines will help create maintainable, user-friendly APIs that scale well with your application.