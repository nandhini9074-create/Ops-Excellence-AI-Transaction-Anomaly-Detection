import pytest
from data_pipeline.validation.business_rules import validate_transaction_exclusive_rule, validate_group_id

def test_exclusive_rule_normal_txn():
    tx = {
        "transaction_id": "123",
        "transaction_no": "TXN-123",
        "group_id": None,
        "group_transaction_id": None
    }
    assert validate_transaction_exclusive_rule(tx) == True

def test_exclusive_rule_group_txn():
    tx = {
        "transaction_id": None,
        "transaction_no": None,
        "group_id": "1b6c6a30-27f7-11ef-b9a3-d70b94feac5e",
        "group_transaction_id": "456"
    }
    assert validate_transaction_exclusive_rule(tx) == True

def test_exclusive_rule_invalid_both():
    tx = {
        "transaction_id": "123",
        "transaction_no": "TXN-123",
        "group_id": "1b6c6a30-27f7-11ef-b9a3-d70b94feac5e",
        "group_transaction_id": "456"
    }
    assert validate_transaction_exclusive_rule(tx) == False

def test_exclusive_rule_invalid_neither():
    tx = {
        "transaction_id": None,
        "transaction_no": None,
        "group_id": None,
        "group_transaction_id": None
    }
    assert validate_transaction_exclusive_rule(tx) == False

def test_group_id_validation():
    tx_valid = {"group_id": "1b6c6a30-27f7-11ef-b9a3-d70b94feac5e"}
    assert validate_group_id(tx_valid) == True
    
    tx_invalid = {"group_id": "some-random-id"}
    assert validate_group_id(tx_invalid) == False
