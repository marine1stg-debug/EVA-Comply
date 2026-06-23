import sys; sys.path.insert(0,'tools')
import policy_builder as B
P="policy_library/"
SPECS=[]

SPECS.append({
 "title":"Configuration Management Policy","path":P+"Configuration_Management_Policy.docx",
 "purpose":"This policy establishes how [Organization Name] defines secure baseline configurations for systems that process, store, or transmit Controlled Unclassified Information (CUI), and how changes to those systems are controlled throughout their lifecycle. Unmanaged configurations and uncontrolled changes are a leading cause of security weaknesses. By enforcing hardened baselines, change control, least functionality, and an accurate component inventory, this policy reduces the attack surface and ensures systems remain in a known, secure state.",
 "scope":["All information systems, endpoints, servers, network devices, and cloud services that process, store, or transmit CUI.","All changes to system configurations, software, and firmware on in-scope systems.","All personnel who configure, change, or maintain in-scope systems."],
 "definitions":[("Baseline Configuration","A documented, approved set of configuration settings for a system that serves as the secure starting point."),("Configuration Setting","An adjustable parameter of hardware or software (e.g., a security option, password rule, or service enabled/disabled)."),("Change Control","The formal process of requesting, reviewing, approving, and recording changes to systems."),("Least Functionality","Configuring systems to provide only essential capabilities; disabling unused ports, protocols, and services."),("Allow-listing","Permitting only explicitly approved software to run; everything else is denied by default.")],
 "roles":[["[IT Manager / ISSO]","Own this policy; approve baselines and significant changes; ensure the component inventory is maintained."],["[System Administrator]","Apply and maintain baselines; implement approved changes; disable unneeded functionality; keep the inventory current."],["[Change Approver / CAB]","Review and approve change requests; assess security impact before changes are deployed."],["All Users","Do not make unauthorized changes or install unapproved software; report configuration issues."],["[Senior Leadership / CISO]","Approve this policy; provide tooling; accept residual risk for documented exceptions."]],
 "statements":[
   ("PS-1  Secure Baseline Configurations","[Organization Name] must establish, document, and maintain secure baseline configurations for each class of system, based on recognized hardening guidance (e.g., CIS Benchmarks or vendor security baselines). Baselines must be applied to new and existing systems."),
   ("PS-2  Configuration Settings","Mandatory security configuration settings must be defined for each system type and enforced via centralized management (e.g., GPO/MDM). Deviations from approved settings must be identified and remediated."),
   ("PS-3  Change Control","Changes to baseline configurations must be requested, security-reviewed, approved, tested where feasible, and recorded before deployment. Emergency changes must follow an expedited process and be documented after the fact."),
   ("PS-4  Security Impact Analysis","The security impact of proposed changes must be analyzed before approval so that changes do not weaken the security posture or introduce new risk."),
   ("PS-5  Access Restrictions for Change","The ability to make configuration changes must be restricted to authorized administrators, logged, and reviewed. Production changes must not be made from standard user accounts."),
   ("PS-6  Least Functionality","Systems must be configured to provide only essential functions. Unused ports, protocols, services, and software must be disabled or removed, and the approved functionality for each system role documented."),
   ("PS-7  Authorized Software (Allow-listing)","Where feasible, software execution must be deny-by-default with only approved applications allowed, prioritizing CUI and high-value systems. A list of approved software must be maintained."),
   ("PS-8  System Component Inventory","An accurate, current inventory of system components (hardware, software, firmware) must be maintained, including where CUI is stored or processed, to support patching, change control, and incident response."),
   ("PS-9  Configuration Monitoring & Drift","Systems must be monitored for unauthorized changes and configuration drift from the approved baseline; deviations must be investigated and corrected."),
 ],
 "procedures":[
   ("6.1  Baseline & Hardening",["Define baselines from CIS/vendor guidance; deploy via GPO/MDM.","Scan or audit systems for compliance with the baseline on a schedule.","Remediate drift within a risk-based timeframe."],"Baseline documents; GPO/MDM exports; configuration-compliance scan reports; remediation records."),
   ("6.2  Change Control",["Submit change requests with security impact; obtain approval; test and deploy.","Record what changed, when, by whom, and the approval."],"Change request/approval records (CAB minutes or tickets); change log; rollback plans."),
   ("6.3  Inventory & Least Functionality",["Maintain the component inventory and update on add/move/change.","Disable unused services/ports; maintain the approved-software list and allow-listing where feasible."],"Component inventory (dated); approved-software list; allow-listing configuration; port/service hardening evidence."),
 ],
 "compliance_focus":"by verifying baselines are applied, changes follow change control, the component inventory is current, and unneeded functionality is disabled.",
 "related":["System Security Plan (SSP) — system inventory and control implementation.","Access Control Policy — restricting who may make changes.","System & Information Integrity Policy — flaw remediation and monitoring that depend on accurate baselines.","Risk Assessment Policy — impact analysis informing change decisions."],
 "mapping_intro":"The table below maps each required control to the policy statement(s) that satisfy it and the evidence an auditor will seek. Control IDs are from NIST SP 800-171 Rev 3 (family 03.04); they are equally applicable to CMMC 2.0 Level 2 and ITSP.10.171 (CPCSC).",
 "mapping":[
   ["03.04.01  Baseline Configuration","PS-1 — secure baselines","Baseline documents; deployment evidence"],
   ["03.04.02  Configuration Settings","PS-2 — enforced settings","GPO/MDM exports; compliance scans"],
   ["03.04.03  Configuration Change Control","PS-3 — change control","Change requests/approvals; change log"],
   ["03.04.04  Impact Analyses","PS-4 — security impact analysis","Impact analysis records in change tickets"],
   ["03.04.05  Access Restrictions for Change","PS-5 — restricted, logged change access","Admin access controls; change logs"],
   ["03.04.06  Least Functionality","PS-6 — disable unused functions","Hardening evidence; approved-function list"],
   ["03.04.08  Authorized Software – Allow by Exception","PS-7 — allow-listing","Approved-software list; allow-listing config"],
   ["03.04.10  System Component Inventory","PS-8 — component inventory","Component inventory (dated)"],
   ["03.04.11  Information Location","PS-8 — where CUI resides","Inventory noting CUI storage/processing locations"],
   ["03.04.12  Config for High-Risk Areas","PS-1, PS-6 — hardened config for high-risk travel/areas","Hardened-device baselines for high-risk use"],
 ],
})

