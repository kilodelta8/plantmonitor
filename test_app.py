import unittest
from unittest.mock import patch, MagicMock
import app
import json

class TestPlantMonitorValues(unittest.TestCase):

    def setUp(self):
        app.app.testing = True
        self.client = app.app.test_client()

    def test_index_route(self):
        """Test that the index page loads."""
        response = self.client.get('/')
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'Plant Monitoring Dashboard', response.data)

    def test_data_route_initial(self):
        """Test that the data endpoint returns JSON."""
        response = self.client.get('/data')
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        self.assertIn('moisture_percent', data)
        self.assertIn('weather_desc', data)
        
    @patch('app.time.sleep')
    @patch('app.send_command_to_arduino')
    def test_manual_water(self, mock_send_command, mock_sleep):
        """Test manual watering triggers the command."""
        mock_send_command.return_value = True
        
        # We need to ensure the app thinks we are connected or handle the error
        # In this case, app.py check logic is inside the route
        
        response = self.client.post('/water_manual')
        
        # Check if the mock was called with "WET"
        mock_send_command.assert_called_with("WET")
        self.assertEqual(response.status_code, 200)
        
    def test_toggle_auto(self):
        """Test toggling auto-watering."""
        # Get initial state
        initial_state = app.system_state['auto_watering_enabled']
        
        response = self.client.post('/toggle_auto')
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        
        # Check if state flipped
        self.assertNotEqual(initial_state, data['enabled'])
        self.assertEqual(app.system_state['auto_watering_enabled'], data['enabled'])

if __name__ == '__main__':
    unittest.main()
