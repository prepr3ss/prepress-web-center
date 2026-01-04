#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Simple debug to check if issues remain"""

from app import app, db
from models_rnd import RNDJob, RNDJobProgressAssignment

with app.app_context():
    print("\nChecking for completion inconsistencies...\n")
    
    issues = []
    all_jobs = RNDJob.query.all()
    
    for job in all_jobs:
        if job.completion_percentage == 100 and job.status != 'completed':
            issues.append(job)
            print(f"ISSUE: {job.job_id} - Completion: 100%, Status: {job.status}")
    
    if not issues:
        print("SUCCESS! No issues found. All jobs with 100% completion have status='completed'")
    else:
        print(f"\nTotal issues: {len(issues)}")
        for job in issues:
            all_assignments = RNDJobProgressAssignment.query.filter_by(job_id=job.id).all()
            print(f"  Job {job.job_id}:")
            for a in all_assignments:
                print(f"    - {a.progress_step.name}: {a.status}")
    
    # CRITICAL: Commit any changes made by property auto-sync
    print("\nCommitting any changes from auto-sync property...")
    db.session.commit()
    print("Done!")
