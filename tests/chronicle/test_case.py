"""Tests for Chronicle case functionality."""

import unittest
from unittest import mock
from typing import Any

from secops.chronicle.case import list_cases
from secops.chronicle.models import APIVersion
from secops.exceptions import APIError


class TestChronicleCase(unittest.TestCase):
    """Tests for Chronicle case functionality."""

    def setUp(self) -> None:
        self.mock_client = mock.MagicMock()
        self.mock_client.instance_id = "projects/test-project/locations/us/instances/test-instance"
        
        # Mock base_url to behave like the callable BaseUrl object
        self.mock_client.base_url = mock.MagicMock()
        self.mock_client.base_url.return_value = "https://test-chronicle.googleapis.com/v1alpha"

    def test_list_cases_defaults(self) -> None:
        """Test list_cases with default parameters."""
        expected_response = {
            "cases": [{"name": "projects/.../cases/123", "displayName": "Case 1"}],
            "nextPageToken": "token123"
        }
        
        mock_response = mock.MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = expected_response
        self.mock_client.session.get.return_value = mock_response

        result = list_cases(self.mock_client)

        self.assertEqual(result, expected_response)
        
        # Verify URL and params
        args, _ = self.mock_client.base_url.call_args
        self.assertEqual(args[0], APIVersion.V1ALPHA)
        
        expected_url = f"{self.mock_client.base_url.return_value}/{self.mock_client.instance_id}/cases"
        self.mock_client.session.get.assert_called_with(expected_url, params={})

    def test_list_cases_with_params(self) -> None:
        """Test list_cases with all parameters."""
        mock_response = mock.MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {}
        self.mock_client.session.get.return_value = mock_response

        list_cases(
            self.mock_client,
            page_size=50,
            page_token="token123",
            filter_query="priority=HIGH",
            order_by="createTime desc",
            api_version=APIVersion.V1BETA
        )

        # Verify URL and params
        args, _ = self.mock_client.base_url.call_args
        self.assertEqual(args[0], APIVersion.V1BETA)
        
        expected_url = f"{self.mock_client.base_url.return_value}/{self.mock_client.instance_id}/cases"
        expected_params = {
            "pageSize": "50",
            "pageToken": "token123",
            "filter": "priority=HIGH",
            "orderBy": "createTime desc"
        }
        self.mock_client.session.get.assert_called_with(expected_url, params=expected_params)

    def test_list_cases_api_error(self) -> None:
        """Test list_cases handling API errors."""
        mock_response = mock.MagicMock()
        mock_response.status_code = 400
        mock_response.text = "Bad Request"
        self.mock_client.session.get.return_value = mock_response

        with self.assertRaises(APIError):
            list_cases(self.mock_client)

    def test_list_cases_json_error(self) -> None:
        """Test list_cases handling JSON parse errors."""
        mock_response = mock.MagicMock()
        mock_response.status_code = 200
        mock_response.json.side_effect = ValueError("Invalid JSON")
        self.mock_client.session.get.return_value = mock_response

        with self.assertRaises(APIError) as cm:
            list_cases(self.mock_client)
        
        self.assertIn("Failed to parse cases response", str(cm.exception))

if __name__ == "__main__":
    unittest.main()
