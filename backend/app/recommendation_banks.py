"""Curated pre-made remediation recommendations, keyed by control ref.

NIST SP 800-171r3 control refs (03.xx.xx). Each value is a list of
recommendations, each a dict: {title, text, title_fr, text_fr, effort, impact}.

  effort ∈ {low, medium, high}   - relative implementation lift
  impact ∈ {low, medium, high}   - security/compliance value of doing it

title_fr / text_fr carry the Canadian-French (Québécois) translation; the API
serves them when the request language is French and falls back to English.

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
         "title_fr": "Centraliser le cycle de vie des comptes dans votre fournisseur d'identité",
         "text_fr": "Regroupez la création, la modification et la désactivation des comptes dans un seul fournisseur d'identité (p. ex. Entra ID, Okta, Google Workspace) afin que tous les systèmes héritent d'une source de vérité unique. Reliez les événements d'arrivée, de mutation et de départ aux RH pour que les comptes soient désactivés dès le départ d'une personne.",
         "effort": "medium", "impact": "high"},
        {"title": "Schedule quarterly access recertification",
         "text": "Run a recurring access review where managers attest to who has access to each system. Document the review and remove anything no longer needed. Start with CUI-bearing systems.",
         "title_fr": "Planifier une recertification trimestrielle des accès",
         "text_fr": "Mettez en place une revue récurrente des accès où les gestionnaires attestent qui a accès à chaque système. Documentez la revue et retirez tout accès devenu inutile. Commencez par les systèmes contenant de l'information contrôlée (CUI).",
         "effort": "low", "impact": "high"},
    ],
    "03.01.02": [
        {"title": "Enforce access from a central policy, not per-host config",
         "text": "Replace per-system local permissions with group/role-based rules managed centrally so authorizations are applied consistently and revoked in one place.",
         "title_fr": "Appliquer les accès par une politique centrale plutôt que par configuration sur chaque hôte",
         "text_fr": "Remplacez les permissions locales propres à chaque système par des règles centralisées fondées sur les groupes ou les rôles, afin que les autorisations soient appliquées de façon uniforme et révoquées à un seul endroit.",
         "effort": "medium", "impact": "high"},
    ],
    "03.01.03": [
        {"title": "Segment the CUI environment and filter egress",
         "text": "Place CUI systems on a dedicated network segment/VLAN with deny-by-default firewall rules, and add egress filtering (and DLP where feasible) so CUI cannot flow to unapproved destinations.",
         "title_fr": "Segmenter l'environnement CUI et filtrer le trafic sortant",
         "text_fr": "Placez les systèmes contenant de l'information contrôlée (CUI) sur un segment réseau ou VLAN dédié avec des règles de pare-feu par refus par défaut, et ajoutez un filtrage du trafic sortant (et une prévention des pertes de données lorsque possible) pour empêcher la fuite des CUI vers des destinations non approuvées.",
         "effort": "high", "impact": "high"},
    ],
    "03.01.04": [
        {"title": "Document and enforce separation of duties",
         "text": "Map the conflicting duties for critical processes (e.g. request vs. approve, develop vs. deploy) and enforce them with role assignments; review for toxic combinations each quarter.",
         "title_fr": "Documenter et appliquer la séparation des tâches",
         "text_fr": "Cartographiez les tâches incompatibles des processus critiques (p. ex. demander c. approuver, développer c. déployer) et appliquez-les par l'attribution des rôles; révisez chaque trimestre les combinaisons à risque.",
         "effort": "medium", "impact": "medium"},
    ],
    "03.01.05": [
        {"title": "Right-size permissions to least privilege",
         "text": "Audit current entitlements, strip access beyond what each role needs, and adopt just-in-time elevation for occasional admin tasks. Recertify on a schedule.",
         "title_fr": "Ajuster les permissions au moindre privilège",
         "text_fr": "Vérifiez les droits actuels, retirez tout accès au-delà de ce dont chaque rôle a besoin et adoptez l'élévation juste-à-temps pour les tâches d'administration occasionnelles. Recertifiez selon un calendrier.",
         "effort": "medium", "impact": "high"},
    ],
    "03.01.06": [
        {"title": "Lock down and broker privileged accounts",
         "text": "Inventory all admin accounts, remove standing/shared admin where possible, require MFA, and move privileged access to just-in-time elevation with full session logging.",
         "title_fr": "Verrouiller et encadrer les comptes privilégiés",
         "text_fr": "Inventoriez tous les comptes d'administration, retirez autant que possible les accès administratifs permanents ou partagés, exigez l'authentification multifacteur (AMF) et faites passer les accès privilégiés à une élévation juste-à-temps avec journalisation complète des sessions.",
         "effort": "medium", "impact": "high"},
        {"title": "Separate admin identities from daily-use accounts",
         "text": "Give administrators a distinct privileged account used only for admin work, never for email or browsing. Low lift, immediate blast-radius reduction.",
         "title_fr": "Séparer les identités d'administration des comptes d'usage quotidien",
         "text_fr": "Donnez aux administrateurs un compte privilégié distinct, utilisé uniquement pour les tâches d'administration, jamais pour le courriel ou la navigation. Effort minime, réduction immédiate du rayon d'impact.",
         "effort": "low", "impact": "high"},
    ],
    "03.01.07": [
        {"title": "Log and alert on privileged function use",
         "text": "Restrict privileged functions to authorized roles and forward their use to your log pipeline with alerting on anomalous activity.",
         "title_fr": "Journaliser et alerter sur l'utilisation des fonctions privilégiées",
         "text_fr": "Restreignez les fonctions privilégiées aux rôles autorisés et acheminez leur utilisation vers votre pipeline de journalisation, avec des alertes sur les activités anormales.",
         "effort": "medium", "impact": "medium"},
    ],
    "03.01.08": [
        {"title": "Enforce account lockout / throttling everywhere",
         "text": "Configure lockout or rate-limiting on failed logons at the central identity provider so the policy applies uniformly, and alert on brute-force patterns.",
         "title_fr": "Appliquer le verrouillage et la limitation des tentatives partout",
         "text_fr": "Configurez le verrouillage des comptes ou la limitation du débit sur les échecs d'ouverture de session au niveau du fournisseur d'identité central, afin que la politique s'applique uniformément, et alertez sur les schémas de force brute.",
         "effort": "low", "impact": "medium"},
    ],
    "03.01.10": [
        {"title": "Push device-lock timeouts via policy",
         "text": "Deploy a managed policy (Intune/MDM/GPO) that locks endpoints after a short inactivity period across all devices, instead of relying on users.",
         "title_fr": "Déployer le verrouillage automatique des appareils par politique",
         "text_fr": "Déployez une politique gérée (Intune/MDM/GPO) qui verrouille les postes après une courte période d'inactivité sur tous les appareils, plutôt que de compter sur les utilisateurs.",
         "effort": "low", "impact": "medium"},
    ],
    "03.01.11": [
        {"title": "Set session timeouts on apps and remote access",
         "text": "Configure idle and absolute session timeouts on critical applications and VPN/remote sessions so sessions do not stay open indefinitely.",
         "title_fr": "Définir des délais d'expiration de session sur les applications et l'accès à distance",
         "text_fr": "Configurez des délais d'expiration de session, par inactivité et absolus, sur les applications critiques et les sessions VPN ou à distance, afin que les sessions ne restent pas ouvertes indéfiniment.",
         "effort": "low", "impact": "medium"},
    ],
    "03.01.12": [
        {"title": "Require MFA and monitoring on all remote access",
         "text": "Front all remote access with an MFA-protected, hardened gateway; disable split tunneling and forward logs centrally for monitoring.",
         "title_fr": "Exiger l'AMF et la surveillance sur tout accès à distance",
         "text_fr": "Faites passer tout accès à distance par une passerelle durcie protégée par authentification multifacteur (AMF); désactivez le tunnel partagé et acheminez les journaux de façon centralisée pour la surveillance.",
         "effort": "medium", "impact": "high"},
    ],
    "03.01.16": [
        {"title": "Move to enterprise wireless authentication",
         "text": "Adopt 802.1X / WPA-Enterprise for corporate wireless, separate guest traffic onto its own network, and enable rogue-AP detection.",
         "title_fr": "Adopter l'authentification sans fil d'entreprise",
         "text_fr": "Adoptez 802.1X / WPA-Entreprise pour le sans-fil corporatif, isolez le trafic invité sur son propre réseau et activez la détection des points d'accès non autorisés.",
         "effort": "medium", "impact": "medium"},
    ],
    "03.01.18": [
        {"title": "Enroll all mobile devices in MDM",
         "text": "Require MDM enrollment with encryption, screen lock, and remote-wipe before a device can reach corporate data; bring BYOD under at least app-level management.",
         "title_fr": "Inscrire tous les appareils mobiles à une solution MDM",
         "text_fr": "Exigez l'inscription à une solution de gestion des appareils mobiles (MDM) avec chiffrement, verrouillage d'écran et effacement à distance avant qu'un appareil puisse accéder aux données de l'entreprise; encadrez au moins au niveau applicatif les appareils personnels (PAP).",
         "effort": "medium", "impact": "high"},
    ],
    "03.01.20": [
        {"title": "Govern external systems and sanction alternatives",
         "text": "Publish an approved-services list, block known high-risk SaaS for CUI, and give staff sanctioned tools so shadow IT is unnecessary.",
         "title_fr": "Encadrer les systèmes externes et offrir des solutions approuvées",
         "text_fr": "Publiez une liste de services approuvés, bloquez les services infonuagiques à risque élevé pour les CUI et fournissez au personnel des outils approuvés afin de rendre l'informatique fantôme inutile.",
         "effort": "medium", "impact": "medium"},
    ],

    # ── 03.02 Awareness & Training ────────────────────────────────────
    "03.02.01": [
        {"title": "Stand up recurring security awareness training",
         "text": "Roll out role-based security awareness training at onboarding and at least annually, including phishing simulations, and track completion.",
         "title_fr": "Mettre en place une formation récurrente de sensibilisation à la sécurité",
         "text_fr": "Déployez une formation de sensibilisation à la sécurité adaptée aux rôles, à l'accueil et au moins une fois par année, incluant des simulations d'hameçonnage, et assurez le suivi des achèvements.",
         "effort": "low", "impact": "high"},
    ],
    "03.02.02": [
        {"title": "Add role-specific training for privileged staff",
         "text": "Supplement general awareness with targeted training for admins, developers, and anyone handling CUI on their specific responsibilities.",
         "title_fr": "Ajouter une formation propre aux rôles pour le personnel privilégié",
         "text_fr": "Complétez la sensibilisation générale par une formation ciblée pour les administrateurs, les développeurs et toute personne manipulant des CUI, sur leurs responsabilités précises.",
         "effort": "low", "impact": "medium"},
    ],

    # ── 03.03 Audit & Accountability ──────────────────────────────────
    "03.03.01": [
        {"title": "Centralize logs into a SIEM/log store",
         "text": "Forward security-relevant logs from endpoints, servers, identity, and network devices into a central, time-synced store with sufficient retention to support investigations.",
         "title_fr": "Centraliser les journaux dans un SIEM ou un dépôt de journaux",
         "text_fr": "Acheminez les journaux pertinents pour la sécurité des postes, serveurs, systèmes d'identité et équipements réseau vers un dépôt central, synchronisé dans le temps, avec une rétention suffisante pour soutenir les enquêtes.",
         "effort": "high", "impact": "high"},
    ],
    "03.03.03": [
        {"title": "Define and document what events you log",
         "text": "Agree the set of auditable events (logons, privilege use, config changes, CUI access) and review the list periodically so coverage stays current.",
         "title_fr": "Définir et documenter les événements à journaliser",
         "text_fr": "Convenez de l'ensemble des événements vérifiables (ouvertures de session, utilisation de privilèges, changements de configuration, accès aux CUI) et révisez la liste périodiquement pour que la couverture demeure à jour.",
         "effort": "low", "impact": "medium"},
    ],
    "03.03.05": [
        {"title": "Build alerting on top of your logs",
         "text": "Add correlation and alerting for high-risk patterns (impossible travel, mass deletes, privilege escalation) so log data is acted on, not just stored.",
         "title_fr": "Bâtir des alertes à partir de vos journaux",
         "text_fr": "Ajoutez de la corrélation et des alertes pour les schémas à risque élevé (déplacement impossible, suppressions massives, élévation de privilèges) afin que les données de journaux soient exploitées et non seulement stockées.",
         "effort": "medium", "impact": "high"},
    ],

    # ── 03.04 Configuration Management ────────────────────────────────
    "03.04.01": [
        {"title": "Establish and enforce secure baselines",
         "text": "Adopt hardened baseline configurations (e.g. CIS Benchmarks) for OSes and key apps, deploy them via MDM/GPO, and monitor for drift.",
         "title_fr": "Établir et appliquer des configurations de référence sécurisées",
         "text_fr": "Adoptez des configurations de référence durcies (p. ex. les balises CIS) pour les systèmes d'exploitation et les applications clés, déployez-les par MDM/GPO et surveillez les écarts.",
         "effort": "high", "impact": "high"},
    ],
    "03.04.02": [
        {"title": "Put configuration changes under change control",
         "text": "Require review/approval for changes to baseline configurations and keep a record of what changed, when, and by whom.",
         "title_fr": "Soumettre les changements de configuration à la gestion des changements",
         "text_fr": "Exigez une revue et une approbation pour les changements aux configurations de référence et conservez un registre de ce qui a changé, quand et par qui.",
         "effort": "medium", "impact": "medium"},
    ],
    "03.04.06": [
        {"title": "Apply least-functionality hardening",
         "text": "Disable unused ports, protocols, services, and software on systems, and document the approved functionality for each system role.",
         "title_fr": "Appliquer le durcissement par fonctionnalité minimale",
         "text_fr": "Désactivez les ports, protocoles, services et logiciels inutilisés sur les systèmes, et documentez les fonctionnalités approuvées pour chaque rôle de système.",
         "effort": "medium", "impact": "medium"},
    ],
    "03.04.08": [
        {"title": "Move to application allow-listing",
         "text": "Where feasible, deny-by-default for software execution and allow only approved applications, starting with CUI and high-value systems.",
         "title_fr": "Adopter une liste d'autorisation des applications",
         "text_fr": "Lorsque possible, appliquez le refus par défaut à l'exécution de logiciels et n'autorisez que les applications approuvées, en commençant par les CUI et les systèmes à grande valeur.",
         "effort": "high", "impact": "high"},
    ],

    # ── 03.05 Identification & Authentication ─────────────────────────
    "03.05.01": [
        {"title": "Ensure unique identification for every user",
         "text": "Eliminate shared/generic accounts so every action is attributable to an individual; where a shared service account is unavoidable, document and tightly control it.",
         "title_fr": "Assurer une identification unique pour chaque utilisateur",
         "text_fr": "Éliminez les comptes partagés ou génériques afin que chaque action soit attribuable à une personne; lorsqu'un compte de service partagé est inévitable, documentez-le et contrôlez-le étroitement.",
         "effort": "low", "impact": "medium"},
    ],
    "03.05.03": [
        {"title": "Enforce phishing-resistant MFA",
         "text": "Require MFA for all users and prioritize phishing-resistant factors (FIDO2/passkeys, app push with number matching) over SMS, starting with admins and remote access.",
         "title_fr": "Exiger une AMF résistante à l'hameçonnage",
         "text_fr": "Exigez l'authentification multifacteur (AMF) pour tous les utilisateurs et privilégiez les facteurs résistants à l'hameçonnage (FIDO2/clés d'accès, notification poussée avec appariement de numéros) plutôt que le SMS, en commençant par les administrateurs et l'accès à distance.",
         "effort": "medium", "impact": "high"},
    ],
    "03.05.05": [
        {"title": "Disable identifier reuse and stale accounts",
         "text": "Prevent reuse of user identifiers and automatically disable accounts after a defined period of inactivity.",
         "title_fr": "Empêcher la réutilisation des identifiants et désactiver les comptes inactifs",
         "text_fr": "Empêchez la réutilisation des identifiants d'utilisateur et désactivez automatiquement les comptes après une période d'inactivité définie.",
         "effort": "low", "impact": "medium"},
    ],
    "03.05.07": [
        {"title": "Modernize password policy to current guidance",
         "text": "Adopt length-based passphrases with breached-password screening and drop forced periodic rotation, aligning with NIST SP 800-63B; back it with MFA.",
         "title_fr": "Moderniser la politique de mots de passe selon les pratiques actuelles",
         "text_fr": "Adoptez des phrases de passe fondées sur la longueur, avec vérification des mots de passe compromis, et abandonnez la rotation périodique forcée, conformément au NIST SP 800-63B; appuyez le tout par l'AMF.",
         "effort": "low", "impact": "medium"},
    ],

    # ── 03.06 Incident Response ───────────────────────────────────────
    "03.06.01": [
        {"title": "Write and socialize an incident response plan",
         "text": "Document an IR plan with roles, severity tiers, contact tree, and reporting obligations; store it offline and make sure responders know it.",
         "title_fr": "Rédiger et diffuser un plan de réponse aux incidents",
         "text_fr": "Documentez un plan de réponse aux incidents précisant les rôles, les niveaux de gravité, l'arbre d'appels et les obligations de signalement; conservez-le hors ligne et assurez-vous que les intervenants le connaissent.",
         "effort": "medium", "impact": "high"},
    ],
    "03.06.02": [
        {"title": "Run a tabletop exercise",
         "text": "Test the IR plan at least annually with a tabletop scenario, capture gaps, and feed fixes back into the plan.",
         "title_fr": "Réaliser un exercice sur table",
         "text_fr": "Testez le plan de réponse aux incidents au moins une fois par année au moyen d'un scénario sur table, relevez les lacunes et réinjectez les correctifs dans le plan.",
         "effort": "low", "impact": "high"},
    ],

    # ── 03.07 Maintenance ─────────────────────────────────────────────
    "03.07.04": [
        {"title": "Control and scan maintenance tools/media",
         "text": "Inspect and scan media and tools used for maintenance before use, and supervise or authorize remote maintenance sessions.",
         "title_fr": "Contrôler et analyser les outils et supports de maintenance",
         "text_fr": "Inspectez et analysez les supports et outils utilisés pour la maintenance avant leur utilisation, et supervisez ou autorisez les sessions de maintenance à distance.",
         "effort": "low", "impact": "medium"},
    ],

    # ── 03.08 Media Protection ────────────────────────────────────────
    "03.08.03": [
        {"title": "Sanitize media before disposal or reuse",
         "text": "Adopt a documented sanitization/destruction process for media holding CUI (cryptographic erase, wipe, or shred) with certificates of destruction.",
         "title_fr": "Assainir les supports avant leur élimination ou réutilisation",
         "text_fr": "Adoptez un processus documenté d'assainissement ou de destruction des supports contenant des CUI (effacement cryptographique, écrasement ou déchiquetage), avec certificats de destruction.",
         "effort": "low", "impact": "medium"},
    ],
    "03.08.05": [
        {"title": "Control and log removable-media use",
         "text": "Restrict removable media by policy and technical control (e.g. block USB mass storage by default), allowing only approved, encrypted devices.",
         "title_fr": "Contrôler et journaliser l'utilisation des supports amovibles",
         "text_fr": "Restreignez les supports amovibles par politique et par contrôle technique (p. ex. bloquer par défaut le stockage de masse USB), en n'autorisant que des appareils approuvés et chiffrés.",
         "effort": "medium", "impact": "medium"},
    ],
    "03.08.07": [
        {"title": "Encrypt CUI on portable media and devices",
         "text": "Require full-disk and removable-media encryption so CUI at rest on portable storage is protected if lost or stolen.",
         "title_fr": "Chiffrer les CUI sur les supports et appareils portatifs",
         "text_fr": "Exigez le chiffrement intégral du disque et des supports amovibles afin que les CUI au repos sur du stockage portatif soient protégés en cas de perte ou de vol.",
         "effort": "low", "impact": "high"},
    ],

    # ── 03.10 Physical Protection ─────────────────────────────────────
    "03.10.07": [
        {"title": "Control and monitor physical access",
         "text": "Restrict physical access to systems and CUI to authorized staff with badge/lock controls, maintain visitor logs, and review access periodically.",
         "title_fr": "Contrôler et surveiller l'accès physique",
         "text_fr": "Restreignez l'accès physique aux systèmes et aux CUI au personnel autorisé au moyen de contrôles par badge ou serrure, tenez des registres de visiteurs et révisez les accès périodiquement.",
         "effort": "medium", "impact": "medium"},
    ],

    # ── 03.11 Risk Assessment ─────────────────────────────────────────
    "03.11.01": [
        {"title": "Perform a documented risk assessment",
         "text": "Run a periodic risk assessment of systems handling CUI, record threats/likelihood/impact, and use it to prioritize remediation.",
         "title_fr": "Réaliser une évaluation des risques documentée",
         "text_fr": "Effectuez une évaluation des risques périodique des systèmes traitant des CUI, consignez les menaces, la probabilité et l'impact, et utilisez-la pour prioriser la correction.",
         "effort": "medium", "impact": "high"},
    ],
    "03.11.02": [
        {"title": "Establish recurring vulnerability scanning",
         "text": "Scan systems for vulnerabilities on a schedule and after significant changes, then track findings to closure with SLAs by severity.",
         "title_fr": "Établir une analyse récurrente des vulnérabilités",
         "text_fr": "Analysez les systèmes à la recherche de vulnérabilités selon un calendrier et après tout changement important, puis assurez le suivi des constats jusqu'à leur résolution avec des délais selon la gravité.",
         "effort": "medium", "impact": "high"},
    ],
    "03.11.04": [
        {"title": "Define a risk-based remediation process",
         "text": "Prioritize and remediate vulnerabilities by risk, with documented timelines and exceptions, rather than ad-hoc patching.",
         "title_fr": "Définir un processus de correction fondé sur le risque",
         "text_fr": "Priorisez et corrigez les vulnérabilités selon le risque, avec des échéances et des exceptions documentées, plutôt qu'une application de correctifs au cas par cas.",
         "effort": "medium", "impact": "medium"},
    ],

    # ── 03.12 Security Assessment ─────────────────────────────────────
    "03.12.01": [
        {"title": "Assess controls and maintain a POA&M",
         "text": "Periodically assess control effectiveness and track deficiencies in a Plan of Action & Milestones with owners and due dates.",
         "title_fr": "Évaluer les contrôles et tenir un plan d'action et de jalons (POA&M)",
         "text_fr": "Évaluez périodiquement l'efficacité des contrôles et suivez les lacunes dans un plan d'action et de jalons (POA&M) comportant des responsables et des échéances.",
         "effort": "medium", "impact": "high"},
    ],
    "03.12.02": [
        {"title": "Operationalize the POA&M",
         "text": "Review the POA&M on a cadence, update status, and close items with evidence so it reflects reality at assessment time.",
         "title_fr": "Rendre le POA&M opérationnel",
         "text_fr": "Révisez le POA&M à une cadence définie, mettez à jour l'état d'avancement et fermez les éléments avec preuves à l'appui, afin qu'il reflète la réalité au moment de l'évaluation.",
         "effort": "low", "impact": "medium"},
    ],

    # ── 03.13 System & Communications Protection ──────────────────────
    "03.13.01": [
        {"title": "Harden and monitor network boundaries",
         "text": "Enforce deny-by-default at boundaries, separate internal/external traffic, and monitor boundary devices centrally.",
         "title_fr": "Durcir et surveiller les frontières du réseau",
         "text_fr": "Appliquez le refus par défaut aux frontières, séparez le trafic interne et externe, et surveillez de façon centralisée les équipements de frontière.",
         "effort": "medium", "impact": "high"},
    ],
    "03.13.08": [
        {"title": "Encrypt CUI in transit",
         "text": "Require TLS 1.2+ (or equivalent) for all transmission of CUI and disable legacy protocols/ciphers.",
         "title_fr": "Chiffrer les CUI en transit",
         "text_fr": "Exigez TLS 1.2 ou plus récent (ou l'équivalent) pour toute transmission de CUI et désactivez les protocoles et algorithmes désuets.",
         "effort": "low", "impact": "high"},
        {"title": "Encrypt CUI at rest",
         "text": "Apply validated encryption to stored CUI (full-disk plus database/file-level where feasible) on servers, endpoints, and portable devices, since r3 03.13.08 now covers storage as well as transmission.",
         "title_fr": "Chiffrer les CUI au repos",
         "text_fr": "Appliquez un chiffrement validé aux CUI stockés (chiffrement intégral du disque, et au niveau des bases de données et des fichiers lorsque possible) sur les serveurs, les postes et les appareils portatifs, puisque le contrôle 03.13.08 de la r3 couvre désormais le stockage en plus de la transmission.",
         "effort": "medium", "impact": "high"},
    ],
    "03.13.11": [
        {"title": "Use FIPS-validated cryptography for CUI",
         "text": "Standardize on FIPS-validated cryptographic modules for protecting CUI and document where they are applied.",
         "title_fr": "Utiliser une cryptographie validée FIPS pour les CUI",
         "text_fr": "Standardisez l'utilisation de modules cryptographiques validés FIPS pour protéger les CUI et documentez les endroits où ils sont appliqués.",
         "effort": "medium", "impact": "medium"},
    ],

    # ── 03.14 System & Information Integrity ──────────────────────────
    "03.14.01": [
        {"title": "Tighten patch/flaw remediation timelines",
         "text": "Define and meet SLAs for applying security patches (e.g. critical within days), measure compliance, and automate where possible.",
         "title_fr": "Resserrer les délais de correction des failles et d'application des correctifs",
         "text_fr": "Définissez et respectez des délais (p. ex. les correctifs critiques en quelques jours) pour l'application des correctifs de sécurité, mesurez la conformité et automatisez lorsque possible.",
         "effort": "medium", "impact": "high"},
    ],
    "03.14.02": [
        {"title": "Deploy and centrally manage EDR/anti-malware",
         "text": "Run modern endpoint protection (EDR) on all endpoints and servers with central visibility, auto-updates, and alerting.",
         "title_fr": "Déployer et gérer de façon centralisée une solution EDR/antimaliciel",
         "text_fr": "Exécutez une protection des terminaux moderne (EDR) sur tous les postes et serveurs, avec visibilité centralisée, mises à jour automatiques et alertes.",
         "effort": "medium", "impact": "high"},
    ],
    "03.14.06": [
        {"title": "Monitor systems for attacks and indicators",
         "text": "Add detection for inbound/outbound attack indicators (IDS/IPS, EDR telemetry) and route alerts to a monitored queue.",
         "title_fr": "Surveiller les systèmes pour détecter attaques et indicateurs",
         "text_fr": "Ajoutez la détection des indicateurs d'attaque entrants et sortants (IDS/IPS, télémétrie EDR) et acheminez les alertes vers une file surveillée.",
         "effort": "medium", "impact": "high"},
    ],
}