SPECS.append({
 "title":"Identification & Authentication Policy","path":P+"Identification_Authentication_Policy.docx",
 "purpose":"This policy establishes how [Organization Name] uniquely identifies users and devices and verifies their identity before granting access to systems that process, store, or transmit Controlled Unclassified Information (CUI). Strong identification and authentication — especially multi-factor authentication — is one of the most effective defenses against account compromise. This policy ensures every action is attributable to an individual and that credentials are managed securely throughout their lifecycle.",
 "scope":["All users (employees, contractors, vendors) and all devices that access in-scope systems.","All authentication mechanisms, including passwords, MFA, certificates, and service-account credentials.","All systems that process, store, or transmit CUI."],
 "definitions":[("Identifier","A unique name (e.g., username) that distinguishes a user, device, or process."),("Authenticator","Something used to prove identity (e.g., password, hardware token, passkey/FIDO2, certificate)."),("Multi-Factor Authentication (MFA)","Requiring two or more independent factors (something you know, have, or are)."),("Phishing-Resistant MFA","MFA that cannot be easily defeated by phishing (e.g., FIDO2/passkeys, PKI)."),("Service Account","A non-human account used by an application or process.")],
 "roles":[["[IT Manager / ISSO]","Own this policy; define authentication standards; ensure MFA is enforced; oversee credential management."],["[System Administrator]","Provision unique identifiers; configure and enforce MFA and password rules; manage authenticators and service accounts."],["[Human Resources]","Provide authoritative identity information for provisioning and de-provisioning."],["All Users","Protect their credentials; use MFA; never share accounts or authenticators; report compromise."],["[Senior Leadership / CISO]","Approve this policy; fund authentication tooling; accept residual risk for documented exceptions."]],
 "statements":[
   ("PS-1  Unique Identification","Every user, device, and process accessing in-scope systems must be uniquely identified. Shared or generic accounts are prohibited on CUI systems unless technically unavoidable, approved, and documented with compensating controls."),
   ("PS-2  Device Identification & Authentication","Devices connecting to in-scope networks or systems must be identified and authenticated where feasible (e.g., 802.1X, certificates, or device compliance checks)."),
   ("PS-3  Multi-Factor Authentication","MFA must be required for all users, prioritizing phishing-resistant factors (FIDO2/passkeys, PKI) over SMS, starting with privileged accounts, remote access, and access to CUI."),
   ("PS-4  Replay-Resistant Authentication","Authentication to privileged accounts and network access must use mechanisms resistant to replay attacks."),
   ("PS-5  Identifier Management","User identifiers must be issued through an authorized process, never reused, and disabled after a defined period of inactivity. Identifier-to-individual mapping must be maintained."),
   ("PS-6  Password Management","Where passwords are used, they must follow current guidance: length-based passphrases, screening against breached-password lists, no forced periodic rotation absent indication of compromise, and secure storage (salted hashing). Default passwords must be changed before deployment."),
   ("PS-7  Authenticator Management","Authenticators (tokens, certificates, keys) must be issued, protected, rotated, revoked, and recovered through controlled processes. Lost or compromised authenticators must be revoked promptly."),
   ("PS-8  Authentication Feedback","Authentication feedback (e.g., masking password entry) must be managed so it does not expose credentials to observation."),
   ("PS-9  Service & Privileged Credentials","Service-account and privileged credentials must be vaulted, rotated, and access-controlled; standing privileged access must be minimized."),
 ],
 "procedures":[
   ("6.1  Provisioning & MFA",["Provision unique identifiers via the authorized request process; enroll users in MFA before granting access.","Enforce phishing-resistant MFA on admin, remote, and CUI access."],"Identity provider configuration; MFA enrollment reports; access request records."),
   ("6.2  Credential Lifecycle",["Apply password/passphrase rules with breached-password screening.","Vault and rotate service/privileged credentials; revoke on loss or departure."],"Password policy configuration; password-vault logs; revocation records."),
   ("6.3  Identifier Hygiene",["Disable identifiers after defined inactivity; prevent reuse.","Maintain identifier-to-person mapping."],"Inactivity-disable reports; identifier inventory."),
 ],
 "compliance_focus":"by verifying unique identification, MFA enforcement (especially phishing-resistant for privileged/remote/CUI access), and secure credential lifecycle management.",
 "related":["Access Control Policy — authorization that follows authentication.","Personnel Security Policy — onboarding/offboarding that drives provisioning.","System Security Plan (SSP) — implementation details for authentication controls.","Configuration Management Policy — baseline settings enforcing authentication rules."],
 "mapping_intro":"The table below maps each required control to the policy statement(s) that satisfy it and the evidence an auditor will seek. Control IDs are from NIST SP 800-171 Rev 3 (family 03.05); they are equally applicable to CMMC 2.0 Level 2 and ITSP.10.171 (CPCSC).",
 "mapping":[
   ["03.05.01  User Identification and Authentication","PS-1, PS-3 — unique IDs; MFA","Identity provider config; MFA reports"],
   ["03.05.02  Device Identification and Authentication","PS-2 — device auth","802.1X/cert/device-compliance config"],
   ["03.05.03  Multi-Factor Authentication","PS-3 — MFA everywhere, phishing-resistant","MFA enrollment and enforcement evidence"],
   ["03.05.04  Replay-Resistant Authentication","PS-4 — replay resistance","Auth mechanism configuration"],
   ["03.05.05  Identifier Management","PS-5 — issuance, no reuse, inactivity disable","Identifier inventory; inactivity-disable reports"],
   ["03.05.07  Password Management","PS-6 — modern password rules; no defaults","Password policy config; breached-password screening"],
   ["03.05.11  Authentication Feedback","PS-8 — masked feedback","Login UI configuration"],
   ["03.05.12  Authenticator Management","PS-7, PS-9 — authenticator lifecycle; vaulting","Authenticator issuance/revocation; vault logs"],
 ],
})

