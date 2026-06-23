import sys; sys.path.insert(0,'tools')
import policy_builder as B
P="policy_library/"
SPECS=[]

SPECS.append({
 "title":"Security Assessment & Continuous Monitoring Policy","path":P+"Security_Assessment_Continuous_Monitoring_Policy.docx",
 "purpose":"This policy establishes how [Organization Name] assesses the effectiveness of its security controls, manages identified deficiencies through a Plan of Action and Milestones (POA&M), and continuously monitors its security posture for systems that process, store, or transmit Controlled Unclassified Information (CUI). Periodic assessment plus ongoing monitoring ensures controls remain effective over time and that gaps are tracked to closure.",
 "scope":["All security controls protecting in-scope systems and CUI.","Periodic control assessments, continuous monitoring activities, and the POA&M.","Information exchanges with external systems/partners where applicable."],
 "definitions":[("Security Assessment","An evaluation of whether controls are implemented correctly and operating as intended."),("POA&M","A documented plan that tracks deficiencies, remediation actions, owners, and milestones."),("Continuous Monitoring","Ongoing awareness of security state through metrics, scans, log review, and control checks."),("Information Exchange","Sharing information with an external system, governed by agreements.")],
 "roles":[["[IT Manager / ISSO]","Own this policy; plan and perform assessments; maintain the POA&M; run continuous monitoring; report to leadership."],["[System Administrator]","Provide evidence; remediate POA&M items; support monitoring tooling."],["[Senior Leadership / CISO]","Approve this policy; review posture and POA&M; accept residual risk."],["All Users","Support assessments by providing accurate information."]],
 "statements":[
   ("PS-1  Periodic Control Assessment","[Organization Name] must assess the security controls protecting CUI [organization-defined: at least annually and upon significant change; recommended: annually] to determine whether they are implemented correctly and operating effectively."),
   ("PS-2  Plan of Action & Milestones (POA&M)","Deficiencies identified through assessments, scans, or monitoring must be recorded in a POA&M with owners, planned actions, and milestone dates, and tracked to closure."),
   ("PS-3  Continuous Monitoring","The organization must continuously monitor its security posture using a defined set of metrics and activities (e.g., vulnerability scans, log/alert review, configuration compliance, control checks) at defined frequencies."),
   ("PS-4  Assessment Independence & Evidence","Assessments must be supported by objective evidence; where practical, assessors should be independent of the control they assess."),
   ("PS-5  Reporting","Assessment results, POA&M status, and monitoring metrics must be reported to leadership on a defined cadence so risk decisions are informed."),
   ("PS-6  Information Exchange","Where in-scope systems exchange information with external systems, the exchange must be governed by agreements that define security responsibilities and requirements."),
 ],
 "procedures":[
   ("6.1  Assess & Track",["Plan and perform the periodic assessment with evidence.","Log deficiencies in the POA&M; assign owners and milestones; track to closure."],"Assessment plan and results; POA&M (dated, updated)."),
   ("6.2  Monitor & Report",["Run continuous-monitoring activities at defined frequencies.","Report posture, POA&M status, and metrics to leadership."],"Monitoring metrics/dashboards; scan and review records; leadership reports."),
 ],
 "compliance_focus":"by verifying controls are assessed on schedule, deficiencies are tracked in the POA&M to closure, continuous-monitoring activities occur, and results are reported.",
 "related":["Risk Assessment Policy — risk inputs and vulnerability scanning.","Audit & Accountability Policy — log review feeding monitoring.","Configuration Management Policy — configuration compliance checks.","System Security Plan (SSP) — control implementation baseline."],
 "mapping_intro":"The table below maps each required control to the policy statement(s) that satisfy it and the evidence an auditor will seek. Control IDs are from NIST SP 800-171 Rev 3 (family 03.12); they are equally applicable to CMMC 2.0 Level 2 and ITSP.10.171 (CPCSC).",
 "mapping":[
   ["03.12.01  Security Assessment","PS-1, PS-4 — periodic assessment with evidence","Assessment plan and results"],
   ["03.12.02  Plan of Action and Milestones","PS-2 — POA&M","POA&M (dated, tracked)"],
   ["03.12.03  Continuous Monitoring","PS-3, PS-5 — monitoring and reporting","Monitoring metrics; leadership reports"],
   ["03.12.05  Information Exchange","PS-6 — exchange agreements","Interconnection/data-sharing agreements"],
 ],
})

