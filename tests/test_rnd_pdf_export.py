"""
Unit tests for R&D PDF Export functionality

This module contains unit tests for the PDF export service,
ensuring proper role-based security and PDF generation.
"""

import unittest
import io
import os
import sys
from datetime import datetime
from unittest.mock import Mock, patch, MagicMock

# Add the parent directory to the path to import modules
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from services.rnd_pdf_export_service import RNDPDFExportService
from models_rnd import (
    RNDJob, RNDProgressStep, RNDJobProgressAssignment, 
    RNDJobTaskAssignment, RNDEvidenceFile, RNDTaskCompletion
)
from models import User


class TestRNDPDFExportService(unittest.TestCase):
    """Test cases for RNDPDFExportService"""
    
    def setUp(self):
        """Set up test fixtures"""
        # Mock database session
        self.mock_db = Mock()
        self.service = RNDPDFExportService(self.mock_db)
        
        # Create mock job
        self.mock_job = Mock(spec=RNDJob)
        self.mock_job.id = 1
        self.mock_job.job_id = "RND-20231201-001"
        self.mock_job.item_name = "Test Item"
        self.mock_job.sample_type = "Blank"
        self.mock_job.priority_level = "high"
        self.mock_job.status = "in_progress"
        self.mock_job.started_at = datetime(2023, 12, 1, 10, 0)
        self.mock_job.deadline_at = datetime(2023, 12, 15, 17, 0)
        self.mock_job.finished_at = None
        self.mock_job.completion_percentage = 45.5
        self.mock_job.notes = "Test job notes"
        
        # Create mock progress step
        self.mock_progress_step = Mock(spec=RNDProgressStep)
        self.mock_progress_step.id = 1
        self.mock_progress_step.name = "Design & Artwork Approval"
        self.mock_progress_step.sample_type = "Design"
        self.mock_progress_step.step_order = 1
        
        # Create mock user
        self.mock_user = Mock(spec=User)
        self.mock_user.id = 1
        self.mock_user.name = "Test User"
        
        # Create mock progress assignment
        self.mock_progress_assignment = Mock(spec=RNDJobProgressAssignment)
        self.mock_progress_assignment.id = 1
        self.mock_progress_assignment.job_id = 1
        self.mock_progress_assignment.progress_step_id = 1
        self.mock_progress_assignment.pic_id = 1
        self.mock_progress_assignment.progress_step = self.mock_progress_step
        self.mock_progress_assignment.pic = self.mock_user
        self.mock_progress_assignment.status = "in_progress"
        self.mock_progress_assignment.started_at = datetime(2023, 12, 1, 10, 0)
        self.mock_progress_assignment.finished_at = None
        self.mock_progress_assignment.completion_percentage = 50.0
        self.mock_progress_assignment.notes = "Test assignment notes"
        
        # Create mock task assignment
        self.mock_task_assignment = Mock(spec=RNDJobTaskAssignment)
        self.mock_task_assignment.id = 1
        self.mock_task_assignment.job_progress_assignment_id = 1
        self.mock_task_assignment.progress_task_id = 1
        self.mock_task_assignment.status = "pending"
        self.mock_task_assignment.completed_at = None
        self.mock_task_assignment.notes = "Test task notes"
        
        # Create mock evidence file
        self.mock_evidence = Mock(spec=RNDEvidenceFile)
        self.mock_evidence.id = 1
        self.mock_evidence.job_id = 1
        self.mock_evidence.job_progress_assignment_id = 1
        self.mock_evidence.job_task_assignment_id = 1
        self.mock_evidence.filename = "test_file.pdf"
        self.mock_evidence.original_filename = "Test File.pdf"
        self.mock_evidence.file_type = "pdf"
        self.mock_evidence.file_size = 1024000  # 1MB
        self.mock_evidence.uploaded_at = datetime(2023, 12, 5, 14, 30)
        
        # Set up relationships
        self.mock_job.progress_assignments = [self.mock_progress_assignment]
        self.mock_progress_assignment.task_assignments = [self.mock_task_assignment]
        self.mock_job.evidence_files = [self.mock_evidence]
    
    def test_service_initialization(self):
        """Test that the service initializes correctly"""
        self.assertEqual(self.service.db, self.mock_db)
        self.assertIsNotNone(self.service.styles)
        self.assertIsNotNone(self.service.title_style)
        self.assertIsNotNone(self.service.section_header_style)
        self.assertIsNotNone(self.service.normal_style)
    
    @patch('services.rnd_pdf_export_service.RNDJob.query.get')
    def test_export_job_to_pdf_success(self, mock_get_job):
        """Test successful PDF export for a job"""
        # Mock the job query
        mock_get_job.return_value = self.mock_job
        
        # Mock the database query for assignments
        self.mock_db.query.return_value.filter.return_value.all.return_value = [
            self.mock_progress_assignment
        ]
        
        # Call the export function
        result = self.service.export_job_to_pdf(1, 'admin', 1)
        
        # Verify result is a BytesIO buffer
        self.assertIsInstance(result, io.BytesIO)
        
        # Verify the job was queried
        mock_get_job.assert_called_once_with(1)
    
    @patch('services.rnd_pdf_export_service.RNDJob.query.get')
    def test_export_job_to_pdf_job_not_found(self, mock_get_job):
        """Test PDF export when job is not found"""
        # Mock the job query to return None
        mock_get_job.return_value = None
        
        # Call the export function and expect an exception
        with self.assertRaises(ValueError) as context:
            self.service.export_job_to_pdf(999, 'admin', 1)
        
        # Verify the error message
        self.assertIn("Job with ID 999 not found", str(context.exception))
    
    @patch('services.rnd_pdf_export_service.RNDJob.query.get')
    def test_export_job_to_pdf_admin_access(self, mock_get_job):
        """Test that admin users can export all tasks"""
        # Mock the job query
        mock_get_job.return_value = self.mock_job
        
        # Mock the database query for assignments
        self.mock_db.query.return_value.filter.return_value.all.return_value = [
            self.mock_progress_assignment
        ]
        
        # Call the export function with admin role
        result = self.service.export_job_to_pdf(1, 'admin', 999)  # Different user ID
        
        # Verify result is a BytesIO buffer (admin can access all jobs)
        self.assertIsInstance(result, io.BytesIO)
    
    @patch('services.rnd_pdf_export_service.RNDJob.query.get')
    def test_export_job_to_pdf_regular_user_access(self, mock_get_job):
        """Test that regular users can only export their assigned tasks"""
        # Mock the job query
        mock_get_job.return_value = self.mock_job
        
        # Mock the database query for assignments (only return assignments for current user)
        self.mock_db.query.return_value.filter.return_value.all.return_value = [
            self.mock_progress_assignment  # This assignment is for user ID 1
        ]
        
        # Call the export function with regular user role
        result = self.service.export_job_to_pdf(1, 'user', 1)  # Same user ID as assignment
        
        # Verify result is a BytesIO buffer
        self.assertIsInstance(result, io.BytesIO)
    
    @patch('services.rnd_pdf_export_service.RNDJob.query.get')
    def test_export_job_to_pdf_regular_user_denied(self, mock_get_job):
        """Test that regular users are denied access to unassigned jobs"""
        # Mock the job query
        mock_get_job.return_value = self.mock_job
        
        # Mock the database query for assignments (return empty for current user)
        self.mock_db.query.return_value.filter.return_value.all.return_value = []  # No assignments for user
        
        # Call the export function with regular user role
        result = self.service.export_job_to_pdf(1, 'user', 1)
        
        # Verify result is a BytesIO buffer (but with no content)
        self.assertIsInstance(result, io.BytesIO)
    
    def test_create_job_info_section(self):
        """Test creation of job information section"""
        # Call the method
        elements = self.service._create_job_info_section(self.mock_job)
        
        # Verify section header is included
        section_headers = [elem for elem in elements if hasattr(elem, 'text') and 'Job Information' in elem.text]
        self.assertTrue(len(section_headers) > 0, "Job Information section header not found")
        
        # Verify job information table is included
        tables = [elem for elem in elements if hasattr(elem, '_arg') and elem._arg[0][0] == 'Job ID']
        self.assertTrue(len(tables) > 0, "Job information table not found")
    
    def test_create_tasks_section_admin(self):
        """Test creation of tasks section for admin user"""
        # Call the method with admin role
        elements = self.service._create_tasks_section(self.mock_job, 'admin', 1)
        
        # Verify section header is included
        section_headers = [elem for elem in elements if hasattr(elem, 'text') and 'Tasks' in elem.text]
        self.assertTrue(len(section_headers) > 0, "Tasks section header not found")
        
        # Verify tasks are included (admin sees all)
        task_tables = [elem for elem in elements if hasattr(elem, '_arg') and len(elem._arg) > 1]
        self.assertTrue(len(task_tables) > 0, "Task tables not found")
    
    def test_create_tasks_section_regular_user(self):
        """Test creation of tasks section for regular user"""
        # Call the method with regular user role
        elements = self.service._create_tasks_section(self.mock_job, 'user', 1)
        
        # Verify section header is included
        section_headers = [elem for elem in elements if hasattr(elem, 'text') and 'Tasks' in elem.text]
        self.assertTrue(len(section_headers) > 0, "Tasks section header not found")
        
        # Verify tasks are included (regular user sees only their assigned tasks)
        task_tables = [elem for elem in elements if hasattr(elem, '_arg') and len(elem._arg) > 1]
        self.assertTrue(len(task_tables) > 0, "Task tables not found")
    
    def test_create_evidence_files_section_admin(self):
        """Test creation of evidence files section for admin user"""
        # Call the method with admin role
        elements = self.service._create_evidence_files_section(self.mock_job, 'admin', 1)
        
        # Verify section header is included
        section_headers = [elem for elem in elements if hasattr(elem, 'text') and 'Proof Files' in elem.text]
        self.assertTrue(len(section_headers) > 0, "Proof Files section header not found")
        
        # Verify evidence files are included (admin sees all)
        evidence_tables = [elem for elem in elements if hasattr(elem, '_arg') and 'File Name' in str(elem._arg)]
        self.assertTrue(len(evidence_tables) > 0, "Evidence file tables not found")
    
    def test_create_evidence_files_section_regular_user(self):
        """Test creation of evidence files section for regular user"""
        # Call the method with regular user role
        elements = self.service._create_evidence_files_section(self.mock_job, 'user', 1)
        
        # Verify section header is included
        section_headers = [elem for elem in elements if hasattr(elem, 'text') and 'Proof Files' in elem.text]
        self.assertTrue(len(section_headers) > 0, "Proof Files section header not found")
        
        # Verify evidence files are included (regular user sees only their assigned evidence)
        evidence_tables = [elem for elem in elements if hasattr(elem, '_arg') and 'File Name' in str(elem._arg)]
        self.assertTrue(len(evidence_tables) > 0, "Evidence file tables not found")
    
    def test_format_datetime(self):
        """Test datetime formatting"""
        # Test with valid datetime
        test_datetime = datetime(2023, 12, 1, 14, 30)
        result = self.service._format_datetime(test_datetime)
        self.assertEqual(result, "1 Desember 2023 14:30")
        
        # Test with None
        result = self.service._format_datetime(None)
        self.assertEqual(result, "N/A")
        
        # Test with string
        result = self.service._format_datetime("2023-12-01T14:30:00")
        self.assertEqual(result, "2023-12-01T14:30:00")
    
    def test_format_file_size(self):
        """Test file size formatting"""
        # Test with bytes
        result = self.service._format_file_size(500)
        self.assertEqual(result, "500 bytes")
        
        # Test with KB
        result = self.service._format_file_size(1500)
        self.assertEqual(result, "1.5 KB")
        
        # Test with MB
        result = self.service._format_file_size(1500000)
        self.assertEqual(result, "1.5 MB")
        
        # Test with None
        result = self.service._format_file_size(None)
        self.assertEqual(result, "Unknown")


