import unittest
from unittest.mock import Mock, patch
import os

class TestCosmosMemoryStore(unittest.TestCase):
    
    @patch.dict(os.environ, {'COSMOSDB_ENDPOINT': 'https://test.documents.azure.com:443/'})
    @patch('services.cosmos_store.COSMOS_AVAILABLE', True)
    @patch('services.cosmos_store.DefaultAzureCredential')
    @patch('services.cosmos_store.CosmosClient')
    def test_cosmos_enabled_with_valid_config(self, mock_cosmos_client, mock_credential):
        from services.cosmos_store import CosmosMemoryStore
        
        # Mock container
        mock_container = Mock()
        mock_database = Mock()
        mock_database.create_container_if_not_exists.return_value = mock_container
        mock_client = Mock()
        mock_client.create_database_if_not_exists.return_value = mock_database
        mock_cosmos_client.return_value = mock_client
        
        store = CosmosMemoryStore()
        
        self.assertTrue(store.enabled)
        self.assertIsNotNone(store.container)
        self.assertEqual(store.container, mock_container)
    
    @patch.dict(os.environ, {}, clear=True)
    def test_cosmos_disabled_without_endpoint(self):
        from services.cosmos_store import CosmosMemoryStore
        
        store = CosmosMemoryStore()
        
        self.assertFalse(store.enabled)
        self.assertIsNone(store.container)
    
    @patch('services.cosmos_store.COSMOS_AVAILABLE', False)
    def test_cosmos_disabled_without_sdk(self):
        from services.cosmos_store import CosmosMemoryStore
        
        store = CosmosMemoryStore()
        
        self.assertFalse(store.enabled)
        self.assertIsNone(store.container)

if __name__ == '__main__':
    unittest.main()