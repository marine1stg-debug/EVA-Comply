"""MSP partner / reseller margin API.

Model (wholesale markup + volume tiers):
  • EVA sets a wholesale price per plan (the MSP's cost) - billing_plans.wholesale_monthly.
  • The client is billed the RETAIL price (tenant.monthly_price) via EVA's Stripe.
  • EVA applies a volume discount to the wholesale based on the MSP's active client
    count, keeps the discounted wholesale, and pays the MSP the difference
    (retail − effective_wholesale) as margin.

Endpoints:
  GET   /me                     MSP self-view (margin dashboard)
  GET   /{msp_id}               Super admin view of one MSP
  PUT   /{msp_id}/terms         Super admin edits volume tiers / cap / enabled
  PATCH /client/{client_id}/retail   Set a client's retail price (floored at wholesale)
"""
import uuid
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.api.auth import get_current_user
from app.models.user import User, UserRole
from app.models.tenant import Tenant, TenantType, SubscriptionStatus
from app.models.billing import BillingPlan

router = APIRouter()

MSP_ROLES = {UserRole.msp_admin, UserRole.msp_analyst}
DEFAULT_TIERS = [
    {"min_clients": 0, "discount_pct": 0},
    {"min_clients": 6, "discount_pct": 5},
    {"min_clients": 16, "discount_pct": 10},
]


def _partner_cfg(msp: Tenant) -> dict:
    raw = (msp.settings or {}).get("partner") or {}
    tiers = raw.get("volume_tiers") or DEFAULT_TIERS
    tiers = sorted(
        [{"min_clients": int(t.get("min_clients", 0)),
          "min_revenue": int(t.get("min_revenue", 0) or 0),
          "discount_pct": float(t.get("discount_pct", 0))} for t in tiers],
        key=lambda t: (t["min_revenue"], t["min_clients"]),
    )
    model = raw.get("model", "wholesale")
    if model not in ("wholesale", "commission"):
        model = "wholesale"
    basis = raw.get("tier_basis", "clients")
    if basis not in ("clients", "revenue"):
        basis = "clients"
    return {
        "enabled": raw.get("enabled", True),
        "volume_tiers": tiers,
        "max_clients": int(raw.get("max_clients", 0) or 0),
        # Partner model: "wholesale" (markup) or "commission" (referral).
        "model": model,
        # Volume tiers keyed on "clients" (active count) or "revenue" (annual $).
        "tier_basis": basis,
        # Commission model parameters.
        "client_discount_pct": float(raw.get("client_discount_pct", 0) or 0),
        "commission_pct": float(raw.get("commission_pct", 0) or 0),
    }


def _save_partner(msp: Tenant, cfg: dict) -> None:
    s = dict(msp.settings or {})
    s["partner"] = cfg
    msp.settings = s  # reassign so SQLAlchemy tracks the JSON change


def _tier_for(cfg: dict, active_clients: int, annual_revenue: int = 0):
    """Return (discount_pct, current_tier, next_tier_or_None).
    Tiers are matched on active client count or annual revenue per tier_basis."""
    tiers = cfg["volume_tiers"]
    by_rev = cfg.get("tier_basis") == "revenue"
    metric = annual_revenue if by_rev else active_clients
    key = (lambda t: t["min_revenue"]) if by_rev else (lambda t: t["min_clients"])
    ordered = sorted(tiers, key=key)
    current = ordered[0] if ordered else {"min_clients": 0, "min_revenue": 0, "discount_pct": 0}
    nxt = None
    for i, t in enumerate(ordered):
        if metric >= key(t):
            current = t
            nxt = ordered[i + 1] if i + 1 < len(ordered) else None
    return current["discount_pct"], current, nxt


def _eff_wholesale(plan: BillingPlan | None, discount_pct: float) -> int:
    base = (plan.wholesale_monthly or 0) if plan else 0
    return round(base * (1 - discount_pct / 100.0))