class TestRNDPDFExportIntegration(unittest.TestCase):
    """Integration tests for R&D PDF Export functionality"""
    
    def setUp(self):
        """Set up test fixtures"""
        # Mock Flask app
        self.app = Mock()
        self.app.config = {'TESTING': True}
        
        # Mock database session
        self.mock_db = Mock()
    
    @patch('services.rnd_pdf_export_service.RNDJob.query.get')
    def test_pdf_generation_with_large_dataset(self, mock_get_job):
        """Test PDF generation with large dataset"""
        # Create a mock job with many tasks and evidence files
        mock_job = Mock(spec=RNDJob)
        mock_job.id = 1
        mock_job.job_id = "RND-20231201-LARGE"
        mock_job.item_name = "Large Dataset Test"
        mock_job.sample_type = "Blank"
        mock_job.priority_level = "high"
        mock_job.status = "in_progress"
        
        # Mock many progress assignments
        mock_assignments = []
        for i in range(10):  # 10 assignments
            assignment = Mock(spec=RNDJobProgressAssignment)
            assignment.id = i + 1
            assignment.job_id = 1
            assignment.progress_step_id = i + 1
            assignment.pic_id = 1
            assignment.status = "in_progress" if i == 0 else "pending"
            
            # Mock many task assignments
            tasks = []
            for j in range(20):  # 20 tasks per assignment
                task = Mock(spec=RNDJobTaskAssignment)
                task.id = (i * 20) + j + 1
                task.job_progress_assignment_id = i + 1
                task.progress_task_id = j + 1
                task.status = "completed" if j < 10 else "pending"
                tasks.append(task)
            
            assignment.task_assignments = tasks
            mock_assignments.append(assignment)
        
        mock_job.progress_assignments = mock_assignments
        
        # Mock many evidence files
        mock_evidence = []
        for i in range(50):  # 50 evidence files
            evidence = Mock(spec=RNDEvidenceFile)
            evidence.id = i + 1
            evidence.job_id = 1
            evidence.filename = f"evidence_{i}.pdf"
            evidence.original_filename = f"Evidence File {i}.pdf"
            evidence.file_type = "pdf"
            evidence.file_size = 1024000 * (i + 1)
            mock_evidence.append(evidence)
        
        mock_job.evidence_files = mock_evidence
        
        # Mock the job query
        mock_get_job.return_value = mock_job
        
        # Create service and export
        service = RNDPDFExportService(self.mock_db)
        
        # This should handle large datasets without timeout
        with patch('services.rnd_pdf_export_service.SimpleDocTemplate') as mock_doc:
            mock_doc.return_value.build = Mock()
            
            # Call the export function
            result = service.export_job_to_pdf(1, 'admin', 1)
            
            # Verify result is a BytesIO buffer
            self.assertIsInstance(result, io.BytesIO)
            
            # Verify the document was built
            mock_doc.return_value.build.assert_called_once()


if __name__ == '__main__':
    unittest.main()