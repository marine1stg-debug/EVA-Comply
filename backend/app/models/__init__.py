# Import all models in dependency order so SQLAlchemy's relationship
# registry is fully populated before any mapper configuration runs.
# tenant → user → framework → evidence (evidence refs Control and Tenant)
from app.models.base import TimestampMixin        # noqa: F401
from app.models.tenant import Tenant              # noqa: F401
from app.models.user import User                  # noqa: F401
from app.models.framework import Framework, Control  # noqa: F401
from app.models.evidence import OrgControl, EvidenceItem  # noqa: F401
from app.models.billing import BillingPlan, Invoice     # noqa: F401
from app.models.platform import PlatformSettings        # noqa: F401
from app.models.llm_settings import LlmSettings          # noqa: F401
from app.models.recommendation import Recommendation      # noqa: F401
from app.models.support import SupportCase, SupportSettings, SupportComment  # noqa: F401
from app.models.audit import AuditLog  # noqa: F401
from app.models.marketplace import ServiceProvider, MarketplaceSkill  # noqa: F401
from app.models.backup import Backup  # noqa: F401
from app.models.agreement import AgreementAcceptance  # noqa: F401
