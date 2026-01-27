"""
Unit tests for R&D Cloudsphere Dashboard API endpoints
"""

import pytest
from datetime import datetime, timedelta
import pytz
from models import db, User, Division
from models_rnd import (
    RNDJob, RNDProgressStep, RNDProgressTask, RNDJobProgressAssignment,
    RNDJobTaskAssignment, RNDFlowConfiguration
)

# Jakarta timezone
jakarta_tz = pytz.timezone('Asia/Jakarta')


class TestDashboardAvailablePeriods:
    """Test /api/dashboard-available-periods endpoint"""

    def test_available_periods_returns_years(self, client, rnd_user):
        """Test that endpoint returns list of available years"""
        # Login as RND user
        client.post('/login', data={
            'username': rnd_user.username,
            'password': 'password'
        })

        response = client.get('/rnd-cloudsphere/api/dashboard-available-periods')
        
        assert response.status_code == 200
        data = response.get_json()
        assert data['success'] is True
        assert 'years' in data
        assert isinstance(data['years'], list)

    def test_available_periods_empty_when_no_jobs(self, client, rnd_user, app):
        """Test that endpoint returns empty list when no jobs exist"""
        # Clear jobs
        RNDJob.query.delete()
        db.session.commit()

        client.post('/login', data={
            'username': rnd_user.username,
            'password': 'password'
        })

        response = client.get('/rnd-cloudsphere/api/dashboard-available-periods')
        
        assert response.status_code == 200
        data = response.get_json()
        assert data['success'] is True
        assert len(data['years']) == 0

    def test_available_periods_descending_order(self, client, rnd_user, app):
        """Test that years are returned in descending order"""
        # Create jobs for different years
        years = [2021, 2023, 2022]
        for year in years:
            job = RNDJob(
                job_id=f'RND-{year}0101-001',
                item_name=f'Test Job {year}',
                sample_type='Blank',
                priority_level='middle',
                started_at=jakarta_tz.localize(datetime(year, 1, 1)),
                deadline_at=jakarta_tz.localize(datetime(year, 2, 1)),
                status='in_progress'
            )
            db.session.add(job)
        db.session.commit()

        client.post('/login', data={
            'username': rnd_user.username,
            'password': 'password'
        })

        response = client.get('/rnd-cloudsphere/api/dashboard-available-periods')
        data = response.get_json()
        
        assert data['years'] == [2023, 2022, 2021]


class TestDashboardAvailableMonths:
    """Test /api/dashboard-available-months endpoint"""

    def test_available_months_returns_months_for_year(self, client, rnd_user, app):
        """Test that endpoint returns available months for selected year"""
        # Create jobs for different months
        year = 2024
        for month in [1, 3, 6, 12]:
            job = RNDJob(
                job_id=f'RND-{year}{month:02d}01-001',
                item_name=f'Test Job {month}',
                sample_type='Blank',
                priority_level='middle',
                started_at=jakarta_tz.localize(datetime(year, month, 1)),
                deadline_at=jakarta_tz.localize(datetime(year, month + 1, 1)),
                status='in_progress'
            )
            db.session.add(job)
        db.session.commit()

        client.post('/login', data={
            'username': rnd_user.username,
            'password': 'password'
        })

        response = client.get(f'/rnd-cloudsphere/api/dashboard-available-months?year={year}')
        
        assert response.status_code == 200
        data = response.get_json()
        assert data['success'] is True
        assert 'months' in data
        assert set(data['months']) == {1, 3, 6, 12}

    def test_available_months_requires_year_param(self, client, rnd_user):
        """Test that endpoint requires year parameter"""
        client.post('/login', data={
            'username': rnd_user.username,
            'password': 'password'
        })

        response = client.get('/rnd-cloudsphere/api/dashboard-available-months')
        
        assert response.status_code == 400
        data = response.get_json()
        assert data['success'] is False


