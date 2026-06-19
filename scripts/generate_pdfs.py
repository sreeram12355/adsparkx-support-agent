"""Generate the sample PDF knowledge-base documents using ReportLab.

These produce two realistic policy PDFs committed under /data:
  - refund_policy.pdf
  - service_level_agreement.pdf

Run once:  python scripts/generate_pdfs.py
"""
from __future__ import annotations

from pathlib import Path

from reportlab.lib.pagesizes import LETTER
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.platypus import (
    SimpleDocTemplate,
    Paragraph,
    Spacer,
    ListFlowable,
    ListItem,
)

DATA_DIR = Path(__file__).resolve().parent.parent / "data"


def _styles():
    styles = getSampleStyleSheet()
    styles.add(
        ParagraphStyle(
            name="DocTitle", parent=styles["Title"], fontSize=20, spaceAfter=14
        )
    )
    styles.add(
        ParagraphStyle(
            name="H", parent=styles["Heading2"], spaceBefore=12, spaceAfter=6
        )
    )
    styles.add(
        ParagraphStyle(
            name="Body", parent=styles["BodyText"], fontSize=10.5, leading=15
        )
    )
    return styles


def _bullets(items, styles):
    return ListFlowable(
        [ListItem(Paragraph(t, styles["Body"])) for t in items],
        bulletType="bullet",
        leftIndent=18,
    )


def build_refund_policy():
    s = _styles()
    doc = SimpleDocTemplate(
        str(DATA_DIR / "refund_policy.pdf"),
        pagesize=LETTER,
        title="CloudDesk Refund Policy",
        topMargin=0.9 * inch,
        bottomMargin=0.9 * inch,
    )
    flow = [
        Paragraph("CloudDesk Refund Policy", s["DocTitle"]),
        Paragraph("Category: Billing &amp; Legal &nbsp;|&nbsp; Effective: 2026-01-01", s["Body"]),
        Spacer(1, 10),

        Paragraph("1. Overview", s["H"]),
        Paragraph(
            "This policy describes when CloudDesk subscription charges are eligible "
            "for a refund. It applies to self-service Starter and Business plans. "
            "Enterprise agreements are governed by their individual contract terms.",
            s["Body"],
        ),

        Paragraph("2. Refund eligibility window", s["H"]),
        _bullets(
            [
                "New subscriptions: full refund if requested within 14 days of the "
                "initial charge and the workspace has fewer than 5 active users.",
                "Monthly renewals: refunds are not issued for monthly renewals once "
                "the new billing cycle has started. You may cancel to stop future charges.",
                "Annual plans: a prorated refund of unused full months is available "
                "within 30 days of the annual charge.",
            ],
            s,
        ),

        Paragraph("3. Non-refundable items", s["H"]),
        _bullets(
            [
                "Charges older than the eligibility windows above.",
                "Usage-based add-ons that have already been consumed.",
                "Taxes already remitted to tax authorities.",
            ],
            s,
        ),

        Paragraph("4. How to request a refund", s["H"]),
        Paragraph(
            "Refund requests are reviewed individually by a human billing specialist "
            "and are not processed automatically. A Workspace Owner or Billing Admin "
            "must submit the request from Settings &rarr; Billing &rarr; Request Refund, "
            "or by contacting billing support with the invoice number. Approved refunds "
            "are returned to the original payment method within 5–10 business days.",
            s["Body"],
        ),

        Paragraph("5. Disputes and chargebacks", s["H"]),
        Paragraph(
            "If you believe you were charged in error, contact billing support before "
            "initiating a chargeback with your bank. Chargebacks filed without prior "
            "contact may result in the workspace being suspended pending resolution. "
            "All disputes are handled by a human specialist.",
            s["Body"],
        ),
    ]
    doc.build(flow)


def build_sla():
    s = _styles()
    doc = SimpleDocTemplate(
        str(DATA_DIR / "service_level_agreement.pdf"),
        pagesize=LETTER,
        title="CloudDesk Service Level Agreement",
        topMargin=0.9 * inch,
        bottomMargin=0.9 * inch,
    )
    flow = [
        Paragraph("CloudDesk Service Level Agreement (SLA)", s["DocTitle"]),
        Paragraph("Category: Reliability &amp; Commercial &nbsp;|&nbsp; Applies to: Business &amp; Enterprise", s["Body"]),
        Spacer(1, 10),

        Paragraph("1. Uptime commitment", s["H"]),
        Paragraph(
            "CloudDesk commits to a monthly uptime of 99.9% for Business plans and "
            "99.95% for Enterprise plans, measured as the percentage of minutes the "
            "core ticketing API is available, excluding scheduled maintenance.",
            s["Body"],
        ),

        Paragraph("2. Support response targets", s["H"]),
        _bullets(
            [
                "Sev-1 (service down, business operations halted): first response "
                "within 1 hour, 24x7.",
                "Sev-2 (major feature impaired): first response within 4 business hours.",
                "Sev-3 (minor issue / question): first response within 1 business day.",
            ],
            s,
        ),

        Paragraph("3. Business impact &amp; service credits", s["H"]),
        Paragraph(
            "If monthly uptime falls below the committed level, affected customers may "
            "claim service credits against the next invoice:",
            s["Body"],
        ),
        _bullets(
            [
                "99.0%–99.9%: 10% credit.",
                "95.0%–99.0%: 25% credit.",
                "Below 95.0%: 50% credit.",
            ],
            s,
        ),
        Paragraph(
            "Credits must be requested within 30 days of the incident and are the "
            "exclusive remedy for downtime. Credit requests are reviewed by a human "
            "account manager.",
            s["Body"],
        ),

        Paragraph("4. Incident communication", s["H"]),
        Paragraph(
            "All incidents are posted to status.clouddesk.com. For Sev-1 incidents, "
            "Enterprise customers receive a formal Root Cause Analysis (RCA) within 5 "
            "business days describing scope, duration, business impact, and corrective "
            "actions. Questions about how a specific incident affected your operations "
            "or your eligibility for credits should be raised with your account manager.",
            s["Body"],
        ),

        Paragraph("5. Exclusions", s["H"]),
        _bullets(
            [
                "Scheduled maintenance announced at least 48 hours in advance.",
                "Issues caused by customer misconfiguration or third-party integrations.",
                "Force majeure events outside CloudDesk's reasonable control.",
            ],
            s,
        ),
    ]
    doc.build(flow)


if __name__ == "__main__":
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    build_refund_policy()
    build_sla()
    print(f"Generated PDFs in {DATA_DIR}:")
    print(" - refund_policy.pdf")
    print(" - service_level_agreement.pdf")
