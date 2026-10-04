from utils.validation.investor_data import is_valid_client_id, is_valid_dp_id, required_missing


def test_dp_id_validation():
    assert is_valid_dp_id("DP-12345") is True
    assert is_valid_dp_id("") is False


def test_client_id_validation():
    assert is_valid_client_id("CL-001") is True
    assert is_valid_client_id("") is False


def test_required_missing_fields():
    case = {"investor_name": "A", "broker_name": "B", "issue_category": "C", "description": "D"}
    assert required_missing(case) == []
    assert required_missing({"investor_name": "", "broker_name": "B", "issue_category": "C", "description": "D"}) == ["investor_name"]