class TestDashboardStats:
    """Test /api/dashboard-stats endpoint"""

    def test_dashboard_stats_returns_metrics(self, client, rnd_user, app):
        """Test that endpoint returns correct statistics"""
        # Create test jobs
        year, month = 2024, 1
        now = datetime.now(jakarta_tz)
        
        # Total jobs: 5
        # Blank: 2, RoHS ICB: 2, RoHS Ribbon: 1
        # Completed: 2, Overdue (not completed past deadline): 1
        
        jobs_data = [
            {'sample_type': 'Blank', 'status': 'completed'},
            {'sample_type': 'Blank', 'status': 'in_progress'},
            {'sample_type': 'RoHS ICB', 'status': 'completed'},
            {'sample_type': 'RoHS ICB', 'status': 'in_progress'},
            {'sample_type': 'RoHS Ribbon', 'status': 'in_progress'},
        ]
        
        for i, job_data in enumerate(jobs_data):
            job = RNDJob(
                job_id=f'RND-20240101-{i+1:03d}',
                item_name=f'Test Job {i+1}',
                sample_type=job_data['sample_type'],
                priority_level='middle',
                started_at=jakarta_tz.localize(datetime(2024, 1, 1)),
                deadline=jakarta_tz.localize(datetime(2024, 1, 15)) if i == 4 else jakarta_tz.localize(datetime(2024, 2, 1)),
                status=job_data['status'],
                finished_at=jakarta_tz.localize(datetime(2024, 1, 10)) if job_data['status'] == 'completed' else None
            )
            db.session.add(job)
        
        # Add overdue job (not completed, deadline passed)
        overdue_job = RNDJob(
            job_id='RND-20240101-006',
            item_name='Overdue Job',
            sample_type='Blank',
            priority_level='high',
            started_at=jakarta_tz.localize(datetime(2024, 1, 1)),
            deadline_at=jakarta_tz.localize(datetime(2024, 1, 5)),
            status='in_progress'
        )
        db.session.add(overdue_job)
        db.session.commit()

        client.post('/login', data={
            'username': rnd_user.username,
            'password': 'password'
        })

        response = client.get(f'/rnd-cloudsphere/api/dashboard-stats?year=2024&month=1')
        
        assert response.status_code == 200
        data = response.get_json()
        assert data['success'] is True
        assert 'data' in data
        
        stats = data['data']
        assert stats['total_jobs'] == 6
        assert stats['blank_jobs'] == 3
        assert stats['rohs_icb_jobs'] == 2
        assert stats['rohs_ribbon_jobs'] == 1
        assert stats['completed_jobs'] == 2

    def test_dashboard_stats_whole_year(self, client, rnd_user, app):
        """Test endpoint with whole year (no month specified)"""
        # Create jobs for different months
        for month in range(1, 4):
            job = RNDJob(
                job_id=f'RND-2024{month:02d}01-001',
                item_name=f'Test Job Month {month}',
                sample_type='Blank',
                priority_level='middle',
                started_at=jakarta_tz.localize(datetime(2024, month, 1)),
                deadline_at=jakarta_tz.localize(datetime(2024, month + 1, 1)),
                status='in_progress'
            )
            db.session.add(job)
        db.session.commit()

        client.post('/login', data={
            'username': rnd_user.username,
            'password': 'password'
        })

        response = client.get('/rnd-cloudsphere/api/dashboard-stats?year=2024')
        
        assert response.status_code == 200
        data = response.get_json()
        assert data['success'] is True
        assert data['data']['total_jobs'] == 3


