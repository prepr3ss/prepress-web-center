# Arsitektur Sistem Work Order Incoming

## 1. Diagram Arsitektur Sistem

```mermaid
graph TB
    subgraph "Frontend Layer"
        UI[HTML Template<br/>mounting_work_order_incoming.html]
        JS[JavaScript<br/>mounting_work_order_incoming.js]
        CSS[CSS Styling<br/>Custom Styles]
    end
    
    subgraph "Application Layer"
        ROUTE[Flask Routes<br/>/mounting-work-order-incoming]
        API[REST API<br/>/api/mounting-work-order-incoming]
        AUTH[Authentication<br/>Session Management]
    end
    
    subgraph "Business Logic Layer"
        CTRL[Controller<br/>WorkOrderController]
        VALID[Validation<br/>DataValidator]
        BIZ[Business Logic<br/>WorkOrderService]
    end
    
    subgraph "Data Layer"
        MODEL[Data Model<br/>MountingWorkOrderIncoming]
        DB[(Database<br/>SQLite/MySQL)]
        MIGRATION[Database Migration<br/>Alembic]
    end
    
    subgraph "External Systems"
        PPIC[PPIC Division<br/>Work Order Source]
        MOUNTING[Mounting Division<br/>Work Order Consumer]
    end
    
    UI --> JS
    JS --> API
    API --> ROUTE
    ROUTE --> CTRL
    CTRL --> VALID
    VALID --> BIZ
    BIZ --> MODEL
    MODEL --> DB
    
    PPIC --> UI
    UI --> MOUNTING
    
    MIGRATION --> DB
```

## 2. Data Flow Diagram

```mermaid
sequenceDiagram
    participant User as User (Mounting)
    participant UI as Frontend UI
    participant API as REST API
    participant CTRL as Controller
    participant BIZ as Business Logic
    participant DB as Database
    
    User->>UI: 1. Buka halaman Work Order Incoming
    UI->>API: 2. GET /api/mounting-work-order-incoming
    API->>CTRL: 3. Request data
    CTRL->>BIZ: 4. Get work orders
    BIZ->>DB: 5. Query data
    DB-->>BIZ: 6. Return data
    BIZ-->>CTRL: 7. Processed data
    CTRL-->>API: 8. JSON response
    API-->>UI: 9. Display data
    UI-->>User: 10. Show work order list
    
    User->>UI: 11. Input multiple work orders
    UI->>UI: 12. Validate input
    UI->>User: 13. Show verification (X baris)
    User->>UI: 14. Confirm submit
    UI->>API: 15. POST /api/mounting-work-order-incoming/batch
    API->>CTRL: 16. Batch create request
    CTRL->>BIZ: 17. Process batch data
    BIZ->>DB: 18. Insert multiple records
    DB-->>BIZ: 19. Success confirmation
    BIZ-->>CTRL: 20. Result summary
    CTRL-->>API: 21. Response with summary
    API-->>UI: 22. Success message
    UI-->>User: 23. Show success notification
```

## 3. Component Architecture

```mermaid
graph LR
    subgraph "Frontend Components"
        A[Input Table Component]
        B[Data Table Component]
        C[Filter Component]
        D[Modal Component]
        E[Validation Component]
    end
    
    subgraph "Backend Components"
        F[Route Handler]
        G[API Controller]
        H[Service Layer]
        I[Repository Layer]
        J[Model Layer]
    end
    
    subgraph "Database Components"
        K[Work Order Table]
        L[Index Tables]
        M[Audit Tables]
    end
    
    A --> E
    B --> C
    D --> A
    E --> F
    F --> G
    G --> H
    H --> I
    I --> J
    J --> K
    K --> L
    K --> M
```

## 4. State Management

```mermaid
stateDiagram-v2
    [*] --> Incoming
    Incoming --> Processed: Process Work Order
    Incoming --> Cancelled: Cancel Work Order
    Processed --> [*]: Complete
    Cancelled --> [*]: Archive
    
    note right of Incoming
        Status: incoming
        - Data dari PPIC
        - Belum diproses
        - Bisa diedit
    end note
    
    note right of Processed
        Status: processed
        - Sudah diproses
        - Tidak bisa diedit
        - Ada processed_at
    end note
    
    note right of Cancelled
        Status: cancelled
        - Dibatalkan
        - Tidak bisa diedit
        - Ada alasan pembatalan
    end note
```

## 5. Database Schema