SPECS.append({
 "title":"System & Communications Protection Policy","path":P+"System_Communications_Protection_Policy.docx",
 "purpose":"This policy establishes how [Organization Name] protects information in transit and at rest and how it segments and defends its networks for systems that process, store, or transmit Controlled Unclassified Information (CUI). Network and cryptographic protections prevent interception, tampering, and lateral movement. This policy defines boundary defense, encryption, key management, and related communications safeguards.",
 "scope":["All networks, boundaries, and communications carrying CUI.","All cryptographic mechanisms protecting CUI in transit and at rest.","All systems and services that transmit, process, or store CUI."],
 "definitions":[("Boundary Protection","Controls (e.g., firewalls) that monitor and control communications at external and key internal boundaries."),("Encryption in Transit","Protecting data as it moves across networks (e.g., TLS, VPN)."),("Encryption at Rest","Protecting stored data (e.g., full-disk, database, file-level encryption)."),("Cryptographic Key Management","Generating, distributing, storing, rotating, and destroying keys securely."),("Deny by Default","Blocking all communications except those explicitly permitted.")],
 "roles":[["[IT Manager / ISSO]","Own this policy; approve network architecture and cryptographic standards; oversee boundary defense."],["[System Administrator]","Implement firewalls, segmentation, encryption, and key management; monitor boundary devices."],["All Users","Use approved, encrypted channels; do not bypass network controls; report anomalies."],["[Senior Leadership / CISO]","Approve this policy; accept residual risk for documented exceptions."]],
 "statements":[
   ("PS-1  Boundary Protection","Communications at external boundaries and key internal boundaries must be monitored and controlled using managed interfaces (e.g., firewalls), with deny-by-default rules and centralized monitoring."),
   ("PS-2  Network Segmentation & Deny-by-Default","CUI systems must be placed in protected segments; network communications must be deny-by-default and allow only explicitly approved flows."),
   ("PS-3  Encryption in Transit","All transmission of CUI must use validated encryption (TLS 1.2+ or equivalent / approved VPN). Legacy protocols and weak ciphers must be disabled."),
   ("PS-4  Encryption at Rest","CUI at rest must be protected with validated encryption on servers, endpoints, databases, and portable devices."),
   ("PS-5  Cryptographic Protection (FIPS)","Cryptography used to protect CUI must use validated (e.g., FIPS-validated) cryptographic modules, and where they are applied must be documented."),
   ("PS-6  Key Management","Cryptographic keys must be established and managed securely (generation, distribution, storage, rotation, and destruction), with access restricted."),
   ("PS-7  Information in Shared Resources","Systems must prevent unauthorized or unintended information transfer via shared system resources (e.g., memory, storage reuse)."),
   ("PS-8  Network Disconnect & Session Authenticity","Network sessions must be terminated after a defined period of inactivity or at session end, and session authenticity protected (e.g., against hijacking)."),
   ("PS-9  Collaborative Devices & Mobile Code","Collaborative computing devices (e.g., cameras, microphones) must indicate active use and be controllable; mobile code must be restricted to approved, controlled use."),
 ],
 "procedures":[
   ("6.1  Network Defense",["Enforce deny-by-default at boundaries; segment CUI; monitor boundary devices centrally.","Terminate idle sessions; protect session authenticity."],"Firewall rules; segmentation diagrams; boundary-device logs; session-timeout configuration."),
   ("6.2  Cryptography",["Enforce TLS 1.2+/approved VPN; encrypt CUI at rest with validated modules.","Manage keys through their lifecycle with restricted access."],"TLS/VPN configuration; encryption-at-rest evidence; FIPS module list; key-management procedures."),
 ],
 "compliance_focus":"by verifying boundary defense and segmentation are enforced, CUI is encrypted in transit and at rest with validated cryptography, and keys are managed securely.",
 "related":["Access Control Policy — remote access and wireless controls.","Media Protection Policy — encryption of CUI on media.","Configuration Management Policy — hardened network device baselines.","System Security Plan (SSP) — network architecture and CUI flows."],
 "mapping_intro":"The table below maps each required control to the policy statement(s) that satisfy it and the evidence an auditor will seek. Control IDs are from NIST SP 800-171 Rev 3 (family 03.13); they are equally applicable to CMMC 2.0 Level 2 and ITSP.10.171 (CPCSC).",
 "mapping":[
   ["03.13.01  Boundary Protection","PS-1 — managed boundaries","Firewall rules; boundary monitoring"],
   ["03.13.04  Information in Shared System Resources","PS-7 — prevent shared-resource leakage","Configuration preventing resource reuse leakage"],
   ["03.13.06  Network Communications – Deny by Default","PS-2 — deny-by-default flows","Firewall deny-by-default rule sets"],
   ["03.13.08  Transmission and Storage Confidentiality","PS-3, PS-4 — encryption in transit and at rest","TLS/VPN and at-rest encryption evidence"],
   ["03.13.09  Network Disconnect","PS-8 — session termination","Idle-session disconnect configuration"],
   ["03.13.10  Cryptographic Key Establishment and Management","PS-6 — key management","Key-management procedures and evidence"],
   ["03.13.11  Cryptographic Protection","PS-5 — validated cryptography","FIPS-validated module list; usage map"],
   ["03.13.12  Collaborative Computing Devices and Applications","PS-9 — collaborative-device control","Camera/mic indicator and control config"],
   ["03.13.13  Mobile Code","PS-9 — mobile-code control","Mobile-code restriction configuration"],
   ["03.13.15  Session Authenticity","PS-8 — session authenticity","Session-protection configuration"],
 ],
})

