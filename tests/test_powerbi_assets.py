from scripts.validate_powerbi_assets import validate_exports


def test_powerbi_fallback_exports_are_valid():
    assert validate_exports() == []
