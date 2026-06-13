"""Curated pre-made remediation recommendations, keyed by control ref.

NIST SP 800-171r3 control refs (03.xx.xx). Each value is a list of
recommendations, each a dict: {title, text, effort, impact}.

  effort ∈ {low, medium, high}   — relative implementation lift
  impact ∈ {low, medium, high}   — security/compliance value of doing it

A "quick win" is low effort + high impact. Controls without an entry fall back
to a recommendation derived from the control's maturity ladder (the statement
at the target level), so coverage is universal. Reused for ITSP.10.171 (shared
refs) and CMMC L1/L2 (mapped) by the recommendations engine.
"""

NIST_171R3_RECS: dict[str, list[dict]] = {
    # ── 03.01 Access Control ──────────────────────────────────────────
    "03.01.01": [
        {"title": "Centralize account lifecycle in your IdP",
         "text": "Move account provisioning, changes, and deprovisioning into a single identity provider (e.g. Entra ID, Okta, Google Workspace) so every system inherits one source of truth. Tie joiner/mover/leaver events to HR so accounts are disabled the day someone leaves.",
         "effort": "medium", "impact": "high"},
        {"title": "Schedule quarterly access recertification",
         "text": "Run a recurring access review where managers attest to who has access to each system. Document the review and remove anything no longer needed. Start with CUI-bearing systems.",
         "effort": "low", "impact": "high"},
    ],
    "03.01.02": [
        {"title": "Enforce access from a central policy, not per-host config",
         "text": "Replace per-system local permissions with group/role-based rules managed centrally so authorizations are applied consistently and revoked in one place.",
         "effort": "medium", "impact": "high"},
    ],
    "03.01.03": [
        {"title": "Segment the CUI environment and filter egress",
         "text": "Place CUI systems on a dedicated network segment/VLAN with deny-by-default firewall rules, and add egress filtering (and DLP where feasible) so CUI cannot flow to unapproved destinations.",
         "effort": "high", "impact": "high"},
    ],
    "03.01.04": [
        {"title": "Document and enforce separation of duties",
         "text": "Map the conflicting duties for critical processes (e.g. request vs. approve, develop vs. deploy) and enforce them with role assignments; review for toxic combinations each quarter.",
         "effort": "medium", "impact": "medium"},
    ],
    "03.01.05": [
        {"title": "Right-size permissions to least privilege",
         "text": "Audit current entitlements, strip access beyond what each role needs, and adopt just-in-time elevation for occasional admin tasks. Recertify on a schedule.",
         "effort": "medium", "impact": "high"},
    ],
    "03.01.06": [
        {"title": "Lock down and broker privileged accounts",
         "text": "Inventory all admin accounts, remove standing/shared admin where possible, require MFA, and move privileged access to just-in-time elevation with full session logging.",
         "effort": "medium", "impact": "high"},
        {"title": "Separate admin identities from daily-use accounts",
         "text": "Give administrators a distinct privileged account used only for admin work, never for email or browsing. Low lift, immediate blast-radius reduction.",
         "effort": "low", "impact": "high"},
    ],
    "03.01.07": [
        {"title": "Log and alert on privileged function use",
         "text": "Restrict privileged functions to authorized roles and forward their use to your log pipeline with alerting on anomalous activity.",
         "effort": "medium", "impact": "medium"},
    ],
    "03.01.08": [
        {"title": "Enforce account lockout / throttling everywhere",
         "text": "Configure lockout or rate-limiting on failed logons at the central identity provider so the policy applies uniformly, and alert on brute-force patterns.",
         "effort": "low", "impact": "medium"},
    ],
    "03.01.10": [
        {"title": "Push device-lock timeouts via policy",
         "text": "Deploy a managed policy (Intune/MDM/GPO) that locks endpoints after a short inactivity period across all devices, instead of relying on users.",
         "effort": "low", "impact": "medium"},
    ],
    "03.01.11": [
        {"title": "Set session timeouts on apps and remote access",
         "text": "Configure idle and absolute session timeouts on critical applications and VPN/remote sessions so sessions do not stay open indefinitely.",
         "effort": "low", "impact": "medium"},
    ],
    "03.01.12": [
        {"title": "Require MFA and monitoring on all remote access",
         "text": "Front all remote access with an MFA-protected, hardened gateway; disable split tunneling and forward logs centrally for monitoring.",
         "effort": "medium", "impact": "high"},
    ],
    "03.01.16": [
        {"title": "Move to enterprise wireless authentication",
         "text": "Adopt 802.1X / WPA-Enterprise for corporate wireless, separate guest traffic onto its own network, and enable rogue-AP detection.",
         "effort": "medium", "impact": "medium"},
    ],
    "03.01.18": [
        {"title": "Enroll all mobile devices in MDM",
         "text": "Require MDM enrollment with encryption, screen lock, and remote-wipe before a device can reach corporate data; bring BYOD under at least app-level management.",
         "effort": "medium", "impact": "high"},
    ],
    "03.01.20": [
        {"title": "Govern external systems and sanction alternatives",
         "text": "Publish an approved-services list, block known high-risk SaaS for CUI, and give staff sanctioned tools so shadow IT is unnecessary.",
         "effort": "medium", "impact": "medium"},
    ],

    # ── 03.02 Awareness & Training ────────────────────────────────────
    "03.02.01": [
        {"title": "Stand up recurring security awareness training",
         "text": "Roll out role-based security awareness training at onboarding and at least annually, including phishing simulations, and track completion.",
         "effort": "low", "impact": "high"},
    ],
    "03.02.02": [
        {"title": "Add role-specific training for privileged staff",
         "text": "Supplement general awareness with targeted training for admins, developers, and anyone handling CUI on their specific responsibilities.",
         "effort": "low", "impact": "medium"},
    ],

    # ── 03.03 Audit & Accountability ──────────────────────────────────
    "03.03.01": [
        {"title": "Centralize logs into a SIEM/log store",
         "text": "Forward security-relevant logs from endpoints, servers, identity, and network devices into a central, time-synced store with sufficient retention to support investigations.",
         "effort": "high", "impact": "high"},
    ],
    "03.03.03": [
        {"title": "Define and document what events you log",
         "text": "Agree the set of auditable events (logons, privilege use, config changes, CUI access) and review the list periodically so coverage stays current.",
         "effort": "low", "impact": "medium"},
    ],
    "03.03.05": [
        {"title": "Build alerting on top of your logs",
         "text": "Add correlation and alerting for high-risk patterns (impossible travel, mass deletes, privilege escalation) so log data is acted on, not just stored.",
         "effort": "medium", "impact": "high"},
    ],

    # ── 03.04 Configuration Management ────────────────────────────────
    "03.04.01": [
        {"title": "Establish and enforce secure baselines",
         "text": "Adopt hardened baseline configurations (e.g. CIS Benchmarks) for OSes and key apps, deploy them via MDM/GPO, and monitor for drift.",
         "effort": "high", "impact": "high"},
    ],
    "03.04.02": [
        {"title": "Put configuration changes under change control",
         "text": "Require review/approval for changes to baseline configurations and keep a record of what changed, when, and by whom.",
         "effort": "medium", "impact": "medium"},
    ],
    "03.04.06": [
        {"title": "Apply least-functionality hardening",
         "text": "Disable unused ports, protocols, services, and software on systems, and document the approved functionality for each system role.",
         "effort": "medium", "impact": "medium"},
    ],
    "03.04.08": [
        {"title": "Move to application allow-listing",
         "text": "Where feasible, deny-by-default for software execution and allow only approved applications, starting with CUI and high-value systems.",
         "effort": "high", "impact": "high"},
    ],

    # ── 03.05 Identification & Authentication ─────────────────────────
    "03.05.01": [
        {"title": "Ensure unique identification for every user",
         "text": "Eliminate shared/generic accounts so every action is attributable to an individual; where a shared service account is unavoidable, document and tightly control it.",
         "effort": "low", "impact": "medium"},
    ],
    "03.05.03": [
        {"title": "Enforce phishing-resistant MFA",
         "text": "Require MFA for all users and prioritize phishing-resistant factors (FIDO2/passkeys, app push with number matching) over SMS, starting with admins and remote access.",
         "effort": "medium", "impact": "high"},
    ],
    "03.05.05": [
        {"title": "Disable identifier reuse and stale accounts",
         "text": "Prevent reuse of user identifiers and automatically disable accounts after a defined period of inactivity.",
         "effort": "low", "impact": "medium"},
    ],
    "03.05.07": [
        {"title": "Modernize password policy to current guidance",
         "text": "Adopt length-based passphrases with breached-password screening and drop forced periodic rotation, aligning with NIST SP 800-63B; back it with MFA.",
         "effort": "low", "impact": "medium"},
    ],

    # ── 03.06 Incident Response ───────────────────────────────────────
    "03.06.01": [
        {"title": "Write and socialize an incident response plan",
         "text": "Document an IR plan with roles, severity tiers, contact tree, and reporting obligations; store it offline and make sure responders know it.",
         "effort": "medium", "impact": "high"},
    ],
    "03.06.02": [
        {"title": "Run a tabletop exercise",
         "text": "Test the IR plan at least annually with a tabletop scenario, capture gaps, and feed fixes back into the plan.",
         "effort": "low", "impact": "high"},
    ],

    # ── 03.07 Maintenance ─────────────────────────────────────────────
    "03.07.04": [
        {"title": "Control and scan maintenance tools/media",
         "text": "Inspect and scan media and tools used for maintenance before use, and supervise or authorize remote maintenance sessions.",
         "effort": "low", "impact": "medium"},
    ],

    # ── 03.08 Media Protection ────────────────────────────────────────
    "03.08.03": [
        {"title": "Sanitize media before disposal or reuse",
         "text": "Adopt a documented sanitization/destruction process for media holding CUI (cryptographic erase, wipe, or shred) with certificates of destruction.",
         "effort": "low", "impact": "medium"},
    ],
    "03.08.05": [
        {"title": "Control and log removable-media use",
         "text": "Restrict removable media by policy and technical control (e.g. block USB mass storage by default), allowing only approved, encrypted devices.",
         "effort": "medium", "impact": "medium"},
    ],
    "03.08.07": [
        {"title": "Encrypt CUI on portable media and devices",
         "text": "Require full-disk and removable-media encryption so CUI at rest on portable storage is protected if lost or stolen.",
         "effort": "low", "impact": "high"},
    ],

    # ── 03.10 Physical Protection ─────────────────────────────────────
    "03.10.07": [
        {"title": "Control and monitor physical access",
         "text": "Restrict physical access to systems and CUI to authorized staff with badge/lock controls, maintain visitor logs, and review access periodically.",
         "effort": "medium", "impact": "medium"},
    ],

    # ── 03.11 Risk Assessment ─────────────────────────────────────────
    "03.11.01": [
        {"title": "Perform a documented risk assessment",
         "text": "Run a periodic risk assessment of systems handling CUI, record threats/likelihood/impact, and use it to prioritize remediation.",
         "effort": "medium", "impact": "high"},
    ],
    "03.11.02": [
        {"title": "Establish recurring vulnerability scanning",
         "text": "Scan systems for vulnerabilities on a schedule and after significant changes, then track findings to closure with SLAs by severity.",
         "effort": "medium", "impact": "high"},
    ],
    "03.11.04": [
        {"title": "Define a risk-based remediation process",
         "text": "Prioritize and remediate vulnerabilities by risk, with documented timelines and exceptions, rather than ad-hoc patching.",
         "effort": "medium", "impact": "medium"},
    ],

    # ── 03.12 Security Assessment ─────────────────────────────────────
    "03.12.01": [
        {"title": "Assess controls and maintain a POA&M",
         "text": "Periodically assess control effectiveness and track deficiencies in a Plan of Action & Milestones with owners and due dates.",
         "effort": "medium", "impact": "high"},
    ],
    "03.12.02": [
        {"title": "Operationalize the POA&M",
         "text": "Review the POA&M on a cadence, update status, and close items with evidence so it reflects reality at assessment time.",
         "effort": "low", "impact": "medium"},
    ],

    # ── 03.13 System & Communications Protection ──────────────────────
    "03.13.01": [
        {"title": "Harden and monitor network boundaries",
         "text": "Enforce deny-by-default at boundaries, separate internal/external traffic, and monitor boundary devices centrally.",
         "effort": "medium", "impact": "high"},
    ],
    "03.13.08": [
        {"title": "Encrypt CUI in transit",
         "text": "Require TLS 1.2+ (or equivalent) for all transmission of CUI and disable legacy protocols/ciphers.",
         "effort": "low", "impact": "high"},
        {"title": "Encrypt CUI at rest",
         "text": "Apply validated encryption to stored CUI (full-disk plus database/file-level where feasible) on servers, endpoints, and portable devices, since r3 03.13.08 now covers storage as well as transmission.",
         "effort": "medium", "impact": "high"},
    ],
    "03.13.11": [
        {"title": "Use FIPS-validated cryptography for CUI",
         "text": "Standardize on FIPS-validated cryptographic modules for protecting CUI and document where they are applied.",
         "effort": "medium", "impact": "medium"},
    ],

    # ── 03.14 System & Information Integrity ──────────────────────────
    "03.14.01": [
        {"title": "Tighten patch/flaw remediation timelines",
         "text": "Define and meet SLAs for applying security patches (e.g. critical within days), measure compliance, and automate where possible.",
         "effort": "medium", "impact": "high"},
    ],
    "03.14.02": [
        {"title": "Deploy and centrally manage EDR/anti-malware",
         "text": "Run modern endpoint protection (EDR) on all endpoints and servers with central visibility, auto-updates, and alerting.",
         "effort": "medium", "impact": "high"},
    ],
    "03.14.06": [
        {"title": "Monitor systems for attacks and indicators",
         "text": "Add detection for inbound/outbound attack indicators (IDS/IPS, EDR telemetry) and route alerts to a monitored queue.",
         "effort": "medium", "impact": "high"},
    ],
}