SPECS.append({
 "title":"System & Information Integrity Policy","path":P+"System_Information_Integrity_Policy.docx",
 "purpose":"This policy establishes how [Organization Name] identifies, reports, and corrects system flaws, and protects systems from malicious code and emerging threats, for environments that process, store, or transmit Controlled Unclassified Information (CUI). Timely patching, anti-malware, threat-advisory awareness, and system monitoring are core defenses against compromise. This policy defines the timelines and tools that keep systems trustworthy.",
 "scope":["All in-scope systems, endpoints, servers, and applications.","Flaw remediation (patching), malicious-code protection, security advisories, and system monitoring.","Information that must be managed and retained for integrity."],
 "definitions":[("Flaw Remediation","Identifying and fixing security defects, typically through patching."),("Malicious Code","Software designed to cause harm (viruses, ransomware, trojans)."),("EDR (Endpoint Detection and Response)","Software that detects, investigates, and responds to threats on endpoints."),("Security Advisory","Vendor or authority notification of a vulnerability or threat requiring action.")],
 "roles":[["[IT Manager / ISSO]","Own this policy; set patch SLAs; ensure anti-malware and monitoring are deployed; track advisories."],["[System Administrator]","Apply patches within SLA; manage EDR/anti-malware; act on advisories; tune monitoring."],["All Users","Keep devices updated; do not disable security tools; report suspicious activity."],["[Senior Leadership / CISO]","Approve this policy; fund tooling; accept residual risk for documented exceptions."]],
 "statements":[
   ("PS-1  Flaw Remediation & Patch SLAs","Security-relevant flaws must be identified and remediated within defined timeframes based on severity (e.g., [organization-defined: critical within 15 days, high within 30 days; recommended per CISA/SLA]). Patch compliance must be measured and automated where possible."),
   ("PS-2  Malicious Code Protection","Modern endpoint protection (EDR/anti-malware) must run on all endpoints and servers, with central management, automatic updates, and alerting. Detected malicious code must be handled under the Incident Response Policy."),
   ("PS-3  Security Alerts & Advisories","The organization must monitor authoritative security alerts and advisories (e.g., vendor, CISA) and take timely action on those affecting its systems."),
   ("PS-4  System Monitoring","Systems and the network must be monitored for attacks and indicators of compromise (e.g., IDS/IPS, EDR telemetry), with alerts routed to a monitored queue and integrated with incident response."),
   ("PS-5  Information Management & Retention","Information within systems must be managed and retained in accordance with requirements so its integrity and availability are preserved for as long as needed."),
   ("PS-6  Integrity Verification","Where feasible, integrity-verification mechanisms must detect unauthorized changes to software, firmware, and information."),
 ],
 "procedures":[
   ("6.1  Patch & Protect",["Identify flaws; apply patches within severity-based SLAs; measure compliance.","Deploy and centrally manage EDR/anti-malware with auto-updates and alerting."],"Patch compliance reports; EDR console/coverage evidence; malware-handling records."),
   ("6.2  Monitor & Advise",["Monitor advisories and act on relevant ones.","Monitor systems for attack indicators; route alerts to incident response."],"Advisory-tracking records; monitoring/alert configuration; alert tickets."),
 ],
 "compliance_focus":"by verifying patches are applied within SLA, anti-malware/EDR is deployed and current, advisories are acted upon, and systems are monitored with alerts routed to response.",
 "related":["Incident Response Policy & Plan — handling detected threats.","Risk Assessment Policy — vulnerability scanning and prioritization.","Audit & Accountability Policy — logs feeding monitoring.","Configuration Management Policy — baselines and patch deployment."],
 "mapping_intro":"The table below maps each required control to the policy statement(s) that satisfy it and the evidence an auditor will seek. Control IDs are from NIST SP 800-171 Rev 3 (family 03.14); they are equally applicable to CMMC 2.0 Level 2 and ITSP.10.171 (CPCSC).",
 "mapping":[
   ["03.14.01  Flaw Remediation","PS-1 — patch SLAs","Patch compliance reports"],
   ["03.14.02  Malicious Code Protection","PS-2 — EDR/anti-malware","EDR coverage; update status; alerts"],
   ["03.14.03  Security Alerts, Advisories, and Directives","PS-3 — advisory monitoring/action","Advisory-tracking records"],
   ["03.14.06  System Monitoring","PS-4, PS-6 — monitoring; integrity checks","Monitoring/alert config; integrity-verification evidence"],
   ["03.14.08  Information Management and Retention","PS-5 — manage and retain information","Retention configuration/records"],
 ],
})

