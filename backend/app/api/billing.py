"""
Billing API — subscription, plan, usage and numbered invoices.

Direct clients pay EVA via Stripe Checkout (monthly or yearly). Each paid
Stripe invoice is mirrored as a numbered Invoice row (INV-YYYY-NNNN) so the
portal has a self-contained, downloadable billing history. When no Stripe key
is configured the checkout is simulated and still produces a numbered invoice
so the screen works end-to-end.
"""
import uuid
from datetime import date, datetime

from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import HTMLResponse
from pydantic import BaseModel
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.config import settings
from app.core import stripe_svc
from app.api.auth import get_current_user
from app.models.user import User, UserRole
from app.models.tenant import Tenant, SubscriptionStatus
from app.models.framework import Framework, Control
from app.models.evidence import OrgControl
from app.models.billing import BillingPlan, Invoice

router = APIRouter()

BILLING_ROLES = {UserRole.super_admin, UserRole.msp_admin, UserRole.client_admin}
PLAN_MRR = {"Professional": 499, "MSP Professional": 1499}
FRONTEND_URL = settings.FRONTEND_URL


# ════════════════ INVOICE HELPERS ════════════════
async def next_invoice_number(db: AsyncSession) -> str:
    """Sequential per-year number, e.g. INV-2026-0007."""
    year = date.today().year
    prefix = f"INV-{year}-"
    n = (await db.execute(
        select(func.count(Invoice.id)).where(Invoice.number.like(prefix + "%"))
    )).scalar_one()
    return f"{prefix}{n + 1:04d}"


async def record_invoice(db: AsyncSession, *, tenant: Tenant | None, kind: str,
                         amount_cents: int, lines: list, status: str = "paid",
                         currency: str = "usd", period_start: date | None = None,
                         period_end: date | None = None, notes: str | None = None,
                         stripe_invoice_id: str | None = None,
                         stripe_payment_intent: str | None = None) -> Invoice:
    inv = Invoice(
        number=await next_invoice_number(db),
        tenant_id=tenant.id if tenant else None,
        tenant_name=tenant.name if tenant else "",
        kind=kind, amount_cents=amount_cents, currency=currency, status=status,
        lines=lines, notes=notes, period_start=period_start, period_end=period_end,
        stripe_invoice_id=stripe_invoice_id, stripe_payment_intent=stripe_payment_intent,
        issued_at=datetime.now(),
        paid_at=datetime.now() if status == "paid" else None,
    )
    db.add(inv)
    await db.commit()
    await db.refresh(inv)
    return inv


def invoice_dict(inv: Invoice) -> dict:
    return {
        "id": str(inv.id), "number": inv.number, "kind": inv.kind,
        "tenant_name": inv.tenant_name,
        "amount": round(inv.amount_cents / 100, 2), "currency": inv.currency,
        "status": inv.status,
        "period_start": inv.period_start.isoformat() if inv.period_start else None,
        "period_end": inv.period_end.isoformat() if inv.period_end else None,
        "issued_at": inv.issued_at.isoformat() if inv.issued_at else None,
        "paid_at": inv.paid_at.isoformat() if inv.paid_at else None,
        "lines": inv.lines or [], "notes": inv.notes,
        "stripe_invoice_id": inv.stripe_invoice_id,
    }


async def _plan_for_tenant(db: AsyncSession, t: Tenant) -> BillingPlan | None:
    if t.plan_id:
        return (await db.execute(select(BillingPlan).where(BillingPlan.id == t.plan_id))).scalar_one_or_none()
    if t.plan_name:
        return (await db.execute(select(BillingPlan).where(BillingPlan.name == t.plan_name))).scalar_one_or_none()
    return None


