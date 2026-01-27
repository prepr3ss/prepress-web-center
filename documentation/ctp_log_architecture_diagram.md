# CTP Log System Architecture

## System Overview

```mermaid
graph TB
    subgraph "Frontend Layer"
        A[Log CTP Overview] --> B[Machine Detail Page]
        B --> C[Problem Form]
        B --> D[Problem List]
        A --> E[Recent Problems]
    end
    
    subgraph "Backend Layer"
        F[Flask Routes] --> G[API Endpoints]
        G --> H[Business Logic]
        H --> I[Database Models]
    end
    
    subgraph "Data Layer"
        I --> J[CTPMachine Table]
        I --> K[CTPProblemLog Table]
        I --> L[CTPNotification Table]
        I --> M[Users Table]
    end
    
    subgraph "File Storage"
        N[Upload Folder] --> O[Problem Photos]
    end
    
    A --> F
    C --> G
    G --> N
```

## Database Schema

```mermaid
erDiagram
    CTPMachine {
        int id PK
        string name
        string nickname
        string status
        text description
        datetime created_at
        datetime updated_at
    }
    
    CTPProblemLog {
        int id PK
        int machine_id FK
        datetime problem_date
        text problem_description
        string problem_photo
        text solution
        string technician_type
        string technician_name
        datetime start_time
        datetime end_time
        string status
        int created_by FK
        datetime created_at
        datetime updated_at
    }
    
    CTPNotification {
        int id PK
        int machine_id FK
        int log_id FK
        string notification_type
        text message
        boolean is_read
        datetime created_at
        datetime read_at
    }
    
    User {
        int id PK
        string username
        string name
        string role
        int division_id FK
    }
    
    CTPMachine ||--o{ CTPProblemLog : "has many"
    CTPMachine ||--o{ CTPNotification : "has many"
    CTPProblemLog ||--o{ CTPNotification : "generates"
    User ||--o{ CTPProblemLog : "creates"
```

## User Flow

```mermaid
flowchart TD
    A[User Login] --> B{Access Level Check}
    B -->|CTP User/Admin| C[Access Log CTP Menu]
    B -->|No Access| D[Redirect to Dashboard]
    
    C --> E[Overview Page]
    E --> F[View Machine Status]
    E --> G[View Recent Problems]
    
    F --> H[Click Machine]
    H --> I[Machine Detail Page]
    
    I --> J[View Statistics]
    I --> K[View Problem History]
    I --> L[Add New Problem]
    
    L --> M[Fill Problem Form]
    M --> N[Upload Photo]
    N --> O[Save Problem]
    
    O --> P[Create Notification]
    P --> Q[Update Machine Status]
    Q --> R[Refresh Page]
    
    K --> S[Complete Problem]
    S --> T[Calculate Downtime]
    T --> U[Update Status]
    U --> V[Create Resolution Notification]
```

## API Endpoints Structure

```mermaid
graph LR
    subgraph "GET Endpoints"
        A1[/api/ctp-machines]
        A2[/api/ctp-problem-logs]
        A3[/api/ctp-notifications]
    end
    
    subgraph "POST Endpoints"
        B1[/api/ctp-problem-logs]
    end
    
    subgraph "PUT Endpoints"
        C1[/api/ctp-problem-logs/:id]
        C2[/api/ctp-notifications/:id/read]
    end
    
    subgraph "DELETE Endpoints"
        D1[/api/ctp-problem-logs/:id]
    end
    
    A1 --> E[Get All Machines]
    A2 --> F[Get Problem Logs with Filters]
    A3 --> G[Get Unread Notifications]
    B1 --> H[Create New Problem Log]
    C1 --> I[Update Problem Log]
    C2 --> J[Mark Notification as Read]
    D1 --> K[Delete Problem Log]
```

## Component Interaction