async def _msp_margin(db: AsyncSession, msp: Tenant) -> dict:
    cfg = _partner_cfg(msp)
    is_commission = cfg["model"] == "commission"
    clients = (await db.execute(
        select(Tenant).where(Tenant.parent_msp_id == msp.id, Tenant.archived == False)  # noqa: E712
    )).scalars().all()
    active = [c for c in clients if c.subscription_status != SubscriptionStatus.cancelled and c.is_active]

    plan_ids = {c.plan_id for c in clients if c.plan_id}
    plans = {}
    if plan_ids:
        rows = (await db.execute(select(BillingPlan).where(BillingPlan.id.in_(plan_ids)))).scalars().all()
        plans = {p.id: p for p in rows}

    def _retail(c):
        plan = plans.get(c.plan_id)
        return c.monthly_price if c.monthly_price is not None else (plan.price_monthly if plan else 0)

    # First pass: annual revenue from active clients (for revenue-based tiers).
    annual_revenue = sum(_retail(c) for c in active) * 12
    discount, current_tier, next_tier = _tier_for(cfg, len(active), annual_revenue)
    cdisc = cfg["client_discount_pct"]
    cpct = cfg["commission_pct"]

    rows_out, t_retail, t_eva, t_margin = [], 0, 0, 0
    for c in clients:
        plan = plans.get(c.plan_id)
        retail = _retail(c)
        billable = c.subscription_status != SubscriptionStatus.cancelled and c.is_active
        if is_commission:
            # Partner gives clients a fixed discount; EVA collects the discounted
            # price and pays the partner a commission on what it collects.
            collected = round(retail * (1 - cdisc / 100.0))
            payout = round(collected * cpct / 100.0)
            eva_keep = max(0, collected - payout)
            row = {"id": str(c.id), "name": c.name, "plan": c.plan_name or (plan.name if plan else "-"),
                   "status": c.subscription_status.value, "active": billable,
                   "retail": retail, "wholesale": collected, "effective_wholesale": eva_keep,
                   "margin": payout, "floor": 0}
            if billable:
                t_retail += collected; t_eva += eva_keep; t_margin += payout
        else:
            eff_ws = _eff_wholesale(plan, discount)
            margin = max(0, retail - eff_ws)
            row = {"id": str(c.id), "name": c.name, "plan": c.plan_name or (plan.name if plan else "-"),
                   "status": c.subscription_status.value, "active": billable,
                   "retail": retail, "wholesale": (plan.wholesale_monthly or 0) if plan else 0,
                   "effective_wholesale": eff_ws, "margin": margin, "floor": eff_ws}
            if billable:
                t_retail += retail; t_eva += eff_ws; t_margin += margin
        rows_out.append(row)
    rows_out.sort(key=lambda r: r["margin"], reverse=True)

    next_hint = None
    if next_tier:
        by_rev = cfg["tier_basis"] == "revenue"
        next_hint = {
            "min_clients": next_tier["min_clients"],
            "min_revenue": next_tier["min_revenue"],
            "discount_pct": next_tier["discount_pct"],
            "clients_needed": max(0, next_tier["min_clients"] - len(active)),
            "revenue_needed": max(0, next_tier["min_revenue"] - annual_revenue),
        }
    return {
        "msp_id": str(msp.id), "msp_name": msp.name,
        "enabled": cfg["enabled"], "max_clients": cfg["max_clients"],
        "model": cfg["model"], "tier_basis": cfg["tier_basis"],
        "client_discount_pct": cdisc, "commission_pct": cpct,
        "annual_revenue": annual_revenue,
        "volume_tiers": cfg["volume_tiers"],
        "discount_pct": discount, "current_tier": current_tier, "next_tier": next_hint,
        "clients": rows_out,
        "totals": {
            "clients": len(clients), "active_clients": len(active),
            "client_mrr": t_retail, "eva_share": t_eva, "msp_payout": t_margin,
            "margin_pct": round(t_margin / t_retail * 100) if t_retail else 0,
        },
    }