# ════════════════ OVERVIEW ════════════════
@router.get("/")
async def billing_overview(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    if current_user.role not in BILLING_ROLES:
        raise HTTPException(status_code=403, detail="Billing requires admin access")

    t = (await db.execute(select(Tenant).where(Tenant.id == current_user.tenant_id))).scalar_one()
    plan = await _plan_for_tenant(db, t)
    price = t.monthly_price or (plan.price_monthly if plan else 0) or PLAN_MRR.get(t.plan_name or "", 0)

    seats = (await db.execute(
        select(func.count(User.id)).where(User.tenant_id == t.id)
    )).scalar_one()
    frameworks = (await db.execute(
        select(func.count(func.distinct(Framework.id)))
        .join(Control, Control.framework_id == Framework.id)
        .join(OrgControl, OrgControl.control_id == Control.id)
        .where(OrgControl.org_id == t.id)
    )).scalar_one()

    invoices = (await db.execute(
        select(Invoice).where(Invoice.tenant_id == t.id).order_by(Invoice.issued_at.desc()).limit(24)
    )).scalars().all()

    yearly = stripe_svc.yearly_price(plan) if plan else price * 12
    disc = plan.yearly_discount_pct if plan else 0
    sub = t.settings or {}
    active = t.subscription_status == SubscriptionStatus.active
    cancel_at_end = bool(sub.get("cancel_at_period_end"))

    return {
        "tenant": t.name,
        "tenant_type": t.tenant_type.value,
        "plan": t.plan_name or (plan.name if plan else "—"),
        "status": t.subscription_status.value,
        "price": price,
        "yearly_price": yearly,
        "yearly_discount_pct": disc,
        "seats": seats,
        "frameworks": frameworks,
        "invoices": [invoice_dict(i) for i in invoices],
        "stripe_connected": bool(t.subscription_id),
        "stripe_enabled": bool(settings.STRIPE_SECRET_KEY),
        # Auto-renewal lifecycle
        "interval": sub.get("interval", "month"),
        "auto_renew": active and not cancel_at_end,
        "cancel_at_period_end": cancel_at_end,
        "renews_at": sub.get("renews_at"),
    }


# ════════════════ STRIPE CHECKOUT ════════════════
class CheckoutBody(BaseModel):
    plan: str = "Professional"
    interval: str = "month"          # "month" | "year"
    success_url: str | None = None
    cancel_url: str | None = None


@router.post("/checkout")
async def checkout(
    body: CheckoutBody,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    if current_user.role not in BILLING_ROLES:
        raise HTTPException(status_code=403, detail="Billing requires admin access")
    t = (await db.execute(select(Tenant).where(Tenant.id == current_user.tenant_id))).scalar_one()
    plan = await _plan_for_tenant(db, t)
    interval = "year" if body.interval == "year" else "month"

    monthly = t.monthly_price or (plan.price_monthly if plan else 0) or PLAN_MRR.get(body.plan, 499)
    if interval == "year":
        amount = stripe_svc.yearly_price(plan) if plan else monthly * 12
    else:
        amount = monthly

    success = body.success_url or f"{FRONTEND_URL}/billing"
    cancel = body.cancel_url or f"{FRONTEND_URL}/billing"
    rec = "year" if interval == "year" else "month"
    today = date.today()
    if interval == "year":
        period_end = date(today.year + 1, today.month, 1)
    else:
        period_end = date(today.year + (1 if today.month == 12 else 0), today.month % 12 + 1, 1)

    # No Stripe key → simulate the subscription and still issue a numbered invoice.
    if not settings.STRIPE_SECRET_KEY:
        t.plan_name = body.plan
        t.monthly_price = monthly
        t.subscription_status = SubscriptionStatus.active
        t.settings = {**(t.settings or {}), "interval": interval,
                      "renews_at": period_end.isoformat(), "cancel_at_period_end": False}
        await db.commit()
        inv = await record_invoice(
            db, tenant=t, kind="subscription", amount_cents=amount * 100,
            lines=[{"description": f"{body.plan} — {rec}ly subscription", "qty": 1, "amount": amount}],
            status="paid", period_start=today, period_end=period_end,
            notes="Simulated — no Stripe key configured.",
        )
        # Payment confirmed (simulated) → email the agreement to the admins.
        from app.core.agreement_email import send_contract_email
        await send_contract_email(db, t)
        return {"simulated": True, "status": "active", "invoice": invoice_dict(inv),
                "message": "Subscription activated (simulated — no Stripe key configured)."}

    # Stripe-managed trial when the platform is in card-trial mode.
    from app.core.platform import get_settings
    from app.core.entitlements import effective_mode
    ps = await get_settings(db)
    subscription_data = {}
    if effective_mode(t, ps) == "card_trial" and ps.trial_days > 0:
        subscription_data["trial_period_days"] = ps.trial_days

    import stripe
    stripe.api_key = settings.STRIPE_SECRET_KEY
    try:
        session = stripe.checkout.Session.create(
            mode="subscription",
            line_items=[{
                "price_data": {
                    "currency": "usd",
                    "product_data": {"name": f"EVA Portal — {body.plan} ({rec}ly)"},
                    "unit_amount": amount * 100,
                    "recurring": {"interval": rec},
                },
                "quantity": 1,
            }],
            subscription_data=subscription_data or None,
            success_url=success + "?checkout=success",
            cancel_url=cancel + "?checkout=cancel",
            client_reference_id=str(t.id),
            metadata={"tenant_id": str(t.id), "plan": body.plan, "interval": interval},
        )
    except Exception as e:
        raise HTTPException(status_code=502, detail=f"Stripe error: {e}")
    return {"simulated": False, "url": session.url}


# ════════════════ AUTO-RENEWAL CONTROL ════════════════
@router.post("/cancel")
async def cancel_subscription(current_user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    """Turn off auto-renewal: the plan stays active until the period end, then stops."""
    if current_user.role not in BILLING_ROLES:
        raise HTTPException(status_code=403, detail="Billing requires admin access")
    t = (await db.execute(select(Tenant).where(Tenant.id == current_user.tenant_id))).scalar_one()
    if settings.STRIPE_SECRET_KEY and t.subscription_id:
        import stripe
        stripe.api_key = settings.STRIPE_SECRET_KEY
        try:
            stripe.Subscription.modify(t.subscription_id, cancel_at_period_end=True)
        except Exception as e:
            raise HTTPException(status_code=502, detail=f"Stripe error: {e}")
    t.settings = {**(t.settings or {}), "cancel_at_period_end": True}
    await db.commit()
    return {"ok": True, "auto_renew": False, "renews_at": (t.settings or {}).get("renews_at")}


@router.post("/resume")
async def resume_subscription(current_user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    """Re-enable auto-renewal before the period ends."""
    if current_user.role not in BILLING_ROLES:
        raise HTTPException(status_code=403, detail="Billing requires admin access")
    t = (await db.execute(select(Tenant).where(Tenant.id == current_user.tenant_id))).scalar_one()
    if settings.STRIPE_SECRET_KEY and t.subscription_id:
        import stripe
        stripe.api_key = settings.STRIPE_SECRET_KEY
        try:
            stripe.Subscription.modify(t.subscription_id, cancel_at_period_end=False)
        except Exception as e:
            raise HTTPException(status_code=502, detail=f"Stripe error: {e}")
    t.settings = {**(t.settings or {}), "cancel_at_period_end": False}
    await db.commit()
    return {"ok": True, "auto_renew": True, "renews_at": (t.settings or {}).get("renews_at")}


# ════════════════ WEBHOOK ════════════════
@router.post("/webhook")
async def stripe_webhook(request: Request, db: AsyncSession = Depends(get_db)):
    """Stripe webhook — unauthenticated; signature-verified with the webhook secret."""
    payload = await request.body()
    sig = request.headers.get("stripe-signature", "")
    if not settings.STRIPE_WEBHOOK_SECRET:
        raise HTTPException(status_code=400, detail="Webhook not configured")
    import stripe
    try:
        event = stripe.Webhook.construct_event(payload, sig, settings.STRIPE_WEBHOOK_SECRET)
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Invalid webhook: {e}")

    etype = event["type"]
    obj = event["data"]["object"]

    if etype == "checkout.session.completed":
        tid = (obj.get("metadata") or {}).get("tenant_id") or obj.get("client_reference_id")
        if tid:
            t = (await db.execute(select(Tenant).where(Tenant.id == tid))).scalar_one_or_none()
            if t:
                t.subscription_status = SubscriptionStatus.active
                t.subscription_id = obj.get("subscription")
                if obj.get("customer"):
                    t.stripe_customer_id = obj.get("customer")
                await db.commit()
                # Payment confirmed → email the signed agreement to the admins.
                from app.core.agreement_email import send_contract_email
                await send_contract_email(db, t)

    elif etype == "invoice.paid":
        # Mirror every recurring Stripe invoice as a numbered local invoice.
        sub = obj.get("subscription")
        cust = obj.get("customer")
        t = None
        if sub:
            t = (await db.execute(select(Tenant).where(Tenant.subscription_id == sub))).scalar_one_or_none()
        if not t and cust:
            t = (await db.execute(select(Tenant).where(Tenant.stripe_customer_id == cust))).scalar_one_or_none()
        sid = obj.get("id")
        exists = None
        if sid:
            exists = (await db.execute(select(Invoice).where(Invoice.stripe_invoice_id == sid))).scalar_one_or_none()
        if t and not exists:
            amount = int(obj.get("amount_paid") or obj.get("amount_due") or 0)
            lines = []
            for li in ((obj.get("lines") or {}).get("data") or []):
                lines.append({"description": li.get("description") or "Subscription",
                              "qty": (li.get("quantity") or 1),
                              "amount": round(int(li.get("amount") or 0) / 100, 2)})
            await record_invoice(
                db, tenant=t, kind="subscription", amount_cents=amount,
                lines=lines or [{"description": "Subscription", "qty": 1, "amount": round(amount / 100, 2)}],
                status="paid", currency=(obj.get("currency") or "usd"),
                stripe_invoice_id=sid, stripe_payment_intent=obj.get("payment_intent"),
            )
            if t.subscription_status != SubscriptionStatus.active:
                t.subscription_status = SubscriptionStatus.active
                await db.commit()

    elif etype == "customer.subscription.updated":
        sub = obj.get("id")
        t = (await db.execute(select(Tenant).where(Tenant.subscription_id == sub))).scalar_one_or_none() if sub else None
        if t:
            cpe = obj.get("current_period_end")
            renews = datetime.utcfromtimestamp(cpe).date().isoformat() if cpe else (t.settings or {}).get("renews_at")
            t.settings = {**(t.settings or {}),
                          "cancel_at_period_end": bool(obj.get("cancel_at_period_end")),
                          "renews_at": renews}
            await db.commit()

    elif etype in ("invoice.payment_failed", "customer.subscription.deleted"):
        sub = obj.get("subscription") or obj.get("id")
        if sub:
            t = (await db.execute(select(Tenant).where(Tenant.subscription_id == sub))).scalar_one_or_none()
            if t:
                t.subscription_status = (SubscriptionStatus.past_due
                                         if etype == "invoice.payment_failed"
                                         else SubscriptionStatus.cancelled)
                await db.commit()
    return {"received": True}


# ════════════════ INVOICES ════════════════
@router.get("/invoices")
async def list_invoices(
    tenant_id: str | None = None,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Caller's invoices. Super admin may pass tenant_id to view any tenant's."""
    q = select(Invoice).order_by(Invoice.issued_at.desc())
    if current_user.role == UserRole.super_admin:
        if tenant_id:
            q = q.where(Invoice.tenant_id == tenant_id)
    else:
        if current_user.role not in BILLING_ROLES:
            raise HTTPException(status_code=403, detail="Billing requires admin access")
        q = q.where(Invoice.tenant_id == current_user.tenant_id)
    rows = (await db.execute(q.limit(200))).scalars().all()
    return {"invoices": [invoice_dict(i) for i in rows]}


async def _get_invoice_scoped(db, current_user, invoice_id) -> Invoice:
    try:
        iid = uuid.UUID(invoice_id)
    except ValueError:
        raise HTTPException(status_code=404, detail="Invoice not found")
    inv = (await db.execute(select(Invoice).where(Invoice.id == iid))).scalar_one_or_none()
    if not inv:
        raise HTTPException(status_code=404, detail="Invoice not found")
    if current_user.role != UserRole.super_admin and inv.tenant_id != current_user.tenant_id:
        raise HTTPException(status_code=403, detail="Not your invoice")
    return inv


def _invoice_html(inv: Invoice) -> str:
    from html import escape as esc
    rows = "".join(
        f"<tr><td>{esc(str(l.get('description','')))}</td><td style='text-align:center'>{esc(str(l.get('qty',1)))}</td>"
        f"<td style='text-align:right'>${float(l.get('amount',0) or 0):,.2f}</td></tr>"
        for l in (inv.lines or [])
    )
    kind_label = {"subscription": "Subscription invoice",
                  "msp_consolidated": "MSP monthly statement",
                  "manual": "Invoice"}.get(inv.kind, "Invoice")
    period = ""
    if inv.period_start or inv.period_end:
        period = f"<p><b>Period:</b> {inv.period_start or '—'} → {inv.period_end or '—'}</p>"
    return f"""<!doctype html><html><head><meta charset="utf-8">
<title>{inv.number}</title>
<style>
 body{{font-family:-apple-system,Segoe UI,Roboto,sans-serif;color:#1e293b;max-width:720px;margin:40px auto;padding:0 24px}}
 .hd{{display:flex;justify-content:space-between;align-items:flex-start;border-bottom:3px solid #2563eb;padding-bottom:16px}}
 .brand{{font-size:22px;font-weight:800;color:#2563eb}}
 .muted{{color:#64748b;font-size:13px}}
 table{{width:100%;border-collapse:collapse;margin-top:24px}}
 th,td{{padding:10px 8px;border-bottom:1px solid #e2e8f0;font-size:14px}}
 th{{text-align:left;color:#64748b;font-size:12px;text-transform:uppercase}}
 .total{{text-align:right;font-size:20px;font-weight:800;margin-top:16px}}
 .badge{{display:inline-block;padding:3px 10px;border-radius:999px;font-size:12px;font-weight:700}}
 .paid{{background:#dcfce7;color:#166534}} .open{{background:#fef9c3;color:#854d0e}}
 @media print{{.noprint{{display:none}}}}
</style></head><body>
<div class="hd">
  <div><div class="brand">EVA Comply</div><div class="muted">EVA Technologies</div></div>
  <div style="text-align:right">
    <div style="font-size:18px;font-weight:700">{esc(inv.number)}</div>
    <div class="muted">{kind_label}</div>
    <div class="muted">Issued {inv.issued_at.strftime('%Y-%m-%d') if inv.issued_at else ''}</div>
  </div>
</div>
<p><b>Billed to:</b> {esc(inv.tenant_name or '—')}</p>
{period}
<p>Status: <span class="badge {'paid' if inv.status=='paid' else 'open'}">{esc(inv.status.upper())}</span></p>
<table><thead><tr><th>Description</th><th style="text-align:center">Qty</th><th style="text-align:right">Amount</th></tr></thead>
<tbody>{rows or '<tr><td colspan=3 class=muted>No line items</td></tr>'}</tbody></table>
<div class="total">Total: ${inv.amount_cents/100:,.2f} {esc(inv.currency.upper())}</div>
{f'<p class="muted">{esc(inv.notes)}</p>' if inv.notes else ''}
<p class="noprint muted" style="margin-top:32px"><button onclick="window.print()">Print / Save as PDF</button></p>
</body></html>"""


@router.get("/invoices/{invoice_id}/download", response_class=HTMLResponse)
async def download_invoice(
    invoice_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    inv = await _get_invoice_scoped(db, current_user, invoice_id)
    return HTMLResponse(_invoice_html(inv))
