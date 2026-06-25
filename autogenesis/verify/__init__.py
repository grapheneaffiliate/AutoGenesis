"""L3 — Verification: the moat. Spec · feasibility · formal · safety · certificate."""

from .spec import SpecResult, check_spec
from .formal import FormalResult, check_formal
from .safety import SafetyResult, check_safety
from .certificate import (
    Certificate,
    certify,
    fingerprint,
    verify_against,
)

__all__ = [
    "SpecResult", "check_spec",
    "FormalResult", "check_formal",
    "SafetyResult", "check_safety",
    "Certificate", "certify", "fingerprint", "verify_against",
]