SPECS.append({
 "title":"Incident Response Policy & Plan","path":P+"Incident_Response_Policy_Plan.docx",
 "purpose":"This policy and plan establish how [Organization Name] prepares for, detects, analyzes, contains, eradicates, recovers from, and reports cybersecurity incidents affecting systems that process, store, or transmit Controlled Unclassified Information (CUI). A prepared, well-rehearsed response limits damage, preserves evidence, and meets contractual and regulatory reporting obligations. This document defines roles, severity levels, and the steps responders follow.",
 "scope":["All cybersecurity incidents and suspected incidents affecting in-scope systems, data, or CUI.","All personnel, contractors, and third parties involved in detecting, reporting, or responding to incidents.","All systems that process, store, or transmit CUI."],
 "definitions":[("Event","Any observable occurrence in a system or network."),("Incident","An event that actually or imminently jeopardizes the confidentiality, integrity, or availability of information or systems."),("Containment","Actions taken to limit the scope and impact of an incident."),("Eradication","Removing the cause of the incident (e.g., malware, unauthorized access)."),("CUI Incident","An incident involving the suspected or confirmed compromise of CUI, which carries specific reporting obligations.")],
 "roles":[["[IT Manager / ISSO]","Own this policy; lead or designate the incident response lead; ensure the plan is current and tested."],["Incident Response Lead","Coordinate response activities; declare severity; manage communications and reporting."],["[System Administrator] / Responders","Execute containment, eradication, and recovery; preserve evidence."],["[Senior Leadership / CISO]","Approve major response decisions; authorize external notifications; accept residual risk."],["All Users","Report suspected incidents immediately through the defined channel; do not attempt to investigate alone."]],
 "statements":[
   ("PS-1  Incident Response Capability","[Organization Name] must maintain an incident response capability covering preparation, detection and analysis, containment, eradication, recovery, and post-incident activity."),
   ("PS-2  Documented Incident Response Plan","A written incident response plan must define roles, severity tiers, the contact/escalation tree, decision authority, and reporting obligations. It must be stored so it remains available during an outage (including offline) and provided to relevant personnel."),
   ("PS-3  Detection & Reporting","Users and systems must have clear channels to report suspected incidents. Security alerts and monitoring (from the Audit & Accountability and System & Information Integrity controls) must feed incident detection."),
   ("PS-4  Triage & Severity","Reported events must be triaged and assigned a severity level that drives response timelines, escalation, and notification."),
   ("PS-5  Containment, Eradication & Recovery","Responders must contain incidents to limit impact, eradicate the cause, and recover affected systems to a known-good state, preserving evidence throughout."),
   ("PS-6  Reporting & Notification","CUI incidents must be reported to the required parties (e.g., government contracting officers / the DoD as required by contract) within the mandated timeframe. Internal and external notifications must be coordinated through leadership."),
   ("PS-7  Incident Response Testing","The plan must be tested at least [annually] (e.g., tabletop exercise); gaps must be captured and fed back into the plan."),
   ("PS-8  Incident Response Training","Responders and relevant staff must receive incident response training appropriate to their role, including how and when to report."),
   ("PS-9  Post-Incident Review","After significant incidents, a lessons-learned review must be conducted and improvements applied to controls and the plan."),
 ],
 "procedures":[
   ("6.1  Detection to Containment",["User/system reports an event through the defined channel; the response lead triages and assigns severity.","Responders contain the incident, preserving logs and evidence."],"Incident tickets with timestamps; severity assignments; evidence-preservation records."),
   ("6.2  Eradication, Recovery & Reporting",["Remove the cause; restore systems to a known-good state; validate.","For CUI incidents, report to required parties within the mandated timeframe."],"Recovery records; CUI-incident reports and submission confirmations."),
   ("6.3  Test & Improve",["Conduct an annual tabletop exercise; capture gaps.","Conduct lessons-learned after significant incidents; update the plan."],"Exercise records; lessons-learned reports; plan revision history."),
 ],
 "compliance_focus":"by verifying the plan is current and tested, incidents are triaged and documented, CUI reporting timelines are met, and responders are trained.",
 "related":["System Security Plan (SSP) — system and CUI context for responders.","Audit & Accountability Policy — logs that support detection and investigation.","System & Information Integrity Policy — monitoring and malicious-code detection feeding incident response.","Access Control Policy — account actions taken during containment."],
 "mapping_intro":"The table below maps each required control to the policy statement(s) that satisfy it and the evidence an auditor will seek. Control IDs are from NIST SP 800-171 Rev 3 (family 03.06); they are equally applicable to CMMC 2.0 Level 2 and ITSP.10.171 (CPCSC).",
 "mapping":[
   ["03.06.01  Incident Handling","PS-1, PS-5 — handling lifecycle","Incident records; containment/recovery evidence"],
   ["03.06.02  Incident Monitoring, Reporting & Response Assistance","PS-3, PS-6 — detection, reporting, assistance","Reporting channels; CUI-incident reports"],
   ["03.06.03  Incident Response Testing","PS-7 — annual testing","Tabletop exercise records"],
   ["03.06.04  Incident Response Training","PS-8 — responder training","Training completion records"],
   ["03.06.05  Incident Response Plan","PS-2 — documented plan","The incident response plan (dated, distributed)"],
 ],
})