SPECS.append({
 "title":"Security Awareness & Training Policy","path":P+"Security_Awareness_Training_Policy.docx",
 "owner":"[IT Manager / ISSO]",
 "purpose":"This policy establishes how [Organization Name] ensures personnel receive security awareness and role-based training appropriate to their duties, so they can recognize and respond to threats and properly protect Controlled Unclassified Information (CUI). People are a primary line of defense; informed staff prevent and report incidents. This policy defines awareness training, role-based training, and tracking.",
 "scope":["All employees, contractors, and third parties with access to in-scope systems or CUI.","Awareness training at onboarding and recurring intervals, plus role-based training.","Tracking of training completion."],
 "definitions":[("Security Awareness Training","General training that helps all users recognize and avoid common threats (e.g., phishing)."),("Role-Based Training","Training tailored to the security responsibilities of a specific role (e.g., admins, developers)."),("Phishing Simulation","A controlled exercise that tests users' ability to recognize phishing.")],
 "roles":[["[IT Manager / ISSO]","Own this policy; define training content and cadence; track completion; report metrics."],["[Human Resources]","Assign training at onboarding; support tracking and follow-up."],["[Department Manager / Supervisor]","Ensure their team completes required training."],["All Users","Complete assigned training; apply it; report suspected threats."],["[Senior Leadership / CISO]","Approve this policy; reinforce a security culture."]],
 "statements":[
   ("PS-1  Security Awareness Training","All users must complete security awareness training at onboarding and at least [organization-defined: annually; recommended: annually], including recognizing phishing, social engineering, and proper CUI handling."),
   ("PS-2  Ongoing Awareness & Phishing Simulation","The organization must reinforce awareness through periodic communications and phishing simulations, using results to target additional training."),
   ("PS-3  Role-Based Training","Personnel with significant security responsibilities (e.g., administrators, developers, incident responders, those handling CUI) must receive role-based training appropriate to their duties before or shortly after assuming the role and periodically thereafter."),
   ("PS-4  Training on Policies & CUI Handling","Training must cover the organization's security policies, acceptable use, and the specific requirements for handling CUI."),
   ("PS-5  Completion Tracking","Training completion must be tracked, and non-completion followed up; records must be retained as evidence."),
 ],
 "procedures":[
   ("6.1  Deliver & Track",["Assign awareness training at onboarding and annually; deliver role-based training to relevant staff.","Run phishing simulations; track completion and follow up on gaps."],"Training assignments and completion records; phishing-simulation results; role-based training records."),
 ],
 "compliance_focus":"by verifying awareness training is completed at onboarding and annually, role-based training is delivered, and completion is tracked.",
 "related":["Personnel Security Policy — onboarding that triggers training.","Access Control Policy — training completed before CUI access.","Incident Response Policy & Plan — how to report incidents.","System Security Plan (SSP) — roles requiring role-based training."],
 "mapping_intro":"The table below maps each required control to the policy statement(s) that satisfy it and the evidence an auditor will seek. Control IDs are from NIST SP 800-171 Rev 3 (family 03.02); they are equally applicable to CMMC 2.0 Level 2 and ITSP.10.171 (CPCSC).",
 "mapping":[
   ["03.02.01  Literacy Training and Awareness","PS-1, PS-2, PS-4 — awareness; phishing; policy/CUI handling","Awareness training records; phishing-simulation results"],
   ["03.02.02  Role-Based Training","PS-3, PS-5 — role-based training; tracking","Role-based training records; completion tracking"],
 ],
})

