# Menu Structure Visualization

## Current Menu Structure
```mermaid
graph TD
    A[Dashboard Impact] --> B[CTP Production]
    A --> C[Press Production]
    A --> D[Mounting Production]
    A --> E[PDND Production]
    A --> F[Design Production]
    A --> G[Administrator]
    A --> H[Settings]
    
    B --> B1[Dashboard]
    B --> B2[KPI CTP]
    B --> B3[Adjustment Press]
    B --> B4[Bon Press]
    B --> B5[Stock Opname]
    B --> B6[Bon Chemical CTP]
    B --> B7[Kartu Stock CTP]
    
    C --> C1[Adjustment Press]
    C --> C2[Bon Press]
    
    D --> D1[Dashboard]
    D --> D2[Adjustment Curve]
    D --> D3[Adjustment Press]
    
    E --> E1[Adjustment Press]
    
    F --> F1[Adjustment Press]
```

## New Menu Structure
```mermaid
graph TD
    A[Dashboard Impact] --> P[Prepress Production]
    A --> C[Press Production]
    A --> E[PDND Production]
    A --> G[Administrator]
    A --> H[Settings]
    
    P --> B[CTP Production]
    P --> D[Mounting Production]
    P --> F[Design Production]
    
    B --> B1[Dashboard]
    B --> B2[KPI CTP]
    B --> B3[Adjustment Press]
    B --> B4[Bon Press]
    B --> B5[Stock Opname]
    B --> B6[Bon Chemical CTP]
    B --> B7[Kartu Stock CTP]
    
    D --> D1[Dashboard]
    D --> D2[Adjustment Curve]
    D --> D3[Adjustment Press]
    
    F --> F1[Adjustment Press]
    
    C --> C1[Adjustment Press]
    C --> C2[Bon Press]
    
    E --> E1[Adjustment Press]
```

## Access Control Logic
- **Prepress Production**: Visible if `can_access_ctp()` OR `can_access_mounting()` OR `can_access_design()`
- **CTP Production**: Visible if `can_access_ctp()`
- **Mounting Production**: Visible if `can_access_mounting()`
- **Design Production**: Visible if `can_access_design()`
- **Press Production**: Visible if `can_access_press()` OR `can_access_ctp()` OR `can_access_mounting()` OR `can_access_pdnd()` OR `can_access_design()`
- **PDND Production**: Visible if `can_access_pdnd()`