SPECS.append({
 "title":"System Maintenance Policy","path":P+"System_Maintenance_Policy.docx",
 "purpose":"This policy establishes how [Organization Name] performs maintenance on systems that process, store, or transmit Controlled Unclassified Information (CUI) in a secure manner, and how it controls maintenance tools, media, personnel, and remote (nonlocal) maintenance sessions. Maintenance activities can introduce malware or expose CUI if uncontrolled. This policy ensures maintenance is authorized, supervised, and does not weaken security.",
 "scope":["All scheduled and unscheduled maintenance on in-scope systems and components.","All maintenance tools, diagnostic equipment, and media used on in-scope systems.","All internal staff, vendors, and third parties who perform maintenance."],
 "definitions":[("Maintenance Tool","Hardware/software used to diagnose, repair, or service a system."),("Nonlocal Maintenance","Maintenance performed over a network from outside the system's physical location."),("Maintenance Personnel","Individuals (internal or external) who perform maintenance."),("Sanitization","Removing data from equipment or media so it cannot be recovered.")],
 "roles":[["[IT Manager / ISSO]","Own this policy; authorize maintenance and maintenance personnel; approve nonlocal maintenance methods."],["[System Administrator]","Schedule and perform maintenance; inspect and control tools/media; supervise vendor maintenance."],["Maintenance Personnel / Vendors","Perform authorized maintenance under the agreed controls; do not remove CUI without authorization."],["All Users","Report maintenance needs through the proper channel; do not allow unauthorized servicing."],["[Senior Leadership / CISO]","Approve this policy; accept residual risk for documented exceptions."]],
 "statements":[
   ("PS-1  Authorized Maintenance","Maintenance on in-scope systems must be authorized, scheduled where possible, and recorded. Only authorized personnel may perform maintenance."),
   ("PS-2  Control of Maintenance Tools & Media","Tools and media used for maintenance must be inspected and scanned for malicious code before use on in-scope systems, and controlled to prevent unauthorized use."),
   ("PS-3  Nonlocal (Remote) Maintenance","Remote maintenance must be authorized, conducted over approved, encrypted, MFA-protected channels, monitored, and terminated when complete. Records of remote maintenance sessions must be kept."),
   ("PS-4  Maintenance Personnel","Maintenance personnel must be authorized; uncleared or unescorted personnel must be supervised by authorized staff. External maintenance providers must operate under agreement."),
   ("PS-5  Media & Equipment Sanitization","Equipment or media leaving the organization for off-site maintenance, disposal, or reuse must have CUI removed or be sanitized in accordance with the Media Protection Policy."),
   ("PS-6  Supervision & Verification","Maintenance activities affecting security functions must be verified afterward to confirm the system's security state is intact."),
 ],
 "procedures":[
   ("6.1  Performing Maintenance",["Authorize and schedule maintenance; inspect/scan tools and media before use.","Record what was done, by whom, and when."],"Maintenance authorizations and logs; tool/media scan records."),
   ("6.2  Remote Maintenance",["Authorize nonlocal maintenance; connect over an approved, encrypted, MFA-protected channel; monitor and terminate.","Sanitize equipment/media before off-site service or disposal."],"Remote-session authorizations and logs; sanitization records."),
 ],
 "compliance_focus":"by verifying maintenance is authorized and logged, tools/media are scanned, remote maintenance is controlled, and equipment is sanitized before leaving the organization.",
 "related":["Media Protection Policy — sanitization of media and equipment.","Access Control Policy — remote access and MFA for nonlocal maintenance.","Configuration Management Policy — verifying configuration after maintenance.","System Security Plan (SSP) — in-scope systems and maintenance arrangements."],
 "mapping_intro":"The table below maps each required control to the policy statement(s) that satisfy it and the evidence an auditor will seek. Control IDs are from NIST SP 800-171 Rev 3 (family 03.07); they are equally applicable to CMMC 2.0 Level 2 and ITSP.10.171 (CPCSC).",
 "mapping":[
   ["03.07.04  Maintenance Tools","PS-2 — control and scan tools/media","Tool/media inspection and scan records"],
   ["03.07.05  Nonlocal Maintenance","PS-3 — controlled remote maintenance","Remote-session authorizations and logs"],
   ["03.07.06  Maintenance Personnel","PS-4 — authorized/supervised personnel","Maintenance authorizations; vendor agreements"],
 ],
})