@router.get("/me")
async def my_partner(current_user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    if current_user.role not in MSP_ROLES:
        raise HTTPException(status_code=403, detail="MSP access required")
    msp = (await db.execute(select(Tenant).where(Tenant.id == current_user.tenant_id))).scalar_one_or_none()
    if not msp or msp.tenant_type != TenantType.msp:
        raise HTTPException(status_code=400, detail="No MSP organization in scope")
    out = await _msp_margin(db, msp)
    out["can_edit_terms"] = False
    out["can_edit_retail"] = current_user.role == UserRole.msp_admin
    return out


@router.get("/{msp_id}")
async def get_partner(msp_id: str, current_user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    if current_user.role != UserRole.super_admin:
        raise HTTPException(status_code=403, detail="Super Admin access required")
    try:
        mid = uuid.UUID(msp_id)
    except ValueError:
        raise HTTPException(status_code=404, detail="MSP not found")
    msp = (await db.execute(select(Tenant).where(Tenant.id == mid))).scalar_one_or_none()
    if not msp or msp.tenant_type != TenantType.msp:
        raise HTTPException(status_code=404, detail="MSP not found")
    out = await _msp_margin(db, msp)
    out["can_edit_terms"] = True
    out["can_edit_retail"] = True
    return out


class TermsBody(BaseModel):
    enabled: bool = True
    max_clients: int = 0
    volume_tiers: list[dict] = []
    model: str = "wholesale"            # "wholesale" | "commission"
    tier_basis: str = "clients"         # "clients" | "revenue"
    client_discount_pct: float = 0
    commission_pct: float = 0


@router.put("/{msp_id}/terms")
async def set_terms(msp_id: str, body: TermsBody, current_user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    if current_user.role != UserRole.super_admin:
        raise HTTPException(status_code=403, detail="Super Admin access required")
    try:
        mid = uuid.UUID(msp_id)
    except ValueError:
        raise HTTPException(status_code=404, detail="MSP not found")
    msp = (await db.execute(select(Tenant).where(Tenant.id == mid))).scalar_one_or_none()
    if not msp or msp.tenant_type != TenantType.msp:
        raise HTTPException(status_code=404, detail="MSP not found")
    tiers = []
    for t in (body.volume_tiers or []):
        try:
            tiers.append({"min_clients": max(0, int(t.get("min_clients", 0))),
                          "min_revenue": max(0, int(t.get("min_revenue", 0) or 0)),
                          "discount_pct": max(0.0, min(100.0, float(t.get("discount_pct", 0))))})
        except (TypeError, ValueError):
            continue
    if not tiers:
        tiers = [{**t, "min_revenue": 0} for t in DEFAULT_TIERS]
    tiers.sort(key=lambda x: (x["min_revenue"], x["min_clients"]))
    model = body.model if body.model in ("wholesale", "commission") else "wholesale"
    basis = body.tier_basis if body.tier_basis in ("clients", "revenue") else "clients"
    _save_partner(msp, {
        "enabled": body.enabled, "max_clients": max(0, body.max_clients),
        "volume_tiers": tiers, "model": model, "tier_basis": basis,
        "client_discount_pct": max(0.0, min(100.0, float(body.client_discount_pct or 0))),
        "commission_pct": max(0.0, min(100.0, float(body.commission_pct or 0))),
    })
    await db.commit()
    return await _msp_margin(db, msp)


class RetailBody(BaseModel):
    retail: int


@router.patch("/client/{client_id}/retail")
async def set_retail(client_id: str, body: RetailBody, current_user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    try:
        cid = uuid.UUID(client_id)
    except ValueError:
        raise HTTPException(status_code=404, detail="Client not found")
    client = (await db.execute(select(Tenant).where(Tenant.id == cid))).scalar_one_or_none()
    if not client or client.tenant_type != TenantType.single_client or not client.parent_msp_id:
        raise HTTPException(status_code=404, detail="MSP-managed client not found")
    # Access: super admin, or the MSP admin that owns this client.
    if current_user.role == UserRole.super_admin:
        pass
    elif current_user.role == UserRole.msp_admin and client.parent_msp_id == current_user.tenant_id:
        pass
    else:
        raise HTTPException(status_code=403, detail="Not allowed to price this client")
    msp = (await db.execute(select(Tenant).where(Tenant.id == client.parent_msp_id))).scalar_one()
    cfg = _partner_cfg(msp)
    active = (await db.execute(select(Tenant).where(Tenant.parent_msp_id == msp.id, Tenant.archived == False))).scalars().all()  # noqa: E712
    active_n = len([c for c in active if c.subscription_status != SubscriptionStatus.cancelled and c.is_active])
    discount, _, _ = _tier_for(cfg, active_n)
    plan = (await db.execute(select(BillingPlan).where(BillingPlan.id == client.plan_id))).scalar_one_or_none() if client.plan_id else None
    floor = _eff_wholesale(plan, discount)
    if body.retail < floor:
        raise HTTPException(status_code=400, detail=f"Retail must be at least the EVA wholesale floor (${floor}/mo)")
    client.monthly_price = body.retail
    await db.commit()
    return {"id": str(client.id), "retail": client.monthly_price, "floor": floor, "margin": max(0, client.monthly_price - floor)}


# ════════════════ MONTHLY MSP STATEMENT ════════════════
@router.post("/{msp_id}/statement")
async def generate_statement(msp_id: str, current_user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    """Super admin generates the MSP's monthly payout statement (a numbered
    invoice, kind=msp_consolidated) and emails the MSP admin from the invoicing
    sender. Amount = total margin EVA owes the MSP this month."""
    if current_user.role != UserRole.super_admin:
        raise HTTPException(status_code=403, detail="Super Admin access required")
    try:
        mid = uuid.UUID(msp_id)
    except ValueError:
        raise HTTPException(status_code=404, detail="MSP not found")
    msp = (await db.execute(select(Tenant).where(Tenant.id == mid))).scalar_one_or_none()
    if not msp or msp.tenant_type != TenantType.msp:
        raise HTTPException(status_code=404, detail="MSP not found")

    from datetime import date
    from app.api.billing import record_invoice, invoice_dict
    from app.core.email import send_email
    from app.core.audit import record as audit_record

    data = await _msp_margin(db, msp)
    totals = data["totals"]
    today = date.today()
    period_start = today.replace(day=1)
    lines = [{
        "description": f"{c['name']} - {c['plan']} (retail ${c['retail']} − EVA ${c['effective_wholesale']})",
        "qty": 1, "amount": c["margin"],
    } for c in data["clients"] if c["active"]]

    inv = await record_invoice(
        db, tenant=msp, kind="msp_consolidated",
        amount_cents=totals["msp_payout"] * 100, lines=lines, status="open",
        period_start=period_start, period_end=today,
        notes=(f"Active clients: {totals['active_clients']}. "
               f"Client billing collected by EVA: ${totals['client_mrr']}/mo. "
               f"EVA share: ${totals['eva_share']}/mo. "
               f"Payout to {msp.name}: ${totals['msp_payout']}/mo."),
    )

    # Notify the MSP admins from the invoicing sender.
    admins = (await db.execute(
        select(User).where(User.tenant_id == msp.id, User.role == UserRole.msp_admin, User.is_active == True)  # noqa: E712
    )).scalars().all()
    for a in admins:
        try:
            send_email(
                to=a.email,
                subject=f"EVA Comply - Monthly statement {inv.number}",
                body=(f"Hello {a.display_name or ''},\n\n"
                      f"Your monthly partner statement {inv.number} is ready.\n"
                      f"Active clients: {totals['active_clients']}\n"
                      f"Your payout this month: ${totals['msp_payout']}\n\n"
                      f"View it in the portal under Partner › Statements.\n\nEVA Comply"),
                sender="invoicing",
            )
        except Exception:
            pass
    try:
        await audit_record(db, current_user, "msp.statement.generated",
                           target=msp.name, detail=f"{inv.number} - payout ${totals['msp_payout']}")
        await db.commit()
    except Exception:
        pass
    return {"invoice": invoice_dict(inv)}


@router.get("/{msp_id}/statements")
async def list_statements(msp_id: str, current_user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    from app.models.billing import Invoice
    from app.api.billing import invoice_dict
    try:
        mid = uuid.UUID(msp_id)
    except ValueError:
        raise HTTPException(status_code=404, detail="MSP not found")
    # Super admin sees any; an MSP admin may only see their own org's.
    if current_user.role != UserRole.super_admin:
        if current_user.role not in MSP_ROLES or current_user.tenant_id != mid:
            raise HTTPException(status_code=403, detail="Not allowed")
    rows = (await db.execute(
        select(Invoice).where(Invoice.tenant_id == mid, Invoice.kind == "msp_consolidated")
        .order_by(Invoice.issued_at.desc())
    )).scalars().all()
    return {"statements": [invoice_dict(i) for i in rows]}
