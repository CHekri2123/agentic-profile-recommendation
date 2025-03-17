import pytest
import pymongo
from unittest.mock import patch, MagicMock
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from app.database import (
    save_user_profile,
    get_user_profile,
    delete_user_profile,
    list_all_users,
    users_collection
)


# Sample user profile for testing
@pytest.fixture
def sample_user_profile():
    return {
        "user_id": "test123",
        "name": "Test User",
        "interests": ["AI", "Technology", "Books"],
        "preferences": {
            "language": "English",
            "categories": ["Science", "Technology"]
        },
        "demographics": {
            "age": 30,
            "location": "New York"
        }
    }

# Mock MongoDB collection
@pytest.fixture
def mock_collection():
    mock = MagicMock()
    return mock

# Test save_user_profile function
@patch('app.database.users_collection')
def test_save_user_profile_insert(mock_collection, sample_user_profile):
    # Setup mock for insert
    mock_result = MagicMock()
    mock_result.upserted_id = "new_id"
    mock_collection.update_one.return_value = mock_result
    
    # Call function
    result = save_user_profile(sample_user_profile)
    
    # Assertions
    assert result is True
    mock_collection.update_one.assert_called_once_with(
        {"user_id": sample_user_profile["user_id"]},
        {"$set": sample_user_profile},
        upsert=True
    )

@patch('app.database.users_collection')
def test_save_user_profile_update(mock_collection, sample_user_profile):
    # Setup mock for update
    mock_result = MagicMock()
    mock_result.upserted_id = None
    mock_collection.update_one.return_value = mock_result
    
    # Call function
    result = save_user_profile(sample_user_profile)
    
    # Assertions
    assert result is True
    mock_collection.update_one.assert_called_once_with(
        {"user_id": sample_user_profile["user_id"]},
        {"$set": sample_user_profile},
        upsert=True
    )

@patch('app.database.users_collection')
def test_save_user_profile_error(mock_collection, sample_user_profile):
    # Setup mock to raise exception
    mock_collection.update_one.side_effect = pymongo.errors.PyMongoError("Test error")
    
    # Call function
    result = save_user_profile(sample_user_profile)
    
    # Assertions
    assert result is False

# Test get_user_profile function
@patch('app.database.users_collection')
def test_get_user_profile_success(mock_collection, sample_user_profile):
    # Setup mock
    mock_collection.find_one.return_value = sample_user_profile
    
    # Call function
    result = get_user_profile(sample_user_profile["user_id"])
    
    # Assertions
    assert result == sample_user_profile
    mock_collection.find_one.assert_called_once_with(
        {"user_id": sample_user_profile["user_id"]}, 
        {"_id": 0}
    )

@patch('app.database.users_collection')
def test_get_user_profile_not_found(mock_collection):
    # Setup mock
    mock_collection.find_one.return_value = None
    
    # Call function
    result = get_user_profile("nonexistent_id")
    
    # Assertions
    assert result is None

@patch('app.database.users_collection')
def test_get_user_profile_error(mock_collection):
    # Setup mock to raise exception
    mock_collection.find_one.side_effect = pymongo.errors.PyMongoError("Test error")
    
    # Call function
    result = get_user_profile("test_id")
    
    # Assertions
    assert result is None

# Test delete_user_profile function
@patch('app.database.users_collection')
def test_delete_user_profile_success(mock_collection):
    # Setup mock
    mock_result = MagicMock()
    mock_result.deleted_count = 1
    mock_collection.delete_one.return_value = mock_result
    
    # Call function
    result = delete_user_profile("test_id")
    
    # Assertions
    assert result is True
    mock_collection.delete_one.assert_called_once_with({"user_id": "test_id"})

@patch('app.database.users_collection')
def test_delete_user_profile_not_found(mock_collection):
    # Setup mock
    mock_result = MagicMock()
    mock_result.deleted_count = 0
    mock_collection.delete_one.return_value = mock_result
    
    # Call function
    result = delete_user_profile("nonexistent_id")
    
    # Assertions
    assert result is False

@patch('app.database.users_collection')
def test_delete_user_profile_error(mock_collection):
    # Setup mock to raise exception
    mock_collection.delete_one.side_effect = pymongo.errors.PyMongoError("Test error")
    
    # Call function
    result = delete_user_profile("test_id")
    
    # Assertions
    assert result is False

# Test list_all_users function
@patch('app.database.users_collection')
def test_list_all_users_success(mock_collection, sample_user_profile):
    # Setup mock
    mock_collection.find.return_value = [sample_user_profile, sample_user_profile]
    
    # Call function
    result = list_all_users()
    
    # Assertions
    assert len(result) == 2
    mock_collection.find.assert_called_once_with({}, {"_id": 0})

@patch('app.database.users_collection')
def test_list_all_users_empty(mock_collection):
    # Setup mock
    mock_collection.find.return_value = []
    
    # Call function
    result = list_all_users()
    
    # Assertions
    assert result == []

@patch('app.database.users_collection')
def test_list_all_users_error(mock_collection):
    # Setup mock to raise exception
    mock_collection.find.side_effect = pymongo.errors.PyMongoError("Test error")
    
    # Call function
    result = list_all_users()
    
    # Assertions
    assert result == []