SPECS.append({
 "title":"Information Security Program Plan (SSP)","path":P+"Information_Security_Program_Plan_SSP.docx",
 "purpose":"This document establishes [Organization Name]'s information security program and serves as the foundation for its System Security Plan (SSP). It describes the system boundary, the Controlled Unclassified Information (CUI) environment, how security controls are implemented, and how the program is planned, resourced, and governed. The SSP is the authoritative reference auditors use to understand the environment and verify control implementation.",
 "scope":["The defined system boundary that processes, stores, or transmits CUI, including components, data flows, and connections.","The security program governance, roles, and planning that support control implementation.","All personnel and third parties operating within the boundary."],
 "definitions":[("System Security Plan (SSP)","The authoritative document describing the system, its boundary, and how each security control is implemented."),("System Boundary","The set of components that make up the system and its authorization scope."),("Rules of Behavior","The documented rules users agree to follow when accessing the system."),("Security Program","The organized set of policies, roles, resources, and activities that protect information.")],
 "roles":[["[IT Manager / ISSO]","Own the security program and SSP; keep the boundary and control implementation current; coordinate assessments."],["[System Administrator]","Maintain the component inventory and data-flow documentation; implement controls described in the SSP."],["[Senior Leadership / CISO]","Approve the program and SSP; provide resources; accept residual risk."],["All Users","Acknowledge and follow the rules of behavior."]],
 "statements":[
   ("PS-1  Policies & Procedures","[Organization Name] must establish, maintain, and disseminate the security policies and procedures required to protect CUI, and review them at least [annually]."),
   ("PS-2  System Security Plan","A System Security Plan must be developed and maintained that describes the system boundary, environment, CUI categories, interconnections, and how each required control is implemented; it must be reviewed and updated on a defined cadence and after significant change."),
   ("PS-3  Boundary & Inventory","The system boundary, component inventory, and data flows for CUI must be documented and kept current."),
   ("PS-4  Rules of Behavior","Rules of behavior for users (including for CUI handling) must be documented, acknowledged before access, and re-acknowledged periodically."),
   ("PS-5  Program Governance & Resourcing","Security roles must be assigned, and the program adequately resourced; the SSP must reference the supporting policies (Access Control, Audit, etc.)."),
   ("PS-6  Plan of Action & Milestones","Gaps in control implementation must be tracked in a POA&M associated with the SSP."),
 ],
 "procedures":[
   ("6.1  Maintain the SSP",["Document the boundary, inventory, CUI categories, interconnections, and control implementation.","Review/update on cadence and after significant change."],"Current SSP (dated); boundary/inventory/data-flow documentation."),
   ("6.2  Governance",["Maintain and disseminate policies; assign security roles.","Obtain rules-of-behavior acknowledgments; track gaps in the POA&M."],"Policy set (dated); role assignments; signed rules of behavior; POA&M."),
 ],
 "compliance_focus":"by verifying the SSP is current and complete, policies are maintained and disseminated, rules of behavior are acknowledged, and gaps are tracked in the POA&M.",
 "related":["All policies in this set — referenced by the SSP for control implementation.","Security Assessment & Continuous Monitoring Policy — assessment and POA&M.","Risk Assessment Policy — risk inputs to the program.","Configuration Management Policy — component inventory and boundary."],
 "mapping_intro":"The table below maps each required control to the policy statement(s) that satisfy it and the evidence an auditor will seek. Control IDs are from NIST SP 800-171 Rev 3 (family 03.15 — Planning); they are equally applicable to CMMC 2.0 Level 2 and ITSP.10.171 (CPCSC).",
 "mapping":[
   ["03.15.01  Policy and Procedures","PS-1, PS-5 — policies maintained and disseminated","Policy set (dated); dissemination evidence"],
   ["03.15.02  System Security Plan","PS-2, PS-3, PS-6 — SSP, boundary, POA&M","Current SSP; boundary/inventory; POA&M"],
   ["03.15.03  Rules of Behavior","PS-4 — documented, acknowledged rules","Signed rules of behavior"],
 ],
})