```mermaid
erDiagram
    MOUNTING_WORK_ORDER_INCOMING {
        int id PK
        datetime incoming_datetime
        string wo_number UK
        string mc_number
        string customer_name
        string item_name
        string print_block
        string print_machine
        int run_length_sheet
        string sheet_size
        string paper_type
        string status
        datetime processed_at
        string processed_by
        datetime created_at
        datetime updated_at
        string created_by
    }
    
    USERS {
        int id PK
        string username UK
        string name
        string role
        datetime created_at
    }
    
    MOUNTING_WORK_ORDER_INCOMING ||--o{ USERS : "created_by"
    MOUNTING_WORK_ORDER_INCOMING ||--o| USERS : "processed_by"
```

## 6. API Request Flow

```mermaid
flowchart TD
    START([Start Request]) --> AUTH{Check Authentication}
    AUTH -->|Not Authenticated| ERROR1[Return 401 Unauthorized]
    AUTH -->|Authenticated| VALIDATE{Validate Request}
    VALIDATE -->|Invalid| ERROR2[Return 400 Bad Request]
    VALIDATE -->|Valid| PROCESS{Process Request}
    PROCESS -->|GET| GET_DATA[Get Data from DB]
    PROCESS -->|POST| CREATE_DATA[Create Data in DB]
    PROCESS -->|PUT| UPDATE_DATA[Update Data in DB]
    PROCESS -->|DELETE| DELETE_DATA[Delete Data from DB]
    
    GET_DATA --> RESPONSE[Return JSON Response]
    CREATE_DATA --> RESPONSE
    UPDATE_DATA --> RESPONSE
    DELETE_DATA --> RESPONSE
    
    ERROR1 --> END([End Request])
    ERROR2 --> END
    RESPONSE --> END
```

## 7. Frontend Component Structure

```mermaid
graph TD
    APP[Main Application] --> HEADER[Page Header]
    APP --> INPUT[Input Section]
    APP --> DATA[Data Section]
    
    INPUT --> TABLE[Input Table]
    INPUT --> BUTTONS[Action Buttons]
    INPUT --> VERIFICATION[Row Verification]
    
    DATA --> FILTER[Filter Section]
    DATA --> DATATABLE[Data Table]
    DATA --> PAGINATION[Pagination]
    
    TABLE --> ROWS[Dynamic Rows]
    TABLE --> VALIDATION[Field Validation]
    
    FILTER --> DATE_FILTER[Date Filter]
    FILTER --> STATUS_FILTER[Status Filter]
    FILTER --> SEARCH[Search Box]
    
    DATATABLE --> ROWS_DATA[Data Rows]
    DATATABLE --> ACTIONS[Row Actions]
    
    MODAL[Confirmation Modal] --> APP
    NOTIFICATION[Toast Notification] --> APP
```

## 8. Security Architecture

```mermaid
graph TB
    subgraph "Security Layers"
        AUTH[Authentication Layer]
        AUTHZ[Authorization Layer]
        VALID[Input Validation]
        SANITIZE[Data Sanitization]
        AUDIT[Audit Logging]
    end
    
    subgraph "Security Measures"
        SESSION[Session Management]
        CSRF[CSRF Protection]
        XSS[XSS Prevention]
        SQL[SQL Injection Prevention]
        RATE[Rate Limiting]
    end
    
    AUTH --> SESSION
    AUTHZ --> CSRF
    VALID --> XSS
    SANITIZE --> SQL
    AUDIT --> RATE
```

## 9. Performance Optimization

```mermaid
graph LR
    subgraph "Frontend Optimization"
        LAZY[Lazy Loading]
        DEBOUNCE[Debouncing]
        CACHE[Client Cache]
        MINIFY[Minification]
    end
    
    subgraph "Backend Optimization"
        INDEX[Database Index]
        POOL[Connection Pooling]
        CACHE2[Server Cache]
        PAGINATION[Pagination]
    end
    
    subgraph "Network Optimization"
        COMPRESS[Compression]
        CDN[CDN Usage]
        HTTP2[HTTP/2]
        ASYNC[Async Operations]
    end
    
    LAZY --> CACHE
    DEBOUNCE --> CACHE2
    INDEX --> PAGINATION
    COMPRESS --> CDN
```

## 10. Deployment Architecture

```mermaid
graph TB
    subgraph "Production Environment"
        LB[Load Balancer]
        WEB1[Web Server 1]
        WEB2[Web Server 2]
        DB[(Database)]
        FILES[File Storage]
    end
    
    subgraph "Development Environment"
        DEV[Development Server]
        DEVDB[(Dev Database)]
        DEVFILES[Dev File Storage]
    end
    
    subgraph "Testing Environment"
        TEST[Testing Server]
        TESTDB[(Test Database)]
        TESTFILES[Test File Storage]
    end
    
    LB --> WEB1
    LB --> WEB2
    WEB1 --> DB
    WEB2 --> DB
    WEB1 --> FILES
    WEB2 --> FILES
    
    DEV --> DEVDB
    DEV --> DEVFILES
    
    TEST --> TESTDB
    TEST --> TESTFILES
```

