import uuid

KNOWN_GROUP_ID = "1b6c6a30-27f7-11ef-b9a3-d70b94feac5e"

def validate_transaction_exclusive_rule(tx: dict) -> bool:
    """
    Validates the CRITICAL GROUP TRANSACTION RULE:
    A transaction MUST be either a normal transaction or a group transaction,
    but NEVER both.
    """
    has_normal = bool(tx.get('transaction_id')) and bool(tx.get('transaction_no'))
    has_group = bool(tx.get('group_id')) and bool(tx.get('group_transaction_id'))
    
    # Must be XOR
    if has_normal and has_group:
        return False
    if not has_normal and not has_group:
        return False
        
    return True

def validate_group_id(tx: dict) -> bool:
    """
    Validates that if a group_id is provided, it matches the known group_id.
    """
    group_id = tx.get('group_id')
    if group_id:
        if group_id != KNOWN_GROUP_ID:
            return False
    return True

def validate_merchant_outlet_mapping(merchant_id: str, outlet_id: str) -> bool:
    """
    This could be expanded to validate against the database,
    but for the pipeline level we can do basic format checks 
    or check against an in-memory cache of valid relationships.
    """
    if not merchant_id or not outlet_id:
        return False
    return True