class TestDashboardTrend:
    """Test /api/dashboard-trend endpoint"""

    def test_dashboard_trend_single_month(self, client, rnd_user, app):
        """Test trend endpoint for single month returns daily data"""
        # Create jobs for different days
        year, month = 2024, 1
        
        for day in [5, 5, 10, 15]:  # 2 jobs on day 5, 1 on day 10, 1 on day 15
            job = RNDJob(
                job_id=f'RND-20240105-{day:03d}',
                item_name=f'Test Job {day}',
                sample_type='Blank',
                priority_level='middle',
                started_at=jakarta_tz.localize(datetime(year, month, day)),
                deadline_at=jakarta_tz.localize(datetime(year, month + 1, 1)),
                status='in_progress'
            )
            db.session.add(job)
        db.session.commit()

        client.post('/login', data={
            'username': rnd_user.username,
            'password': 'password'
        })

        response = client.get('/rnd-cloudsphere/api/dashboard-trend?year=2024&month=1')
        
        assert response.status_code == 200
        data = response.get_json()
        assert data['success'] is True
        assert 'labels' in data['data']
        assert 'total' in data['data']
        assert len(data['data']['labels']) > 0

    def test_dashboard_trend_whole_year(self, client, rnd_user, app):
        """Test trend endpoint for whole year returns monthly data"""
        # Create jobs for different months
        for month in [1, 3, 6]:
            for day in range(1, 4):  # 3 jobs per month
                job = RNDJob(
                    job_id=f'RND-2024{month:02d}{day:02d}-001',
                    item_name=f'Test Job {month}-{day}',
                    sample_type='Blank',
                    priority_level='middle',
                    started_at=jakarta_tz.localize(datetime(2024, month, day)),
                    deadline_at=jakarta_tz.localize(datetime(2024, month + 1, 1)),
                    status='in_progress'
                )
                db.session.add(job)
        db.session.commit()

        client.post('/login', data={
            'username': rnd_user.username,
            'password': 'password'
        })

        response = client.get('/rnd-cloudsphere/api/dashboard-trend?year=2024')
        
        assert response.status_code == 200
        data = response.get_json()
        assert data['success'] is True
        assert len(data['data']['labels']) > 0


class TestDashboardStageDistribution:
    """Test /api/dashboard-stage-distribution endpoint"""

    def test_stage_distribution_by_pic(self, client, rnd_user, rnd_pic_user, app):
        """Test that endpoint returns job distribution by PIC"""
        # Create jobs assigned to different PICs
        pic1 = rnd_pic_user
        pic2 = User(
            username='pic2',
            email='pic2@test.com',
            name='PIC 2',
            division_id=6,  # RND
            is_active=True
        )
        db.session.add(pic2)
        db.session.commit()

        # Create jobs and assignments
        for i in range(3):
            job = RNDJob(
                job_id=f'RND-20240101-{i+1:03d}',
                item_name=f'Test Job {i+1}',
                sample_type='Blank',
                priority_level='middle',
                started_at=jakarta_tz.localize(datetime(2024, 1, 1)),
                deadline_at=jakarta_tz.localize(datetime(2024, 2, 1)),
                status='in_progress'
            )
            db.session.add(job)
            db.session.flush()
            
            # Assign to PIC
            pic = pic1 if i < 2 else pic2
            progress_step = RNDProgressStep.query.first()
            if progress_step:
                assignment = RNDJobProgressAssignment(
                    job_id=job.id,
                    progress_step_id=progress_step.id,
                    pic_id=pic.id,
                    status='pending'
                )
                db.session.add(assignment)
        
        db.session.commit()

        client.post('/login', data={
            'username': rnd_user.username,
            'password': 'password'
        })

        response = client.get('/rnd-cloudsphere/api/dashboard-stage-distribution?year=2024&month=1')
        
        assert response.status_code == 200
        data = response.get_json()
        assert data['success'] is True
        assert 'data' in data
        assert isinstance(data['data'], list)