```mermaid
sequenceDiagram
    participant U as User
    participant F as Frontend
    participant A as API
    participant D as Database
    participant S as Storage
    
    U->>F: Open Log CTP Page
    F->>A: GET /api/ctp-machines
    A->>D: Query CTPMachine table
    D-->>A: Return machine data
    A-->>F: JSON response
    F-->>U: Display machine cards
    
    U->>F: Click "Add Problem"
    F-->>U: Show problem form
    U->>F: Fill form & upload photo
    F->>A: POST /api/ctp-problem-logs
    A->>S: Save photo file
    A->>D: Insert problem log
    A->>D: Create notification
    D-->>A: Success response
    A-->>F: JSON response
    F-->>U: Show success message
    F->>F: Refresh problem list
```

## File Structure

```
impact/
├── templates/
│   ├── _sidebar.html (modified)
│   ├── log_ctp_overview.html (new)
│   └── log_ctp_detail.html (new)
├── static/
│   └── js/
│       ├── log_ctp_handler.js (new)
│       └── log_ctp_detail_handler.js (new)
├── uploads/
│   └── ctp_problems/ (new)
├── app.py (modified)
├── config.py (modified)
└── migrations/
    └── versions/
        └── create_ctp_log_tables.py (new)
```

## Security Considerations

```mermaid
graph TD
    A[Authentication Check] --> B{User Role}
    B -->|Admin| C[Full Access]
    B -->|CTP User| D[Limited Access]
    B -->|Other| E[No Access]
    
    C --> F[Can View All Machines]
    C --> G[Can Add/Edit/Delete Problems]
    
    D --> H[Can View Assigned Machines]
    D --> I[Can Add Problems]
    D --> J[Can Edit Own Problems]
    
    E --> K[Redirect to Dashboard]
    
    F --> L[File Upload Validation]
    G --> L
    H --> L
    I --> L
    J --> L
    
    L --> M[Check File Type]
    M --> N[Check File Size]
    N --> O[Sanitize Filename]
    O --> P[Save to Secure Location]
```

## Performance Optimization

```mermaid
graph LR
    A[Database Indexes] --> B[Faster Queries]
    C[Image Compression] --> D[Reduced Storage]
    E[Pagination] --> F[Improved Load Times]
    G[Caching] --> H[Reduced Database Load]
    
    subgraph "Database Optimization"
        I[Index on machine_id]
        J[Index on created_at]
        K[Index on status]
    end
    
    subgraph "Frontend Optimization"
        L[Lazy Loading Images]
        M[Debounced Search]
        N[Virtual Scrolling]
    end
```

## Notification System Flow

```mermaid
stateDiagram-v2
    [*] --> NewProblem: Problem Created
    NewProblem --> NotificationGenerated: Create Notification
    NotificationGenerated --> Unread: Notification Saved
    Unread --> Read: User Views Notification
    Read --> [*]
    
    Unread --> AutoRead: Mark as Read after 7 days
    AutoRead --> [*]
    
    NewProblem --> ProblemResolved: Problem Completed
    ProblemResolved --> ResolutionNotification: Create Resolution Notification
    ResolutionNotification --> Unread
```

## Error Handling Strategy

```mermaid
graph TD
    A[API Request] --> B{Validation}
    B -->|Pass| C[Process Request]
    B -->|Fail| D[Return 400 Error]
    
    C --> E{Database Operation}
    E -->|Success| F[Return Success Response]
    E -->|Error| G[Log Error]
    
    G --> H{Error Type}
    H -->|Database Error| I[Return 500 Error]
    H -->|File Upload Error| J[Return 413 Error]
    H -->|Authorization Error| K[Return 403 Error]
    
    D --> L[Show Client Error Message]
    I --> M[Show Server Error Message]
    J --> N[Show File Size Error]
    K --> O[Show Access Denied Message]
```

## Deployment Architecture

```mermaid
graph TB
    subgraph "Production Environment"
        A[Load Balancer] --> B[Web Server 1]
        A --> C[Web Server 2]
        
        B --> D[Application Server]
        C --> D
        
        D --> E[Database Cluster]
        D --> F[File Storage]
        
        G[Monitoring] --> D
        H[Backup System] --> E
        H --> F
    end
    
    subgraph "Development Environment"
        I[Local Server] --> J[Local Database]
        I --> K[Local Storage]
    end