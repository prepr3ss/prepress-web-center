# Dynamic Filter Architecture

## System Architecture Diagram

```mermaid
graph TB
    subgraph "Frontend Layer"
        A[tabelkpictp.html] --> B[Dynamic Filter JS]
        C[dashboard_ctp.html] --> B
        D[stock_opname_ctp.html] --> B
        E[chemical_bon_ctp.html] --> B
        
        B --> F[populateYearOptions]
        B --> G[populateMonthOptions]
        B --> H[extractYearsFromExistingData]
        B --> I[extractMonthsFromExistingData]
    end
    
    subgraph "API Layer"
        J[/api/ctp-production-logs/years]
        K[/api/ctp-production-logs/months]
        L[/api/chemical-bon-ctp/years]
        M[/api/chemical-bon-ctp/months]
        
        N[/get-kpi-data]
        O[/get-stock-opname-data]
        P[/api/chemical-bon-ctp/list]
    end
    
    subgraph "Backend Layer"
        Q[CtpProductionLog Model]
        R[ChemicalBonCTP Model]
        S[Database - ctp_db]
        
        Q --> S
        R --> S
    end
    
    F --> J
    F --> L
    G --> K
    G --> M
    H --> N
    H --> O
    H --> P
    I --> N
    I --> O
    I --> P
    
    J --> Q
    K --> Q
    L --> R
    M --> R
    N --> Q
    O --> Q
    P --> R
```

## Implementation Flow Diagram

```mermaid
sequenceDiagram
    participant User
    participant Frontend
    participant API
    participant Backend
    participant Database
    
    User->>Frontend: Load page
    Frontend->>Frontend: Initialize filters
    
    Note over Frontend: Year Population Flow
    Frontend->>API: GET /api/{module}/years
    alt API Success
        API-->>Frontend: {success: true, years: [2024, 2023, 2022]}
        Frontend->>Frontend: Populate year select
    else API Failure
        API-->>Frontend: Error response
        Frontend->>API: GET /api/{module}/list (fallback)
        API-->>Frontend: Full data list
        Frontend->>Frontend: Extract years from data
        Frontend->>Frontend: Populate year select
    end
    
    User->>Frontend: Select year
    Frontend->>Frontend: Trigger month population
    
    Note over Frontend: Month Population Flow
    Frontend->>API: GET /api/{module}/months?year=2024
    alt API Success
        API-->>Frontend: {success: true, months: [1, 2, 3, 12]}
        Frontend->>Frontend: Populate month select
    else API Failure
        API-->>Frontend: Error response
        Frontend->>API: GET /api/{module}/list (fallback)
        API-->>Frontend: Full data list
        Frontend->>Frontend: Extract months from data for 2024
        Frontend->>Frontend: Populate month select
    end
    
    User->>Frontend: Apply filters
    Frontend->>API: GET /api/{module}/list?year=2024&month=3
    API->>Backend: Query database with filters
    Backend->>Database: SELECT * FROM table WHERE YEAR(date)=2024 AND MONTH(date)=3
    Database-->>Backend: Filtered results
    Backend-->>API: Processed data
    API-->>Frontend: {success: true, data: [...]}
    Frontend->>Frontend: Update table with filtered data
```

## Error Handling Flow

```mermaid
graph TD
    A[Start Filter Population] --> B[Try API Endpoint]
    B --> C{API Response Success?}
    C -->|Yes| D[Parse Response Data]
    C -->|No| E[Log Error]
    E --> F[Try Fallback Method]
    
    D --> G{Data Valid?}
    G -->|Yes| H[Populate Filter Options]
    G -->|No| F
    
    F --> I[Fetch Full Data List]
    I --> J{Data Fetch Success?}
    J -->|Yes| K[Extract Date Information]
    J -->|No| L[Show Error Message]
    
    K --> M[Parse Years/Months]
    M --> N[Populate Filter Options]
    
    L --> O[Use Static Options]
    H --> P[Success]
    N --> P
    O --> Q[Graceful Degradation]
```

## Data Flow Architecture

```mermaid
graph LR
    subgraph "Client Side"
        A[Browser] --> B[JavaScript Functions]
        B --> C[DOM Elements]
        C --> D[Filter Selects]
    end
    
    subgraph "Network Layer"
        E[HTTP Requests] --> F[API Endpoints]
        F --> G[Response Processing]
    end
    
    subgraph "Server Side"
        H[Flask Routes] --> I[Business Logic]
        I --> J[Database Queries]
        J --> K[SQLAlchemy ORM]
        K --> L[Database Connection]
    end
    
    D --> E
    G --> B
    H --> F
    L --> M[(ctp_db)]
```

## Component Interaction Matrix

| Component | Responsibility | Data Source | Output |
|-----------|----------------|--------------|---------|
| `populateYearOptions()` | Fetch available years | API or fallback data | Year select options |
| `populateMonthOptions()` | Fetch available months for year | API or fallback data | Month select options |
| `extractYearsFromExistingData()` | Fallback year extraction | Full data list | Year array |
| `extractMonthsFromExistingData()` | Fallback month extraction | Full data list | Month array |
| `/api/ctp-production-logs/years` | Backend year service | ctp_production_logs.log_date | JSON years list |
| `/api/ctp-production-logs/months` | Backend month service | ctp_production_logs.log_date | JSON months list |
| `/api/chemical-bon-ctp/years` | Backend year service | chemical_bon_ctp.tanggal | JSON years list |
| `/api/chemical-bon-ctp/months` | Backend month service | chemical_bon_ctp.tanggal | JSON months list |

## Technology Stack

### Frontend
- **HTML5**: Template structure
- **Bootstrap 5**: UI components
- **JavaScript ES6+**: Dynamic functionality
- **Fetch API**: HTTP requests

### Backend
- **Flask**: Web framework
- **SQLAlchemy**: ORM
- **SQLite/MySQL**: Database
- **Python 3.8+**: Runtime

### Database Schema
```sql
-- ctp_production_logs table
CREATE TABLE ctp_production_logs (
    id INTEGER PRIMARY KEY,
    log_date DATE NOT NULL,
    -- other fields...
);

-- chemical_bon_ctp table  
CREATE TABLE chemical_bon_ctp (
    id INTEGER PRIMARY KEY,
    tanggal DATE NOT NULL,
    -- other fields...
);
```

## Performance Considerations

### Database Optimization
- Add indexes on date columns: `CREATE INDEX idx_log_date ON ctp_production_logs(log_date)`
- Use efficient date extraction queries
- Implement query result caching

### Frontend Optimization
- Debounce filter change events
- Implement loading indicators
- Cache API responses locally
- Use async/await for non-blocking operations

### Network Optimization
- Minimize API calls through intelligent caching
- Use appropriate HTTP status codes
- Implement request timeouts
- Compress API responses

## Security Considerations

### API Security
- Require authentication for all endpoints
- Validate input parameters
- Implement rate limiting
- Use HTTPS in production

### Data Validation
- Sanitize user inputs
- Validate date formats
- Handle SQL injection prevention
- Implement proper error messages

## Monitoring & Logging

### Frontend Monitoring
- Console error logging
- User interaction tracking
- Performance metrics
- Error reporting

### Backend Monitoring
- API request logging
- Database query performance
- Error tracking
- Resource usage monitoring