import pytest
from transcriptions.utils import some_utility_function

def test_some_utility_function():
    result = some_utility_function(5, 10)
    assert result == 15  # Assuming the function adds two numbers