SPECS.append({
 "title":"System & Services Acquisition Policy","path":P+"System_Services_Acquisition_Policy.docx",
 "purpose":"This policy establishes how [Organization Name] builds security into the acquisition and development of systems, components, and services that will process, store, or transmit Controlled Unclassified Information (CUI). Security requirements defined before acquisition are far cheaper and more effective than retrofits. This policy ensures security engineering principles are applied, unsupported components are avoided, and external service providers meet CUI requirements.",
 "scope":["Acquisition and development of systems, components, software, and services that will handle CUI.","External system services and providers operating on the organization's behalf.","Decommissioning of unsupported components."],
 "definitions":[("Security Engineering Principles","Design practices (e.g., least privilege, defense in depth, secure defaults) applied when building systems."),("Unsupported Component","Hardware/software no longer receiving security updates from its vendor."),("External System Service","A service provided by an external provider (e.g., a SaaS or managed service) used by the organization.")],
 "roles":[["[IT Manager / ISSO]","Own this policy; define security requirements for acquisitions; approve external services; track component support status."],["[System Administrator] / Developers","Apply security engineering principles; configure acquired components securely; replace unsupported components."],["[Procurement]","Include security requirements in contracts; obtain provider attestations."],["[Senior Leadership / CISO]","Approve this policy; accept residual risk for documented exceptions."]],
 "statements":[
   ("PS-1  Security Requirements in Acquisition","Security requirements (including CUI protection requirements such as the applicable NIST 800-171 / CMMC controls) must be defined and included in acquisitions and contracts for systems, components, and services that will handle CUI."),
   ("PS-2  Security Engineering Principles","Security engineering principles (e.g., least privilege, defense in depth, secure defaults, minimization) must be applied when designing, developing, and configuring systems."),
   ("PS-3  Unsupported Components","Unsupported system components must be identified and replaced; where continued use is unavoidable, documented compensating controls and a remediation plan must be in place."),
   ("PS-4  External System Services","Providers of external system services that store, process, or transmit CUI must meet equivalent security requirements; responsibilities must be defined in agreements, and provider compliance verified (e.g., attestations, certifications)."),
   ("PS-5  Acceptance & Verification","Before systems or services are placed into operation, their security configuration and controls must be verified against the defined requirements."),
 ],
 "procedures":[
   ("6.1  Acquire Securely",["Define and include security/CUI requirements in acquisitions and contracts.","Apply security engineering principles in design and configuration; verify before go-live."],"Acquisition/contract security requirements; design/configuration evidence; acceptance checklists."),
   ("6.2  Providers & Lifecycle",["Assess and contract external service providers handling CUI; verify compliance.","Identify and replace unsupported components; document compensating controls where needed."],"Provider agreements and attestations; unsupported-component inventory and remediation plans."),
 ],
 "compliance_focus":"by verifying security requirements are included in acquisitions, security engineering principles are applied, unsupported components are managed, and external CUI service providers meet requirements.",
 "related":["Supply Chain Risk Management Policy — supplier and supply-chain risk.","Configuration Management Policy — secure configuration of acquired components.","Risk Assessment Policy — assessing acquisition and provider risk.","System Security Plan (SSP) — boundary including external services."],
 "mapping_intro":"The table below maps each required control to the policy statement(s) that satisfy it and the evidence an auditor will seek. Control IDs are from NIST SP 800-171 Rev 3 (family 03.16); they are equally applicable to CMMC 2.0 Level 2 and ITSP.10.171 (CPCSC).",
 "mapping":[
   ["03.16.01  Security Engineering Principles","PS-2, PS-5 — engineering principles; verification","Design/config evidence; acceptance checklists"],
   ["03.16.02  Unsupported System Components","PS-3 — manage/replace unsupported components","Unsupported-component inventory; remediation plans"],
   ["03.16.03  External System Services","PS-1, PS-4 — requirements and provider compliance","Contract requirements; provider attestations"],
 ],
})

