import unittest
from unittest.mock import Mock, patch

from flask import Flask

import rnd_cloudsphere


class TestCompleteIfReadyEndpoint(unittest.TestCase):
    def setUp(self):
        self.app = Flask(__name__)
        self.app.register_blueprint(rnd_cloudsphere.rnd_cloudsphere_bp)
        self.client = self.app.test_client()

    @patch('rnd_cloudsphere.RNDJob.query.get')
    @patch('rnd_cloudsphere.RNDJobProgressAssignment.query')
    @patch('rnd_cloudsphere.current_user')
    def test_complete_if_ready_by_pic_success(self, mock_user, mock_assignment_query, mock_job_get):
        # Setup a job and progress assignments all completed
        mock_job = Mock()
        mock_job.id = 1
        mock_job.status = 'in_progress'

        pa1 = Mock()
        pa1.status = 'completed'
        pa1.pic_id = 10
        pa1.progress_step = Mock(name='Step1')

        pa2 = Mock()
        pa2.status = 'completed'
        pa2.pic_id = 11
        pa2.progress_step = Mock(name='Step2')

        mock_assignment_query.filter_by.return_value.all.return_value = [pa1, pa2]
        mock_job_get.return_value = mock_job

        # Current user is PIC (one of pic_ids)
        mock_user.id = 10
        mock_user.is_admin = Mock(return_value=False)

        response = self.client.post('/rnd-cloudsphere/api/jobs/1/complete-if-ready')
        data = response.get_json()

        self.assertEqual(response.status_code, 200)
        self.assertTrue(data['success'])

    @patch('rnd_cloudsphere.RNDJob.query.get')
    @patch('rnd_cloudsphere.RNDJobProgressAssignment.query')
    @patch('rnd_cloudsphere.current_user')
    def test_complete_if_ready_by_admin_success(self, mock_user, mock_assignment_query, mock_job_get):
        mock_job = Mock()
        mock_job.id = 2
        mock_job.status = 'in_progress'

        pa1 = Mock(); pa1.status = 'completed'; pa1.pic_id = 20; pa1.progress_step = Mock(name='A')
        mock_assignment_query.filter_by.return_value.all.return_value = [pa1]
        mock_job_get.return_value = mock_job

        mock_user.id = 99
        mock_user.is_admin = Mock(return_value=True)

        response = self.client.post('/rnd-cloudsphere/api/jobs/2/complete-if-ready')
        data = response.get_json()

        self.assertEqual(response.status_code, 200)
        self.assertTrue(data['success'])

    @patch('rnd_cloudsphere.RNDJob.query.get')
    @patch('rnd_cloudsphere.RNDJobProgressAssignment.query')
    @patch('rnd_cloudsphere.current_user')
    def test_complete_if_ready_not_all_completed(self, mock_user, mock_assignment_query, mock_job_get):
        mock_job = Mock(); mock_job.id = 3
        pa1 = Mock(); pa1.status = 'completed'; pa1.pic_id = 30; pa1.progress_step = Mock(name='X')
        pa2 = Mock(); pa2.status = 'in_progress'; pa2.pic_id = 31; pa2.progress_step = Mock(name='Y')
        mock_assignment_query.filter_by.return_value.all.return_value = [pa1, pa2]
        mock_job_get.return_value = mock_job

        mock_user.id = 30
        mock_user.is_admin = Mock(return_value=False)

        response = self.client.post('/rnd-cloudsphere/api/jobs/3/complete-if-ready')
        data = response.get_json()

        self.assertEqual(response.status_code, 400)
        self.assertFalse(data['success'])

    @patch('rnd_cloudsphere.RNDJob.query.get')
    @patch('rnd_cloudsphere.RNDJobProgressAssignment.query')
    @patch('rnd_cloudsphere.current_user')
    def test_complete_if_ready_forbidden_for_unrelated_user(self, mock_user, mock_assignment_query, mock_job_get):
        mock_job = Mock(); mock_job.id = 4
        pa1 = Mock(); pa1.status = 'completed'; pa1.pic_id = 40; pa1.progress_step = Mock(name='Z')
        mock_assignment_query.filter_by.return_value.all.return_value = [pa1]
        mock_job_get.return_value = mock_job

        mock_user.id = 999
        mock_user.is_admin = Mock(return_value=False)

        response = self.client.post('/rnd-cloudsphere/api/jobs/4/complete-if-ready')
        data = response.get_json()

        self.assertEqual(response.status_code, 403)
        self.assertFalse(data['success'])


if __name__ == '__main__':
    unittest.main()