SPECS.append({
 "title":"Media Protection Policy","path":P+"Media_Protection_Policy.docx",
 "purpose":"This policy establishes how [Organization Name] protects, handles, stores, transports, and sanitizes digital and physical media that contain Controlled Unclassified Information (CUI). Media — from hard drives and USB sticks to printed documents and backups — is easily lost, stolen, or improperly discarded. This policy ensures CUI on media is protected at rest, in transport, and at end of life.",
 "scope":["All digital media (drives, SSDs, USB devices, optical media, backup media) and physical media (printed documents) containing CUI.","All storage, transport, reuse, and disposal of such media.","All personnel who handle media containing CUI."],
 "definitions":[("Media","Digital or physical material on which information is recorded (drives, USB, optical, paper, backups)."),("Sanitization","Rendering data unrecoverable through cryptographic erase, wiping, degaussing, or destruction."),("Removable Media","Portable storage that can be connected/disconnected (e.g., USB drives)."),("Media Marking","Labeling media to indicate the sensitivity (e.g., CUI) of its contents.")],
 "roles":[["[IT Manager / ISSO]","Own this policy; approve sanitization and disposal methods; authorize media use."],["[System Administrator]","Implement encryption and removable-media controls; perform or verify sanitization; manage backups."],["All Users","Handle, store, and transport CUI media per this policy; report lost or stolen media immediately."],["[Senior Leadership / CISO]","Approve this policy; accept residual risk for documented exceptions."]],
 "statements":[
   ("PS-1  Media Storage & Access","Media containing CUI must be stored securely (physically and logically) and access restricted to authorized personnel."),
   ("PS-2  Media Marking","Media containing CUI must be marked or labeled to indicate its sensitivity, unless the organization's environment makes marking unnecessary and this is documented."),
   ("PS-3  Encryption of CUI on Media","CUI at rest on portable and removable media must be protected with validated encryption (full-disk and/or file-level), so loss or theft does not result in disclosure."),
   ("PS-4  Removable Media Control","Use of removable media on CUI systems must be restricted by policy and technical control (e.g., block unapproved USB mass storage by default); only approved, encrypted devices may be used, and their use logged."),
   ("PS-5  Media Transport","Media containing CUI transported outside controlled areas must be protected (encrypted and/or in approved containers), and transport activities tracked."),
   ("PS-6  Media Sanitization & Disposal","Media containing CUI must be sanitized using an approved method (cryptographic erase, wipe, degauss, or destruction) before disposal, release, or reuse, with records/certificates retained."),
   ("PS-7  Backup Protection","Backups containing CUI must be protected with cryptographic protection consistent with the CUI they hold, and access to backups controlled."),
 ],
 "procedures":[
   ("6.1  Handling & Control",["Mark and securely store CUI media; restrict access.","Enforce removable-media controls; allow only approved encrypted devices."],"Media inventory/marking; removable-media policy config; device approval records."),
   ("6.2  Transport, Sanitization & Backup",["Encrypt and track media in transport.","Sanitize media before disposal/reuse and retain certificates; protect backups cryptographically."],"Transport logs; sanitization/destruction certificates; backup encryption configuration."),
 ],
 "compliance_focus":"by verifying CUI media is marked, encrypted, access-controlled, transported securely, sanitized before disposal, and that backups are cryptographically protected.",
 "related":["System Maintenance Policy — sanitization of equipment before off-site service.","System & Communications Protection Policy — encryption standards.","Physical Protection Policy — secure storage areas for media.","System Security Plan (SSP) — CUI categories and locations."],
 "mapping_intro":"The table below maps each required control to the policy statement(s) that satisfy it and the evidence an auditor will seek. Control IDs are from NIST SP 800-171 Rev 3 (family 03.08); they are equally applicable to CMMC 2.0 Level 2 and ITSP.10.171 (CPCSC).",
 "mapping":[
   ["03.08.01  Media Storage","PS-1 — secure storage","Storage controls; access records"],
   ["03.08.02  Media Access","PS-1 — restricted access","Access-control evidence"],
   ["03.08.03  Media Sanitization","PS-6 — sanitization/disposal","Sanitization/destruction certificates"],
   ["03.08.04  Media Marking","PS-2 — marking","Examples of marked media; marking procedure"],
   ["03.08.05  Media Transport","PS-5 — protected transport","Transport tracking; encryption evidence"],
   ["03.08.07  Media Use","PS-3, PS-4 — encryption; removable-media control","Removable-media config; encryption evidence"],
   ["03.08.09  System Backup – Cryptographic Protection","PS-7 — protected backups","Backup encryption configuration"],
 ],
})