SPECS.append({
 "title":"Supply Chain Risk Management Policy","path":P+"Supply_Chain_Risk_Management_Policy.docx",
 "purpose":"This policy establishes how [Organization Name] manages cybersecurity risk arising from its suppliers, products, and the broader supply chain for systems and services that handle Controlled Unclassified Information (CUI). Compromised or untrustworthy suppliers and components can undermine even strong internal controls. This policy defines supply-chain risk planning, supplier requirements, and acquisition practices.",
 "scope":["Suppliers, vendors, manufacturers, and service providers whose products or services affect CUI or in-scope systems.","Acquisition strategies, tools, and methods used to obtain those products and services.","Ongoing management of supply-chain relationships and requirements."],
 "definitions":[("Supply Chain","The network of suppliers, products, and services that contribute to the organization's systems."),("Supply Chain Risk","The risk that a supplier, product, or service introduces a vulnerability or compromise."),("Supplier Requirements","Security obligations imposed on suppliers (e.g., flow-down of CUI protection requirements)."),("Provenance","Knowledge of the origin and chain of custody of a product or component.")],
 "roles":[["[IT Manager / ISSO]","Own this policy; maintain the supply-chain risk plan; set supplier security requirements; assess supplier risk."],["[Procurement]","Apply approved acquisition strategies; flow down requirements into contracts; obtain attestations."],["[Senior Leadership / CISO]","Approve this policy; accept residual supply-chain risk."],["All Users","Use only approved suppliers/products; report supply-chain concerns."]],
 "statements":[
   ("PS-1  Supply Chain Risk Management Plan","[Organization Name] must develop and maintain a plan to manage supply-chain cybersecurity risk, identifying critical suppliers/components and the controls applied to manage their risk."),
   ("PS-2  Acquisition Strategies, Tools & Methods","The organization must use acquisition strategies, tools, and methods that reduce supply-chain risk (e.g., buying from trusted sources, requiring security attestations, verifying provenance where feasible)."),
   ("PS-3  Supplier Requirements & Flow-Down","Security and CUI protection requirements must be defined for suppliers handling CUI or supplying in-scope components, and flowed down through contracts; supplier compliance must be verified."),
   ("PS-4  Supplier Risk Assessment","Suppliers and products that affect CUI must be risk-assessed before engagement and periodically thereafter, and risk responses documented."),
   ("PS-5  Ongoing Monitoring","Supply-chain relationships must be monitored for changes in risk (e.g., supplier breaches, end-of-support), with action taken as needed."),
 ],
 "procedures":[
   ("6.1  Plan & Require",["Maintain the supply-chain risk plan; identify critical suppliers/components.","Define and flow down supplier security/CUI requirements; obtain attestations."],"Supply-chain risk plan; supplier requirements in contracts; supplier attestations."),
   ("6.2  Assess & Monitor",["Risk-assess suppliers/products before engagement and periodically.","Monitor for supplier risk changes; respond as needed."],"Supplier risk assessments; monitoring records; risk-response decisions."),
 ],
 "compliance_focus":"by verifying a supply-chain risk plan exists, supplier security/CUI requirements are flowed down and verified, and supplier risk is assessed and monitored.",
 "related":["System & Services Acquisition Policy — acquiring systems and services securely.","Risk Assessment Policy — supplier and product risk.","Configuration Management Policy — component inventory and provenance.","System Security Plan (SSP) — external services in the boundary."],
 "mapping_intro":"The table below maps each required control to the policy statement(s) that satisfy it and the evidence an auditor will seek. Control IDs are from NIST SP 800-171 Rev 3 (family 03.17); they are equally applicable to CMMC 2.0 Level 2 and ITSP.10.171 (CPCSC).",
 "mapping":[
   ["03.17.01  Supply Chain Risk Management Plan","PS-1 — SCRM plan","Supply-chain risk plan (dated)"],
   ["03.17.02  Acquisition Strategies, Tools, and Methods","PS-2 — risk-reducing acquisition","Acquisition strategy; trusted-source evidence"],
   ["03.17.03  Supply Chain Requirements and Processes","PS-3, PS-4, PS-5 — requirements, assessment, monitoring","Supplier requirements/attestations; risk assessments; monitoring records"],
 ],
})

