"""AUTOGENESIS — a platform-agnostic, proof-carrying substrate for verified
robot maintenance & replication.

Phase 1 (this package) is the information spine: L0 Genome, L1 Feasibility,
L2 Synthesis, L3 Verification (the moat), L6 Governance. The headline contract
is :class:`autogenesis.api.Capability` — ``ingest`` / ``diagnose`` /
``plan_repair`` — where everything returned as *Verified* carries a
machine-checkable certificate.
"""

from .api import Capability, IngestError, VerifiedRepair
from .genome import Genome

__version__ = "1.0.0"

__all__ = ["Capability", "IngestError", "VerifiedRepair", "Genome", "__version__"]