SPECS.append({
 "title":"Personnel Security Policy","path":P+"Personnel_Security_Policy.docx",
 "purpose":"This policy establishes how [Organization Name] manages security risks associated with personnel who access systems and Controlled Unclassified Information (CUI), through screening, agreements, and disciplined onboarding, transfer, and termination processes. People are both the organization's greatest asset and a common source of risk; this policy ensures access is granted to trustworthy individuals and removed promptly when no longer warranted.",
 "scope":["All employees, contractors, and third parties who are granted access to in-scope systems or CUI.","All hiring, transfer, and termination activities that affect such access.","All agreements governing acceptable use and confidentiality."],
 "definitions":[("Screening","Pre-access vetting appropriate to the role and the sensitivity of the information accessed."),("Acceptable Use / Rules of Behavior","The documented rules users agree to follow when accessing systems and CUI."),("Termination","The end of an individual's employment or engagement."),("Transfer","A change in an individual's role that may change their access needs.")],
 "roles":[["[Human Resources]","Conduct screening; obtain signed agreements; notify IT of hires, transfers, and terminations within the defined timeframe."],["[IT Manager / ISSO]","Own this policy; ensure access is provisioned and removed in coordination with HR; maintain records."],["[Department Manager / Supervisor]","Define role access needs; confirm least privilege; initiate transfers/terminations."],["All Users","Comply with acceptable-use agreements; protect CUI; report concerns."],["[Senior Leadership / CISO]","Approve this policy; accept residual risk for documented exceptions."]],
 "statements":[
   ("PS-1  Personnel Screening","Individuals must be screened commensurate with the sensitivity of the information and systems they will access before access to CUI is granted, in accordance with applicable law and contract."),
   ("PS-2  Acceptable Use & Confidentiality Agreements","Before access is granted, individuals must sign acceptable-use / rules-of-behavior and confidentiality agreements covering the protection of CUI."),
   ("PS-3  Access on Hire","Access must be provisioned with least privilege only after screening and agreements are complete and security awareness training is initiated."),
   ("PS-4  Personnel Transfer","When an individual changes roles, their access must be reviewed and adjusted to match the new role within [organization-defined: 5 business days; recommended: 5 business days]."),
   ("PS-5  Personnel Termination","Upon termination, access must be revoked promptly (recommended: same day), credentials and authenticators disabled, and organizational property (including CUI) recovered. HR must notify IT within [1 business day]."),
   ("PS-6  Third-Party Personnel","Contractor and vendor personnel must meet equivalent screening and agreement requirements and be subject to the same access-removal discipline."),
 ],
 "procedures":[
   ("6.1  Onboarding",["Screen the individual; obtain signed agreements; provision least-privilege access; assign training.","Record completion before CUI access."],"Screening records; signed agreements; access request forms; training assignments."),
   ("6.2  Transfer & Termination",["On transfer, review and adjust access to the new role.","On termination, revoke access same-day, disable credentials, and recover property."],"Transfer/termination checklists; access-revocation records; property-return records."),
 ],
 "compliance_focus":"by verifying screening and agreements are completed before access, transfers adjust access appropriately, and terminations result in prompt access removal.",
 "related":["Access Control Policy — provisioning, least privilege, and access termination.","Identification & Authentication Policy — credential issuance and revocation.","Security Awareness & Training Policy — onboarding training.","System Security Plan (SSP) — roles and CUI access context."],
 "mapping_intro":"The table below maps each required control to the policy statement(s) that satisfy it and the evidence an auditor will seek. Control IDs are from NIST SP 800-171 Rev 3 (family 03.09); they are equally applicable to CMMC 2.0 Level 2 and ITSP.10.171 (CPCSC).",
 "mapping":[
   ["03.09.01  Personnel Screening","PS-1, PS-6 — screening before access","Screening records; vendor screening evidence"],
   ["03.09.02  Personnel Termination and Transfer","PS-4, PS-5 — transfer and termination actions","Termination/transfer checklists; access-revocation records"],
 ],
})

