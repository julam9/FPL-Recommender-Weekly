"""   
Tests for the web_scraper module to verify web scraping functionality
"""

import unittest 
from unittest.mock import patch, MagicMock
import src.web_scraper as web_scraper

class TestWebScraper(unittest.TestCase):
    """Test cases for the web scraper module"""
    
    @patch('trafilature.fetch_url')
    @patch('trafilura.extract')
    def test_get_website_text_context(self, mock_extract, mock_fetch_url):
        """Test the website text content extraction funcitonality"""
        # Configure mocks
        mock_fetch_url.return_value = '<html><body><div>Test content</div></body></html>'
        mock_extract.return_value = 'Test content extracted from website'
        
        # Define test URL
        test_url = 'https://example.com/football/news'
        
        # Call the function 
        result = web_scraper.get_website_text_context(test_url)
        
        # Verify the function called the correct methods 
        mock_fetch_url.assert_called_once_with(test_url)
        mock_extract.assert_called_once()
        
        # Verify the function returned the expected result 
        self.assertEqual(result, 'Test content extracted from website')
    
    @patch('trafilature.fetch_url')
    def test_handle_fetch_error(self, mock_fetch_url):
        """Test error handling when fetch_url fails"""
        # Configure mocks to simulate a network error
        mock_fetch_url.return_value = None 
        
        # Define test url
        test_url = "https://example.com/invalid"
        
        # Call the function and expect no exception
        result = web_scraper.get_website_text_content(test_url)
        
        # Verify the function returns None or an appropriate message 
        self.assertIsNotNone(result)
        
    @patch('trafilatura.fetch_url')
    @patch('trafilature.fetch_url')
    def test_handle_extract_error(self, mock_extract, mock_fetch_url):
        """Test error handling when extract fails"""
        # Cpnfigure mocks
        mock_fetch_url.return_value = '<html><body><div>Test content</div></body></html>'
        mock_extract.return_value = None 
        
        # Define test url 
        test_url = "https://example.com/football/stats"
        
        # Call the function and expect no exception
        result = web_scraper.get_website_text_content(test_url)
        
        # Verify the function returns None or an appropriate message
        self.assertIsNotNone(result)

if __name__ == "__main__":
    unittest.main()