SPECS.append({
 "title":"Information Security Policy","path":P+"Information_Security_Policy.docx",
 "purpose":"This is the overarching information security policy of [Organization Name]. It sets leadership's expectations for protecting the confidentiality, integrity, and availability of information — including Controlled Unclassified Information (CUI) — and establishes the framework of domain-specific policies, roles, and accountability that implement those expectations. All other security policies derive their authority from this document.",
 "scope":["All information and information systems owned or operated by [Organization Name], with particular focus on CUI.","All employees, contractors, and third parties who access organizational information or systems.","All locations and environments, including cloud, on-premises, and remote work."],
 "definitions":[("Information Security","Protecting information's confidentiality, integrity, and availability."),("Confidentiality","Ensuring information is accessible only to those authorized."),("Integrity","Ensuring information is accurate and not improperly altered."),("Availability","Ensuring information and systems are accessible when needed."),("CUI","Controlled Unclassified Information requiring safeguarding under law, regulation, or contract.")],
 "roles":[["[Senior Leadership / CISO]","Set the security direction; approve this and subordinate policies; provide resources; accept residual risk."],["[IT Manager / ISSO]","Own the security program; maintain subordinate policies; oversee implementation and reporting."],["[Department Managers / Supervisors]","Ensure their teams comply; support implementation in their areas."],["All Users","Protect information and CUI; follow all security policies; report incidents and concerns."]],
 "statements":[
   ("PS-1  Commitment to Information Security","[Organization Name] is committed to protecting the confidentiality, integrity, and availability of its information and that entrusted to it, and to meeting its legal, regulatory, and contractual obligations, including the protection of CUI."),
   ("PS-2  Policy Framework","A framework of domain-specific policies (Access Control, Audit & Accountability, Configuration Management, Identification & Authentication, Incident Response, Maintenance, Media Protection, Personnel Security, Physical Protection, Risk Assessment, Security Assessment & Continuous Monitoring, Security Awareness & Training, Supply Chain Risk Management, System & Communications Protection, System & Information Integrity, System & Services Acquisition, and the SSP) implements this policy; each must be maintained and followed."),
   ("PS-3  Roles & Accountability","Security roles and responsibilities must be assigned, and all personnel are accountable for complying with security policies."),
   ("PS-4  Risk-Based Approach","Security decisions must be risk-based, focusing resources on the greatest risks to information and CUI."),
   ("PS-5  Compliance & Continuous Improvement","The organization must monitor compliance, assess control effectiveness, and continuously improve its security posture."),
   ("PS-6  Policy Review","This policy and its subordinate policies must be reviewed at least [annually] and updated as the business, technology, or threat landscape changes."),
 ],
 "procedures":[
   ("6.1  Govern & Maintain",["Maintain and disseminate this policy and the subordinate policy set; assign security roles.","Review at least annually and after significant change."],"Approved policy set (dated); role assignments; review records."),
   ("6.2  Monitor & Improve",["Monitor compliance and control effectiveness; track gaps in the POA&M.","Apply improvements based on assessments, incidents, and changes."],"Compliance/assessment reports; POA&M; revision history."),
 ],
 "compliance_focus":"by verifying the policy framework is maintained and disseminated, roles are assigned, compliance is monitored, and policies are reviewed at least annually.",
 "related":["System Security Plan (SSP) — implementation reference for controls.","All domain-specific policies — subordinate to this policy.","Risk Assessment Policy — the risk basis for security decisions.","Security Assessment & Continuous Monitoring Policy — compliance and improvement."],
 "mapping_intro":"This overarching policy is implemented by the domain-specific policies and maps primarily to the planning controls. Control IDs are from NIST SP 800-171 Rev 3; they are equally applicable to CMMC 2.0 Level 2 and ITSP.10.171 (CPCSC).",
 "mapping":[
   ["03.15.01  Policy and Procedures","PS-1, PS-2, PS-6 — security policy framework; review","This policy and the subordinate policy set (dated)"],
   ["03.15.02  System Security Plan","PS-2, PS-4 — framework feeding the SSP","Reference to the SSP and program plan"],
   ["(All families 03.01–03.17)","PS-2 — implemented via subordinate policies","The corresponding domain policy for each family"],
 ],
})

for s in SPECS:
    B.build(s)
    print("  built", s["path"].split("/")[-1])
print(f"batch2: {len(SPECS)} policies")