SPECS.append({
 "title":"Physical Protection Policy","path":P+"Physical_Protection_Policy.docx",
 "purpose":"This policy establishes how [Organization Name] controls physical access to facilities, equipment, and supporting infrastructure that house systems and Controlled Unclassified Information (CUI). Logical controls can be undermined if an attacker gains physical access. This policy ensures only authorized individuals can physically reach CUI systems, that access is monitored, and that off-site and transmission scenarios are addressed.",
 "scope":["All facilities, work areas, server/network rooms, and equipment that store or process CUI.","Visitors and third parties requiring physical access.","Alternate work sites and the protection of CUI transmission lines/equipment where applicable."],
 "definitions":[("Controlled Area","A space where access is limited to authorized individuals."),("Physical Access Authorization","Approved entitlement for an individual to enter a controlled area."),("Visitor","An individual without standing physical access authorization."),("Alternate Work Site","A location outside primary facilities (e.g., home office) where work is performed.")],
 "roles":[["[IT Manager / ISSO] / Facilities","Own this policy; authorize physical access; maintain access lists; oversee monitoring."],["[System Administrator]","Protect equipment in controlled areas; manage access to server/network rooms."],["All Users","Follow physical security rules; challenge/escort visitors; protect CUI at alternate work sites; report incidents."],["[Senior Leadership / CISO]","Approve this policy; accept residual risk for documented exceptions."]],
 "statements":[
   ("PS-1  Physical Access Authorizations","Physical access to controlled areas housing CUI systems must be limited to authorized individuals via an approved list, with credentials (badges/keys) issued and revoked through a controlled process."),
   ("PS-2  Physical Access Control","Entry to controlled areas must be enforced with locks, badge readers, or equivalent, and access lists reviewed [organization-defined: at least quarterly; recommended: quarterly]."),
   ("PS-3  Monitoring Physical Access","Physical access must be monitored (e.g., logs, alarms, video where appropriate) and unauthorized access investigated."),
   ("PS-4  Visitor Control","Visitors must be identified, authorized, logged, and escorted in controlled areas; visitor records must be retained."),
   ("PS-5  Alternate Work Sites","CUI accessed or stored at alternate work sites (e.g., remote work) must be protected with equivalent safeguards (locked storage, screen privacy, device encryption)."),
   ("PS-6  Protecting Transmission & Output Devices","Cabling, network equipment, and output devices (e.g., printers) handling CUI must be protected against unauthorized physical access and interception where applicable."),
 ],
 "procedures":[
   ("6.1  Access & Monitoring",["Maintain authorized-access lists; issue/revoke badges; review lists quarterly.","Monitor access; log and investigate anomalies."],"Access lists (dated); badge issuance/revocation; access logs; review sign-offs."),
   ("6.2  Visitors & Remote",["Log and escort visitors in controlled areas.","Provide alternate-work-site safeguards and acknowledgments."],"Visitor logs; remote-work security acknowledgments."),
 ],
 "compliance_focus":"by verifying access lists are current and reviewed, controlled areas are physically secured and monitored, visitors are escorted and logged, and alternate work sites are protected.",
 "related":["Access Control Policy — logical access complementing physical controls.","Media Protection Policy — physical storage of CUI media.","System & Communications Protection Policy — protection of transmission lines.","System Security Plan (SSP) — facility and CUI context."],
 "mapping_intro":"The table below maps each required control to the policy statement(s) that satisfy it and the evidence an auditor will seek. Control IDs are from NIST SP 800-171 Rev 3 (family 03.10); they are equally applicable to CMMC 2.0 Level 2 and ITSP.10.171 (CPCSC).",
 "mapping":[
   ["03.10.01  Physical Access Authorizations","PS-1 — authorized-access list","Access lists; badge issuance records"],
   ["03.10.02  Monitoring Physical Access","PS-3 — monitoring","Access logs; alarm/video records"],
   ["03.10.06  Alternate Work Site","PS-5 — remote-site safeguards","Remote-work acknowledgments; safeguards"],
   ["03.10.07  Physical Access Control","PS-2, PS-4 — enforced entry; visitor control","Lock/badge config; visitor logs; list reviews"],
   ["03.10.08  Access Control for Transmission","PS-6 — protect cabling/equipment","Physical protection of cabling/output devices"],
 ],
})

