# KPI Individual Scores Calculation Documentation

## Overview
Individual KPI Scores measure the **average duration (in days) required for each PIC to complete each stage**, calculated per month.

---

## Calculation Formula

```
KPI Score = Total Days Spent on Stage ÷ Number of Jobs Completed in that Stage
```

### Example:
```
Abdul Haris Halim - Design Stage (January 2026):
- 9 jobs where Abdul was PIC for Design stage
- Total days: 52.92 days (across all 9 jobs)
- Average: 52.92 ÷ 9 = 5.88 days per job
```

---

## Step-by-Step Calculation Logic

### 1. Filter Assignments (by Completion Month)
```
WHERE:
  - PIC = Selected User
  - Stage = Selected Stage (e.g., "Design & Artwork Approval")
  - Status = "completed"
  - finished_at BETWEEN [Month Start] AND [Month End]
```

**Example:** January 2026 = 2026-01-01 to 2026-02-01

---

### 2. For Each Completed Assignment, Calculate Duration

```
Start Time = PREVIOUS step's finished_at
End Time = CURRENT step's finished_at
Duration = End Time - Start Time
```

**Timeline Example (from actual data):**

```
Job: RND-20260103-001
Timeline:
├─ Step 1 (Job Created): 2025-12-29 15:49:00
├─ Step 2 (Design): 2026-01-04 13:00:24
│  └─ Duration: Dec 29 15:49 → Jan 4 13:00 = 5.88 days
│
└─ Step 3 (Mastercard): 2026-01-12 12:05:48
   └─ Duration: Jan 4 13:00 → Jan 12 12:05 = 7.96 days
```

---

### 3. Handle First Step Specially

**For Design & Artwork Approval** (usually first step):
- Start Time = `job.started_at` (job creation date)
- End Time = `design_assignment.finished_at`

**For Other Stages:**
- Start Time = Previous step's `finished_at`
- End Time = Current step's `finished_at`

---

### 4. Calculate Average

```
Average Days = Sum of All Durations ÷ Count of Jobs Completed
```

**Example Calculation:**
```
Abdul Haris Halim - Design (9 jobs in January):

Job 1 (RND-20260103-001): 5.88 days
Job 2 (RND-20260108-001): 4.83 days
Job 3 (RND-20260108-002): 4.83 days
Job 4 (RND-20260108-003): 4.83 days
Job 5 (RND-20260108-004): 4.83 days
Job 6 (RND-20260108-005): 4.83 days
Job 7 (RND-20260108-006): 4.83 days
Job 8 (RND-20260108-???): X.XX days
Job 9 (RND-20260108-???): X.XX days
─────────────────────────────────
Total:                     52.92 days
Count:                     9 jobs
Average:                   52.92 ÷ 9 = 5.88 days/job
```

---

## Month Attribution

**Important:** Score is attributed to the **completion month**, not the start month.

```
If a job:
- Starts: January 15
- Design finishes: January 20 ✅ Counts in JANUARY
- Mastercard finishes: February 5 ✅ Counts in FEBRUARY (not January!)
```

This ensures each stage's score reflects actual work completed **in that month**, not work that started in that month.

---

## What This Score Represents

| Score | Interpretation |
|-------|-----------------|
| **5.88 days** | Average: Each Design job took 5.88 days to complete for this PIC |
| **10.5 days** | Average: Each Mastercard job took 10.5 days for this PIC |
| **0.0 days** | No jobs completed by this PIC in this stage this month |

---

## Dashboard Display

### Format: `[Average Days] [Unit Label]`

**Example:**
```
Abdul Haris Halim
└─ Design:       5.88 hari  (5.88 days)
└─ Mastercard:   0.00 hari  (no jobs completed)
└─ Blank:        0.00 hari  (no jobs completed)
```

---

## Key Points for Management

✅ **What it measures:**
- Individual productivity per stage
- Average time required to complete each stage
- Performance trends month-to-month

✅ **How to use it:**
- Compare between users: Who completes Design faster?
- Compare between months: Is performance improving?
- Identify bottlenecks: Which stages take longest?

⚠️ **Important notes:**
- Includes ALL jobs assigned to the user in that stage
- Calculated from step-to-step completion, not total job time
- Attributed to completion month, not start month
- Zero score means no jobs completed in that stage/month

---

## Database Tables Involved

```
rnd_job_progress_assignments:
├─ pic_id (User assigned to this stage)
├─ job_id (Job being worked on)
├─ progress_step_id (Which stage: Design, Mastercard, etc.)
├─ status (completed / pending / in_progress)
├─ started_at (When this stage started)
└─ finished_at (When this stage finished) ← KEY FIELD

rnd_progress_steps:
└─ name (Design & Artwork Approval, Mastercard Release, etc.)

rnd_jobs:
└─ started_at (Job creation time, used as baseline for first step)
```

---

## Verification Steps

To verify a score is correct:

1. **Find the user in the dashboard**
2. **Select the month** you want to verify
3. **Click on their stage** (e.g., Design)
4. **Check the server logs** (when debug is enabled):
   ```
   DEBUG Scores: Stage 'Design' for user 'Abdul Haris Halim':
     Total assignments found: 9
     Assignment #1: RND-20260103-001: 5.88 days
     Assignment #2: RND-20260108-001: 4.83 days
     ...
     Total: 52.92 days
     Completed jobs: 9
     Average: 5.88 days per job
   ```

---

## Implementation Details

**File:** `rnd_cloudsphere.py`  
**Endpoint:** `/api/dashboard-individual-scores`  
**Filter:** By `RNDJobProgressAssignment.finished_at` (completion month)

**Calculation Logic:**
- For each stage, find all completed assignments by this user in this month
- For each assignment, calculate time from previous step to current step
- Average all durations
- Return as days (rounded to 2 decimals)