## 11. Monitoring and Logging

```mermaid
graph TD
    subgraph "Monitoring Components"
        LOG[Application Logs]
        ERROR[Error Tracking]
        PERF[Performance Metrics]
        USER[User Activity]
    end
    
    subgraph "Alerting System"
        EMAIL[Email Alerts]
        SLACK[Slack Notifications]
        DASHBOARD[Monitoring Dashboard]
    end
    
    subgraph "Log Storage"
        FILES2[Log Files]
        DB2[Log Database]
        SIEM[SIEM System]
    end
    
    LOG --> FILES2
    ERROR --> DB2
    PERF --> DASHBOARD
    USER --> SIEM
    
    FILES2 --> EMAIL
    DB2 --> SLACK
    DASHBOARD --> EMAIL
    SIEM --> SLACK
```

## 12. Integration Points

```mermaid
graph LR
    subgraph "Internal Systems"
        WO[Work Order System]
        USER_MGMT[User Management]
        AUTH_SYSTEM[Authentication System]
        NOTIF[Notification System]
    end
    
    subgraph "External Systems"
        PPIC_SYS[PPIC System]
        ERP[ERP System]
        EMAIL_SRV[Email Service]
    end
    
    subgraph "Work Order Incoming"
        WOI[Work Order Incoming Module]
    end
    
    PPIC_SYS --> WOI
    WOI --> WO
    WOI --> USER_MGMT
    WOI --> AUTH_SYSTEM
    WOI --> NOTIF
    WOI --> ERP
    NOTIF --> EMAIL_SRV
```

## 13. Technology Stack

```mermaid
graph TB
    subgraph "Frontend Stack"
        HTML5[HTML5]
        CSS3[CSS3]
        JS[JavaScript ES6+]
        BOOTSTRAP[Bootstrap 5]
        FONTAWESOME[Font Awesome]
    end
    
    subgraph "Backend Stack"
        PYTHON[Python 3.9+]
        FLASK[Flask]
        SQLALCHEMY[SQLAlchemy]
        ALEMBIC[Alembic]
        JWT[JWT Tokens]
    end
    
    subgraph "Database Stack"
        SQLITE[SQLite]
        MYSQL[MySQL]
        REDIS[Redis Cache]
    end
    
    subgraph "DevOps Stack"
        DOCKER[Docker]
        NGINX[Nginx]
        GUNICORN[Gunicorn]
        GIT[Git]
    end
    
    HTML5 --> BOOTSTRAP
    CSS3 --> BOOTSTRAP
    JS --> FONTAWESOME
    
    PYTHON --> FLASK
    FLASK --> SQLALCHEMY
    FLASK --> ALEMBIC
    FLASK --> JWT
    
    SQLALCHEMY --> SQLITE
    SQLALCHEMY --> MYSQL
    FLASK --> REDIS
    
    DOCKER --> NGINX
    NGINX --> GUNICORN
    GUNICORN --> FLASK
```

## 14. Development Workflow

```mermaid
gitgraph
    commit id: "Initial Setup"
    branch feature-model
    checkout feature-model
    commit id: "Create Database Model"
    checkout main
    merge feature-model
    
    branch feature-api
    checkout feature-api
    commit id: "Implement API Endpoints"
    checkout main
    merge feature-api
    
    branch feature-ui
    checkout feature-ui
    commit id: "Create HTML Template"
    commit id: "Implement JavaScript"
    checkout main
    merge feature-ui
    
    branch feature-integration
    checkout feature-integration
    commit id: "Integrate Components"
    commit id: "Add Navigation Menu"
    checkout main
    merge feature-integration
    
    branch testing
    checkout testing
    commit id: "Unit Tests"
    commit id: "Integration Tests"
    commit id: "Bug Fixes"
    checkout main
    merge testing
    
    commit id: "Production Release"
```

## 15. Risk Assessment

```mermaid
mindmap
  root((Risks))
    Technical Risks
      Database Performance
      API Scalability
      Frontend Compatibility
      Security Vulnerabilities
    Business Risks
      User Adoption
      Data Quality
      Process Integration
      Training Requirements
    Operational Risks
      System Downtime
      Data Loss
      Backup Failure
      Recovery Time
    Mitigation Strategies
      Performance Testing
      Security Audits
      User Training
      Backup Planning
      Monitoring Systems