SPECS.append({
 "title":"Risk Assessment Policy","path":P+"Risk_Assessment_Policy.docx",
 "purpose":"This policy establishes how [Organization Name] identifies, assesses, prioritizes, and responds to cybersecurity risks to its operations, assets, and individuals, including risks to Controlled Unclassified Information (CUI), on a recurring basis. Risk assessment focuses limited resources on the threats that matter most and drives remediation decisions. This policy ties together vulnerability management and risk-based decision-making.",
 "scope":["All systems, processes, and third-party relationships that affect the confidentiality, integrity, or availability of CUI.","Recurring and event-driven risk assessments and vulnerability scanning.","Risk-response and remediation decisions."],
 "definitions":[("Risk","The likelihood and impact of a threat exploiting a vulnerability."),("Risk Assessment","A structured analysis of threats, vulnerabilities, likelihood, and impact."),("Vulnerability","A weakness that could be exploited to compromise a system."),("Risk Response","The decision to mitigate, transfer, avoid, or accept a risk.")],
 "roles":[["[IT Manager / ISSO]","Own this policy; conduct/oversee risk assessments and scanning; prioritize remediation; report risk to leadership."],["[System Administrator]","Run vulnerability scans; remediate findings; provide system information for assessments."],["[Senior Leadership / CISO]","Approve this policy; accept or direct response to residual risk; provide resources."],["All Users","Report risks and weaknesses they observe."]],
 "statements":[
   ("PS-1  Recurring Risk Assessment","[Organization Name] must perform a documented risk assessment of systems handling CUI [organization-defined: at least annually and upon significant change; recommended: annually], recording threats, vulnerabilities, likelihood, and impact."),
   ("PS-2  Vulnerability Monitoring & Scanning","Systems must be scanned for vulnerabilities on a defined schedule and after significant changes; results must be tracked to closure with timelines based on severity."),
   ("PS-3  Risk Prioritization","Identified risks and vulnerabilities must be prioritized by risk (impact × likelihood, considering control effectiveness) to focus remediation."),
   ("PS-4  Risk Response & Remediation","For each significant risk, the organization must select and document a response (mitigate, transfer, avoid, or accept) with owners and timelines; accepted risks must be approved at an appropriate level."),
   ("PS-5  Threat & Vulnerability Inputs","Risk assessments must consider current threat information, vendor advisories, and the system component inventory so that newly disclosed vulnerabilities are evaluated promptly."),
   ("PS-6  Linkage to POA&M","Remediation items and accepted risks affecting CUI must be reflected in the Plan of Action and Milestones (POA&M)."),
 ],
 "procedures":[
   ("6.1  Assessment & Scanning",["Conduct the periodic risk assessment; document threats/likelihood/impact.","Scan on schedule and after changes; track findings with SLAs by severity."],"Risk assessment report (dated); scan reports; vulnerability tracker."),
   ("6.2  Response",["Prioritize and assign remediation; document risk-response decisions and approvals.","Reflect items in the POA&M."],"Remediation tickets; risk-acceptance approvals; POA&M."),
 ],
 "compliance_focus":"by verifying risk assessments are current, vulnerability scanning occurs on schedule, findings are tracked to closure by severity, and risk responses are documented.",
 "related":["Security Assessment & Continuous Monitoring Policy — control assessment and POA&M.","System & Information Integrity Policy — flaw remediation timelines.","Configuration Management Policy — component inventory feeding scanning.","Supply Chain Risk Management Policy — supplier risk."],
 "mapping_intro":"The table below maps each required control to the policy statement(s) that satisfy it and the evidence an auditor will seek. Control IDs are from NIST SP 800-171 Rev 3 (family 03.11); they are equally applicable to CMMC 2.0 Level 2 and ITSP.10.171 (CPCSC).",
 "mapping":[
   ["03.11.01  Risk Assessment","PS-1, PS-3 — periodic, prioritized assessment","Risk assessment report (dated)"],
   ["03.11.02  Vulnerability Monitoring and Scanning","PS-2, PS-5 — scanning and threat inputs","Scan reports; vulnerability tracker"],
   ["03.11.04  Risk Response","PS-4, PS-6 — documented response; POA&M","Risk-response decisions; POA&M"],
 ],
})

for s in SPECS:
    B.build(s)
    print("  built", s["path"].split("/")[-1])
print(f"batch1: {len(SPECS)} policies")
