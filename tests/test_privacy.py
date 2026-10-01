import pytest

from pycord.privacy import contains_pii, detect_pii, redact


@pytest.mark.parametrize(
    ("text", "kind"),
    [
        ("Call me on 0712345678", "phone_ke"),
        ("My number is +254 712 345 678", "phone_ke"),
        ("New line 0112345678", "phone_ke"),
        ("QFT3XYZ12A Confirmed. Ksh500 sent", "mpesa_code"),
        ("KRA PIN A012345678Z", "kra_pin"),
        ("ID number 12345678", "national_id"),
        ("Email wanjiku@example.co.ke", "email"),
    ],
)
def test_detects_kenyan_pii(text, kind):
    assert kind in {m.kind for m in detect_pii(text)}


@pytest.mark.parametrize(
    "text",
    [
        "How do I plant maize during the long rains?",
        "PYTHONISTA GOVERNMENT",
        "The meetup has 1500 attendees",
    ],
)
def test_clean_text(text):
    assert not contains_pii(text)


def test_redact():
    out = redact("Send to 0712345678, code QFT3XYZ12A")
    assert "0712345678" not in out
    assert "QFT3XYZ12A" not in out
    assert "[PHONE_KE]" in out and "[MPESA_CODE]" in out