class TestDashboardSLA:
    """Test /api/dashboard-sla endpoint"""

    def test_sla_on_time_ratio(self, client, rnd_user, app):
        """Test that SLA endpoint calculates on-time ratio correctly"""
        # Create completed jobs: 3 on-time, 2 late
        year, month = 2024, 1
        
        # On-time jobs
        for i in range(3):
            job = RNDJob(
                job_id=f'RND-20240101-{i+1:03d}',
                item_name=f'On-Time Job {i+1}',
                sample_type='Blank',
                priority_level='middle',
                started_at=jakarta_tz.localize(datetime(2024, 1, 1)),
                deadline_at=jakarta_tz.localize(datetime(2024, 1, 15)),
                finished_at=jakarta_tz.localize(datetime(2024, 1, 10)),
                status='completed'
            )
            db.session.add(job)
        
        # Late jobs
        for i in range(2):
            job = RNDJob(
                job_id=f'RND-20240101-{4+i:03d}',
                item_name=f'Late Job {i+1}',
                sample_type='Blank',
                priority_level='middle',
                started_at=jakarta_tz.localize(datetime(2024, 1, 1)),
                deadline_at=jakarta_tz.localize(datetime(2024, 1, 15)),
                finished_at=jakarta_tz.localize(datetime(2024, 1, 20)),
                status='completed'
            )
            db.session.add(job)
        
        db.session.commit()

        client.post('/login', data={
            'username': rnd_user.username,
            'password': 'password'
        })

        response = client.get('/rnd-cloudsphere/api/dashboard-sla?year=2024&month=1')
        
        assert response.status_code == 200
        data = response.get_json()
        assert data['success'] is True
        
        sla = data['data']
        assert sla['total_count'] == 5
        assert sla['on_time_count'] == 3
        assert sla['on_time_pct'] == 60.0

    def test_sla_no_completed_jobs(self, client, rnd_user, app):
        """Test SLA with no completed jobs"""
        # Create only in-progress jobs
        for i in range(3):
            job = RNDJob(
                job_id=f'RND-20240101-{i+1:03d}',
                item_name=f'In-Progress Job {i+1}',
                sample_type='Blank',
                priority_level='middle',
                started_at=jakarta_tz.localize(datetime(2024, 1, 1)),
                deadline_at=jakarta_tz.localize(datetime(2024, 2, 1)),
                status='in_progress'
            )
            db.session.add(job)
        
        db.session.commit()

        client.post('/login', data={
            'username': rnd_user.username,
            'password': 'password'
        })

        response = client.get('/rnd-cloudsphere/api/dashboard-sla?year=2024&month=1')
        
        assert response.status_code == 200
        data = response.get_json()
        assert data['success'] is True
        
        sla = data['data']
        assert sla['total_count'] == 0
        assert sla['on_time_pct'] == 0


class TestDashboardAuthentication:
    """Test authentication and authorization"""

    def test_endpoints_require_login(self, client):
        """Test that all dashboard endpoints require authentication"""
        endpoints = [
            '/rnd-cloudsphere/api/dashboard-available-periods',
            '/rnd-cloudsphere/api/dashboard-available-months?year=2024',
            '/rnd-cloudsphere/api/dashboard-stats?year=2024',
            '/rnd-cloudsphere/api/dashboard-trend?year=2024',
            '/rnd-cloudsphere/api/dashboard-stage-distribution?year=2024',
            '/rnd-cloudsphere/api/dashboard-sla?year=2024'
        ]
        
        for endpoint in endpoints:
            response = client.get(endpoint)
            assert response.status_code == 401 or response.status_code == 403


# Fixtures
@pytest.fixture
def rnd_user(app):
    """Create test RND user"""
    with app.app_context():
        user = User(
            username='rnd_user',
            email='rnd_user@test.com',
            name='RND User',
            division_id=6,  # RND division
            is_active=True
        )
        user.set_password('password')
        db.session.add(user)
        db.session.commit()
        return user


@pytest.fixture
def rnd_pic_user(app):
    """Create test RND PIC user"""
    with app.app_context():
        user = User(
            username='rnd_pic',
            email='rnd_pic@test.com',
            name='RND PIC',
            division_id=6,  # RND division
            is_active=True
        )
        user.set_password('password')
        db.session.add(user)
        db.session.commit()
        return user
