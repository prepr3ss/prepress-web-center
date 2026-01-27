"""
Integration tests for R&D PDF Export functionality

This module contains integration tests for the PDF export route,
testing the complete flow from HTTP request to PDF generation.
"""

import unittest
import os
import sys
import json
import io
from datetime import datetime
from unittest.mock import Mock, patch, MagicMock

# Add parent directory to path to import modules
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Mock Flask app for testing
from flask import Flask

# Import the blueprint to test
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from rnd_cloudsphere import rnd_cloudsphere_bp
from models_rnd import RNDJob


class TestRNDPDFExportIntegration(unittest.TestCase):
    """Integration tests for R&D PDF Export route"""
    
    def setUp(self):
        """Set up test fixtures"""
        # Create Flask app for testing
        self.app = Flask(__name__)
        self.app.config['TESTING'] = True
        self.app.config['SECRET_KEY'] = 'test-secret-key'
        
        # Register the blueprint
        self.app.register_blueprint(rnd_cloudsphere_bp)
        
        # Create test client
        self.client = self.app.test_client()
        
        # Mock database session
        self.mock_db = Mock()
        
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
    
    @patch('rnd_cloudsphere.RNDJob.query.get')
    @patch('rnd_cloudsphere.RNDJobProgressAssignment.query')
    @patch('rnd_cloudsphere.current_user')
    @patch('rnd_cloudsphere.RNDPDFExportService')
    def test_pdf_export_admin_success(self, mock_service_class, mock_current_user, mock_assignment_query, mock_get_job):
        """Test successful PDF export by admin user"""
        # Set up mocks
        mock_get_job.return_value = self.mock_job
        
        mock_current_user.is_admin.return_value = True
        mock_current_user.id = 1
        mock_current_user.role = 'admin'
        
        # Mock PDF service
        mock_service = Mock()
        mock_service_class.return_value = mock_service
        
        # Mock PDF buffer
        pdf_buffer = io.BytesIO(b"mock PDF content")
        mock_service.export_job_to_pdf.return_value = pdf_buffer
        
        # Make the request
        response = self.client.get('/rnd-cloudsphere/api/jobs/1/export/pdf')
        
        # Verify response
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.content_type, 'application/pdf')
        self.assertIn('attachment', response.headers.get('Content-Disposition'))
        self.assertIn('RND_Job_RND-20231201-001', response.headers.get('Content-Disposition'))
        
        # Verify service was called correctly
        mock_service_class.assert_called_once()
        mock_service.export_job_to_pdf.assert_called_once_with(1, 'admin', 1)
    
    @patch('rnd_cloudsphere.RNDJob.query.get')
    @patch('rnd_cloudsphere.RNDJobProgressAssignment.query')
    @patch('rnd_cloudsphere.current_user')
    def test_pdf_export_regular_user_assigned(self, mock_current_user, mock_assignment_query, mock_get_job):
        """Test PDF export by regular user who is assigned to the job"""
        # Set up mocks
        mock_get_job.return_value = self.mock_job
        
        mock_current_user.is_admin.return_value = False
        mock_current_user.id = 1
        mock_current_user.role = 'user'
        
        # Mock assignment (user is assigned)
        mock_assignment = Mock()
        mock_assignment_query.filter.return_value.first.return_value = mock_assignment
        
        # Mock PDF service
        with patch('rnd_cloudsphere.RNDPDFExportService') as mock_service_class:
            mock_service = Mock()
            mock_service_class.return_value = mock_service
            
            # Mock PDF buffer
            pdf_buffer = io.BytesIO(b"mock PDF content")
            mock_service.export_job_to_pdf.return_value = pdf_buffer
            
            # Make the request
            response = self.client.get('/rnd-cloudsphere/api/jobs/1/export/pdf')
            
            # Verify response
            self.assertEqual(response.status_code, 200)
            self.assertEqual(response.content_type, 'application/pdf')
            self.assertIn('attachment', response.headers.get('Content-Disposition'))
    
    @patch('rnd_cloudsphere.RNDJob.query.get')
    @patch('rnd_cloudsphere.RNDJobProgressAssignment.query')
    @patch('rnd_cloudsphere.current_user')
    def test_pdf_export_regular_user_not_assigned(self, mock_current_user, mock_assignment_query, mock_get_job):
        """Test PDF export by regular user who is not assigned to the job"""
        # Set up mocks
        mock_get_job.return_value = self.mock_job
        
        mock_current_user.is_admin.return_value = False
        mock_current_user.id = 2
        mock_current_user.role = 'user'
        
        # Mock assignment (user is not assigned)
        mock_assignment_query.filter.return_value.first.return_value = None
        
        # Make the request
        response = self.client.get('/rnd-cloudsphere/api/jobs/1/export/pdf')
        
        # Verify response
        self.assertEqual(response.status_code, 403)
        response_data = json.loads(response.data.decode('utf-8'))
        self.assertFalse(response_data['success'])
        self.assertIn('Access denied', response_data['error'])
    
    @patch('rnd_cloudsphere.RNDJob.query.get')
    def test_pdf_export_job_not_found(self, mock_get_job):
        """Test PDF export for non-existent job"""
        # Set up mocks
        mock_get_job.return_value = None
        
        # Mock current user
        with patch('rnd_cloudsphere.current_user') as mock_current_user:
            mock_current_user.is_admin.return_value = True
            mock_current_user.id = 1
            mock_current_user.role = 'admin'
            
            # Make the request
            response = self.client.get('/rnd-cloudsphere/api/jobs/999/export/pdf')
            
            # Verify response
            self.assertEqual(response.status_code, 404)
            response_data = json.loads(response.data.decode('utf-8'))
            self.assertFalse(response_data['success'])
            self.assertIn('not found', response_data['error'])
    
    @patch('rnd_cloudsphere.RNDJob.query.get')
    @patch('rnd_cloudsphere.RNDPDFExportService')
    @patch('rnd_cloudsphere.current_user')
    def test_pdf_export_service_error(self, mock_current_user, mock_service_class, mock_get_job):
        """Test PDF export when service raises an error"""
        # Set up mocks
        mock_get_job.return_value = self.mock_job
        
        mock_current_user.is_admin.return_value = True
        mock_current_user.id = 1
        mock_current_user.role = 'admin'
        
        # Mock PDF service to raise an exception
        mock_service = Mock()
        mock_service_class.return_value = mock_service
        mock_service.export_job_to_pdf.side_effect = Exception("PDF generation failed")
        
        # Make the request
        response = self.client.get('/rnd-cloudsphere/api/jobs/1/export/pdf')
        
        # Verify response
        self.assertEqual(response.status_code, 500)
        response_data = json.loads(response.data.decode('utf-8'))
        self.assertFalse(response_data['success'])
        self.assertIn('Error exporting PDF', response_data['error'])
    
    @patch('rnd_cloudsphere.RNDJob.query.get')
    @patch('rnd_cloudsphere.RNDPDFExportService')
    @patch('rnd_cloudsphere.current_user')
    def test_pdf_export_large_dataset_timeout(self, mock_current_user, mock_service_class, mock_get_job):
        """Test PDF export with large dataset that might timeout"""
        # Set up mocks
        mock_get_job.return_value = self.mock_job
        
        mock_current_user.is_admin.return_value = True
        mock_current_user.id = 1
        mock_current_user.role = 'admin'
        
        # Mock PDF service to simulate timeout
        mock_service = Mock()
        mock_service_class.return_value = mock_service
        mock_service.export_job_to_pdf.side_effect = Exception("Request timeout")
        
        # Make the request
        response = self.client.get('/rnd-cloudsphere/api/jobs/1/export/pdf')
        
        # Verify response
        self.assertEqual(response.status_code, 500)
        response_data = json.loads(response.data.decode('utf-8'))
        self.assertFalse(response_data['success'])
        self.assertIn('Error exporting PDF', response_data['error'])
    
    @patch('rnd_cloudsphere.RNDJob.query.get')
    @patch('rnd_cloudsphere.RNDPDFExportService')
    @patch('rnd_cloudsphere.current_user')
    def test_pdf_export_filename_generation(self, mock_current_user, mock_service_class, mock_get_job):
        """Test that PDF filename is generated correctly"""
        # Set up mocks
        mock_get_job.return_value = self.mock_job
        
        mock_current_user.is_admin.return_value = True
        mock_current_user.id = 1
        mock_current_user.role = 'admin'
        
        # Mock PDF service
        mock_service = Mock()
        mock_service_class.return_value = mock_service
        
        # Mock PDF buffer
        pdf_buffer = io.BytesIO(b"mock PDF content")
        mock_service.export_job_to_pdf.return_value = pdf_buffer
        
        # Make the request
        response = self.client.get('/rnd-cloudsphere/api/jobs/1/export/pdf')
        
        # Verify response
        self.assertEqual(response.status_code, 200)
        
        # Check filename format
        content_disposition = response.headers.get('Content-Disposition')
        self.assertIn('attachment', content_disposition)
        self.assertIn('RND_Job_RND-20231201-001', content_disposition)
        self.assertIn('.pdf', content_disposition)
    
    @patch('rnd_cloudsphere.RNDJob.query.get')
    @patch('rnd_cloudsphere.RNDPDFExportService')
    @patch('rnd_cloudsphere.current_user')
    def test_pdf_export_content_type(self, mock_current_user, mock_service_class, mock_get_job):
        """Test that PDF content type is correct"""
        # Set up mocks
        mock_get_job.return_value = self.mock_job
        
        mock_current_user.is_admin.return_value = True
        mock_current_user.id = 1
        mock_current_user.role = 'admin'
        
        # Mock PDF service
        mock_service = Mock()
        mock_service_class.return_value = mock_service
        
        # Mock PDF buffer
        pdf_buffer = io.BytesIO(b"mock PDF content")
        mock_service.export_job_to_pdf.return_value = pdf_buffer
        
        # Make the request
        response = self.client.get('/rnd-cloudsphere/api/jobs/1/export/pdf')
        
        # Verify response
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.content_type, 'application/pdf')


if __name__ == '__main__':
    unittest.main()