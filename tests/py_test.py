import pytest
from utils.rfc_validator import validar_rfc


# --- VALID RFCs (should NOT raise) ---
@pytest.mark.parametrize(
    "rfc",
    [
        "XAXX010101000",
        "XEXX010101000",
        "GODE561231GR8",
        "MOPR800101AB1",
        "HEGA920305LZ2",
    ],
)
def test_rfc_validos_no_raises(rfc):
    # Should not raise any exception
    result = validar_rfc(rfc, "fisica")
    assert result is True or result is None  # depending on your implementation


# --- INVALID RFCs (should raise Exception) ---
@pytest.mark.parametrize(
    "rfc",
    [
        "ABC123",
        "1234567890123",
        "GODE561231",
        "GODE561231GR888",
        "",
        "   ",
    ],
)
def test_rfc_invalidos_raise(rfc):
    with pytest.raises(Exception):
        validar_rfc(rfc, "fisica")


# --- NONE INPUT (should raise) ---
def test_rfc_none_raises():
    with pytest.raises(Exception):
        validar_rfc(None, "fisica")


# --- INVALID CHARACTERS ---
@pytest.mark.parametrize(
    "rfc",
    [
        "!!!INVALID!!!",
        "GODE56@231GR8",
    ],
)
def test_rfc_invalid_chars_raise(rfc):
    with pytest.raises(Exception):
        validar_rfc(rfc, "fisica")


# --- WRONG TIPO (if your function enforces it) ---
def test_rfc_wrong_tipo_raises():
    with pytest.raises(Exception):
        validar_rfc("GODE561231GR8", "morfdfsal")


# --- EDGE CASES (decide behavior: here we assume valid format should NOT raise) ---
@pytest.mark.parametrize(
    "rfc",
    [
        "AAAA000000AAA",
        "ZZZZ991231ZZ9",
        "ABCD010101000",
    ],
)
def test_rfc_edge_cases_no_raises(rfc):
    try:
        validar_rfc(rfc, "fisica")
    except Exception as e:
        pytest.fail(f"Unexpected exception for edge case {rfc}: {e}")
