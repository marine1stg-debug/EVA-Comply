# -*- coding: utf-8 -*-
import sys; sys.path.insert(0,'tools')
import policy_builder as B
P="policy_library/"
S=[]
S.append({"title":"Politique d'évaluation de la sécurité et de surveillance continue","path":P+"Security_Assessment_Continuous_Monitoring_Policy.fr.docx",
 "purpose":"La présente politique établit comment [Nom de l'organisation] évalue l'efficacité de ses contrôles de sécurité, gère les déficiences au moyen d'un plan d'action et de jalons (POA&M) et surveille en continu sa posture de sécurité pour les systèmes qui traitent, stockent ou transmettent de l'information contrôlée non classifiée (CUI). L'évaluation périodique combinée à la surveillance continue garantit que les contrôles demeurent efficaces dans le temps et que les écarts sont suivis jusqu'à résolution.",
 "scope":["Tous les contrôles de sécurité protégeant les systèmes visés et les CUI.","Les évaluations périodiques des contrôles, les activités de surveillance continue et le POA&M.","Les échanges d'information avec des systèmes/partenaires externes lorsque applicable."],
 "definitions":[("Évaluation de la sécurité","Une évaluation visant à déterminer si les contrôles sont mis en œuvre correctement et fonctionnent comme prévu."),("POA&M","Un plan documenté qui suit les déficiences, les mesures correctives, les responsables et les jalons."),("Surveillance continue","Une connaissance continue de l'état de sécurité par des indicateurs, analyses, revues de journaux et vérifications de contrôles."),("Échange d'information","Le partage d'information avec un système externe, régi par des ententes.")],
 "roles":[["[Gestionnaire TI / ISSO]","Être propriétaire de la politique; planifier et réaliser les évaluations; tenir le POA&M; assurer la surveillance continue; signaler à la direction."],["[Administrateur système]","Fournir les preuves; corriger les éléments du POA&M; soutenir les outils de surveillance."],["[Haute direction / RSSI]","Approuver la politique; examiner la posture et le POA&M; accepter le risque résiduel."],["Tous les utilisateurs","Soutenir les évaluations en fournissant de l'information exacte."]],
 "statements":[
   ("PS-1  Évaluation périodique des contrôles","[Nom de l'organisation] doit évaluer les contrôles protégeant les CUI [défini par l'organisation : au moins annuellement et lors d'un changement important; recommandé : annuellement] afin de déterminer s'ils sont mis en œuvre correctement et fonctionnent efficacement."),
   ("PS-2  Plan d'action et de jalons (POA&M)","Les déficiences relevées par les évaluations, analyses ou la surveillance doivent être consignées dans un POA&M avec responsables, mesures prévues et dates de jalons, et suivies jusqu'à résolution."),
   ("PS-3  Surveillance continue","L'organisation doit surveiller en continu sa posture au moyen d'un ensemble défini d'indicateurs et d'activités (analyses de vulnérabilités, revue des journaux/alertes, conformité de configuration, vérifications de contrôles) à des fréquences définies."),
   ("PS-4  Indépendance et preuves d'évaluation","Les évaluations doivent s'appuyer sur des preuves objectives; lorsque possible, les évaluateurs devraient être indépendants du contrôle qu'ils évaluent."),
   ("PS-5  Rapports","Les résultats d'évaluation, l'état du POA&M et les indicateurs de surveillance doivent être communiqués à la direction selon une cadence définie afin d'éclairer les décisions de risque."),
   ("PS-6  Échange d'information","Lorsque des systèmes visés échangent de l'information avec des systèmes externes, l'échange doit être régi par des ententes définissant les responsabilités et exigences de sécurité."),
 ],
 "procedures":[
   ("6.1  Évaluer et suivre",["Planifier et réaliser l'évaluation périodique avec preuves.","Consigner les déficiences au POA&M; assigner responsables et jalons; suivre jusqu'à résolution."],"Plan et résultats d'évaluation; POA&M (daté, mis à jour)."),
   ("6.2  Surveiller et rapporter",["Exécuter les activités de surveillance continue aux fréquences définies.","Communiquer la posture, l'état du POA&M et les indicateurs à la direction."],"Indicateurs/tableaux de bord de surveillance; registres d'analyse et de revue; rapports à la direction."),
 ],
 "compliance_focus":"en vérifiant que les contrôles sont évalués selon le calendrier, que les déficiences sont suivies dans le POA&M jusqu'à résolution, que la surveillance continue a lieu et que les résultats sont communiqués.",
 "related":["Politique d'évaluation des risques — entrées de risque et analyse des vulnérabilités.","Politique d'audit et de responsabilisation — revue des journaux alimentant la surveillance.","Politique de gestion de la configuration — vérifications de conformité de configuration.","Plan de sécurité du système (SSP) — base de mise en œuvre des contrôles."],
 "mapping_intro":"Les identifiants proviennent du NIST SP 800-171 Rev 3 (famille 03.12); ils s'appliquent également au CMMC 2.0 niveau 2 et à l'ITSP.10.171 (CPCSC).",
 "mapping":[
   ["03.12.01  Évaluation de la sécurité","PS-1, PS-4 — évaluation périodique avec preuves","Plan et résultats d'évaluation"],
   ["03.12.02  Plan d'action et de jalons","PS-2 — POA&M","POA&M (daté, suivi)"],
   ["03.12.03  Surveillance continue","PS-3, PS-5 — surveillance et rapports","Indicateurs de surveillance; rapports à la direction"],
   ["03.12.05  Échange d'information","PS-6 — ententes d'échange","Ententes d'interconnexion/de partage de données"],
 ]})

S.append({"title":"Politique de protection des systèmes et des communications","path":P+"System_Communications_Protection_Policy.fr.docx",
 "purpose":"La présente politique établit comment [Nom de l'organisation] protège l'information en transit et au repos et comment elle segmente et défend ses réseaux pour les systèmes qui traitent, stockent ou transmettent de l'information contrôlée non classifiée (CUI). Les protections réseau et cryptographiques préviennent l'interception, l'altération et le déplacement latéral. Cette politique définit la défense des frontières, le chiffrement, la gestion des clés et les mesures de protection des communications connexes.",
 "scope":["Tous les réseaux, frontières et communications transportant des CUI.","Tous les mécanismes cryptographiques protégeant les CUI en transit et au repos.","Tous les systèmes et services qui transmettent, traitent ou stockent des CUI."],
 "definitions":[("Protection des frontières","Contrôles (p. ex. pare-feu) qui surveillent et contrôlent les communications aux frontières externes et internes clés."),("Chiffrement en transit","Protéger les données lorsqu'elles circulent sur les réseaux (p. ex. TLS, RPV)."),("Chiffrement au repos","Protéger les données stockées (disque intégral, base de données, niveau fichier)."),("Gestion des clés cryptographiques","Générer, distribuer, stocker, renouveler et détruire les clés de façon sécurisée."),("Refus par défaut","Bloquer toutes les communications sauf celles explicitement permises.")],
 "roles":[["[Gestionnaire TI / ISSO]","Être propriétaire de la politique; approuver l'architecture réseau et les normes cryptographiques; superviser la défense des frontières."],["[Administrateur système]","Mettre en œuvre pare-feu, segmentation, chiffrement et gestion des clés; surveiller les équipements de frontière."],["Tous les utilisateurs","Utiliser des canaux approuvés et chiffrés; ne pas contourner les contrôles réseau; signaler les anomalies."],["[Haute direction / RSSI]","Approuver la politique; accepter le risque résiduel pour les exceptions documentées."]],
 "statements":[
   ("PS-1  Protection des frontières","Les communications aux frontières externes et internes clés doivent être surveillées et contrôlées au moyen d'interfaces gérées (p. ex. pare-feu), avec des règles de refus par défaut et une surveillance centralisée."),
   ("PS-2  Segmentation et refus par défaut","Les systèmes contenant des CUI doivent être placés dans des segments protégés; les communications réseau doivent être en refus par défaut et ne permettre que les flux explicitement approuvés."),
   ("PS-3  Chiffrement en transit","Toute transmission de CUI doit utiliser un chiffrement validé (TLS 1.2+ ou l'équivalent / RPV approuvé). Les protocoles désuets et algorithmes faibles doivent être désactivés."),
   ("PS-4  Chiffrement au repos","Les CUI au repos doivent être protégés par un chiffrement validé sur les serveurs, postes, bases de données et appareils portatifs."),
   ("PS-5  Protection cryptographique (FIPS)","La cryptographie utilisée pour protéger les CUI doit recourir à des modules cryptographiques validés (p. ex. validés FIPS), et leurs emplacements d'application doivent être documentés."),
   ("PS-6  Gestion des clés","Les clés cryptographiques doivent être établies et gérées de façon sécurisée (génération, distribution, stockage, renouvellement et destruction), avec un accès restreint."),
   ("PS-7  Information dans les ressources partagées","Les systèmes doivent empêcher tout transfert non autorisé ou non intentionnel d'information par les ressources partagées (p. ex. mémoire, réutilisation du stockage)."),
   ("PS-8  Déconnexion réseau et authenticité de session","Les sessions réseau doivent être terminées après une période d'inactivité définie ou à la fin de la session, et l'authenticité des sessions protégée (p. ex. contre le détournement)."),
   ("PS-9  Dispositifs collaboratifs et code mobile","Les dispositifs informatiques collaboratifs (p. ex. caméras, microphones) doivent indiquer leur utilisation active et être contrôlables; le code mobile doit être restreint à un usage approuvé et contrôlé."),
 ],
 "procedures":[
   ("6.1  Défense du réseau",["Appliquer le refus par défaut aux frontières; segmenter les CUI; surveiller les équipements de frontière de façon centralisée.","Terminer les sessions inactives; protéger l'authenticité des sessions."],"Règles de pare-feu; schémas de segmentation; journaux des équipements de frontière; configuration des délais de session."),
   ("6.2  Cryptographie",["Imposer TLS 1.2+/RPV approuvé; chiffrer les CUI au repos avec des modules validés.","Gérer les clés tout au long de leur cycle de vie avec un accès restreint."],"Configuration TLS/RPV; preuves de chiffrement au repos; liste des modules FIPS; procédures de gestion des clés."),
 ],
 "compliance_focus":"en vérifiant que la défense des frontières et la segmentation sont appliquées, que les CUI sont chiffrés en transit et au repos avec une cryptographie validée, et que les clés sont gérées de façon sécurisée.",
 "related":["Politique de contrôle d'accès — accès à distance et contrôles sans fil.","Politique de protection des supports — chiffrement des CUI sur supports.","Politique de gestion de la configuration — configurations de référence durcies des équipements réseau.","Plan de sécurité du système (SSP) — architecture réseau et flux de CUI."],
 "mapping_intro":"Les identifiants proviennent du NIST SP 800-171 Rev 3 (famille 03.13); ils s'appliquent également au CMMC 2.0 niveau 2 et à l'ITSP.10.171 (CPCSC).",
 "mapping":[
   ["03.13.01  Protection des frontières","PS-1 — frontières gérées","Règles de pare-feu; surveillance des frontières"],
   ["03.13.04  Information dans les ressources partagées","PS-7 — empêcher les fuites par ressources partagées","Config empêchant les fuites par réutilisation"],
   ["03.13.06  Communications réseau – refus par défaut","PS-2 — flux en refus par défaut","Ensembles de règles de pare-feu en refus par défaut"],
   ["03.13.08  Confidentialité en transmission et au stockage","PS-3, PS-4 — chiffrement en transit et au repos","Preuves de chiffrement TLS/RPV et au repos"],
   ["03.13.09  Déconnexion réseau","PS-8 — fin de session","Configuration de déconnexion par inactivité"],
   ["03.13.10  Établissement et gestion des clés","PS-6 — gestion des clés","Procédures et preuves de gestion des clés"],
   ["03.13.11  Protection cryptographique","PS-5 — cryptographie validée","Liste des modules validés FIPS; carte d'utilisation"],
   ["03.13.12  Dispositifs et applications collaboratifs","PS-9 — contrôle des dispositifs collaboratifs","Config d'indicateur et de contrôle caméra/micro"],
   ["03.13.13  Code mobile","PS-9 — contrôle du code mobile","Configuration de restriction du code mobile"],
   ["03.13.15  Authenticité de session","PS-8 — authenticité de session","Configuration de protection des sessions"],
 ]})

S.append({"title":"Politique d'intégrité des systèmes et de l'information","path":P+"System_Information_Integrity_Policy.fr.docx",
 "purpose":"La présente politique établit comment [Nom de l'organisation] cerne, signale et corrige les failles des systèmes et protège ceux-ci contre le code malveillant et les menaces émergentes, pour les environnements qui traitent, stockent ou transmettent de l'information contrôlée non classifiée (CUI). L'application rapide des correctifs, l'antimaliciel, la veille des avis de menaces et la surveillance des systèmes sont des défenses essentielles. Cette politique définit les délais et les outils qui maintiennent les systèmes dignes de confiance.",
 "scope":["Tous les systèmes, postes, serveurs et applications visés.","La correction des failles (application de correctifs), la protection contre le code malveillant, les avis de sécurité et la surveillance des systèmes.","L'information devant être gérée et conservée pour son intégrité."],
 "definitions":[("Correction des failles","Cerner et corriger les défauts de sécurité, généralement par l'application de correctifs."),("Code malveillant","Logiciel conçu pour nuire (virus, rançongiciel, chevaux de Troie)."),("EDR (détection et réponse sur les terminaux)","Logiciel qui détecte, investigue et répond aux menaces sur les terminaux."),("Avis de sécurité","Notification d'un fournisseur ou d'une autorité concernant une vulnérabilité ou une menace nécessitant une action.")],
 "roles":[["[Gestionnaire TI / ISSO]","Être propriétaire de la politique; fixer les délais de correctifs; assurer le déploiement de l'antimaliciel et de la surveillance; suivre les avis."],["[Administrateur système]","Appliquer les correctifs dans les délais; gérer l'EDR/antimaliciel; agir sur les avis; ajuster la surveillance."],["Tous les utilisateurs","Tenir les appareils à jour; ne pas désactiver les outils de sécurité; signaler l'activité suspecte."],["[Haute direction / RSSI]","Approuver la politique; financer les outils; accepter le risque résiduel pour les exceptions documentées."]],
 "statements":[
   ("PS-1  Correction des failles et délais de correctifs","Les failles pertinentes pour la sécurité doivent être cernées et corrigées dans des délais définis selon la gravité (p. ex. [défini par l'organisation : critique en 15 jours, élevée en 30 jours; recommandé selon CISA/ANS]). La conformité aux correctifs doit être mesurée et automatisée lorsque possible."),
   ("PS-2  Protection contre le code malveillant","Une protection des terminaux moderne (EDR/antimaliciel) doit fonctionner sur tous les postes et serveurs, avec gestion centralisée, mises à jour automatiques et alertes. Le code malveillant détecté doit être traité selon la Politique de réponse aux incidents."),
   ("PS-3  Avis et alertes de sécurité","L'organisation doit surveiller les avis et alertes de sécurité autoritatifs (p. ex. fournisseur, CISA) et agir rapidement sur ceux touchant ses systèmes."),
   ("PS-4  Surveillance des systèmes","Les systèmes et le réseau doivent être surveillés pour les attaques et indicateurs de compromission (p. ex. IDS/IPS, télémétrie EDR), les alertes étant acheminées vers une file surveillée et intégrées à la réponse aux incidents."),
   ("PS-5  Gestion et conservation de l'information","L'information dans les systèmes doit être gérée et conservée conformément aux exigences afin de préserver son intégrité et sa disponibilité aussi longtemps que nécessaire."),
   ("PS-6  Vérification de l'intégrité","Lorsque possible, des mécanismes de vérification d'intégrité doivent détecter les changements non autorisés aux logiciels, micrologiciels et à l'information."),
 ],
 "procedures":[
   ("6.1  Corriger et protéger",["Cerner les failles; appliquer les correctifs dans les délais par gravité; mesurer la conformité.","Déployer et gérer de façon centralisée l'EDR/antimaliciel avec mises à jour automatiques et alertes."],"Rapports de conformité aux correctifs; preuves de couverture EDR; registres de traitement des maliciels."),
   ("6.2  Surveiller et veiller",["Surveiller les avis et agir sur les pertinents.","Surveiller les systèmes pour les indicateurs d'attaque; acheminer les alertes à la réponse aux incidents."],"Registres de suivi des avis; configuration de surveillance/alerte; billets d'alerte."),
 ],
 "compliance_focus":"en vérifiant que les correctifs sont appliqués dans les délais, que l'antimaliciel/EDR est déployé et à jour, que les avis sont traités et que les systèmes sont surveillés avec acheminement des alertes.",
 "related":["Politique et plan de réponse aux incidents — traitement des menaces détectées.","Politique d'évaluation des risques — analyse et priorisation des vulnérabilités.","Politique d'audit et de responsabilisation — journaux alimentant la surveillance.","Politique de gestion de la configuration — configurations de référence et déploiement des correctifs."],
 "mapping_intro":"Les identifiants proviennent du NIST SP 800-171 Rev 3 (famille 03.14); ils s'appliquent également au CMMC 2.0 niveau 2 et à l'ITSP.10.171 (CPCSC).",
 "mapping":[
   ["03.14.01  Correction des failles","PS-1 — délais de correctifs","Rapports de conformité aux correctifs"],
   ["03.14.02  Protection contre le code malveillant","PS-2 — EDR/antimaliciel","Couverture EDR; état des mises à jour; alertes"],
   ["03.14.03  Alertes, avis et directives de sécurité","PS-3 — surveillance/action sur les avis","Registres de suivi des avis"],
   ["03.14.06  Surveillance des systèmes","PS-4, PS-6 — surveillance; vérifications d'intégrité","Config de surveillance/alerte; preuves de vérification d'intégrité"],
   ["03.14.08  Gestion et conservation de l'information","PS-5 — gérer et conserver l'information","Configuration/registres de conservation"],
 ]})

S.append({"title":"Politique de sensibilisation et de formation en sécurité","path":P+"Security_Awareness_Training_Policy.fr.docx",
 "owner":"[Gestionnaire TI / ISSO]",
 "purpose":"La présente politique établit comment [Nom de l'organisation] veille à ce que le personnel reçoive une sensibilisation à la sécurité et une formation adaptée à ses rôles et à ses fonctions, afin de reconnaître et de contrer les menaces et de bien protéger l'information contrôlée non classifiée (CUI). Les personnes sont une première ligne de défense; un personnel informé prévient et signale les incidents. Cette politique définit la formation de sensibilisation, la formation propre aux rôles et le suivi.",
 "scope":["Tous les employés, sous-traitants et tiers ayant accès aux systèmes visés ou aux CUI.","La formation de sensibilisation à l'entrée en fonction et à intervalles récurrents, ainsi que la formation propre aux rôles.","Le suivi des achèvements de formation."],
 "definitions":[("Formation de sensibilisation","Formation générale aidant tous les utilisateurs à reconnaître et éviter les menaces courantes (p. ex. hameçonnage)."),("Formation propre aux rôles","Formation adaptée aux responsabilités de sécurité d'un rôle précis (p. ex. administrateurs, développeurs)."),("Simulation d'hameçonnage","Un exercice contrôlé qui teste la capacité des utilisateurs à reconnaître l'hameçonnage.")],
 "roles":[["[Gestionnaire TI / ISSO]","Être propriétaire de la politique; définir le contenu et la cadence; suivre les achèvements; produire les indicateurs."],["[Ressources humaines]","Assigner la formation à l'entrée en fonction; soutenir le suivi et les relances."],["[Gestionnaire de service / Superviseur]","Veiller à ce que leur équipe complète la formation requise."],["Tous les utilisateurs","Compléter la formation assignée; l'appliquer; signaler les menaces soupçonnées."],["[Haute direction / RSSI]","Approuver la politique; renforcer une culture de sécurité."]],
 "statements":[
   ("PS-1  Formation de sensibilisation à la sécurité","Tous les utilisateurs doivent suivre une formation de sensibilisation à l'entrée en fonction et au moins [défini par l'organisation : annuellement; recommandé : annuellement], couvrant la reconnaissance de l'hameçonnage, l'ingénierie sociale et la bonne manipulation des CUI."),
   ("PS-2  Sensibilisation continue et simulation d'hameçonnage","L'organisation doit renforcer la sensibilisation par des communications périodiques et des simulations d'hameçonnage, et utiliser les résultats pour cibler une formation additionnelle."),
   ("PS-3  Formation propre aux rôles","Le personnel ayant des responsabilités de sécurité importantes (p. ex. administrateurs, développeurs, intervenants en incident, personnes manipulant des CUI) doit recevoir une formation propre à son rôle avant ou peu après l'assumer, puis périodiquement."),
   ("PS-4  Formation sur les politiques et la manipulation des CUI","La formation doit couvrir les politiques de sécurité de l'organisation, l'usage acceptable et les exigences précises de manipulation des CUI."),
   ("PS-5  Suivi des achèvements","L'achèvement de la formation doit être suivi, et le non-achèvement faire l'objet de relances; les registres doivent être conservés à titre de preuve."),
 ],
 "procedures":[
   ("6.1  Offrir et suivre",["Assigner la formation de sensibilisation à l'entrée en fonction et annuellement; offrir la formation propre aux rôles au personnel concerné.","Mener des simulations d'hameçonnage; suivre les achèvements et relancer les lacunes."],"Assignations et registres d'achèvement; résultats des simulations d'hameçonnage; registres de formation propre aux rôles."),
 ],
 "compliance_focus":"en vérifiant que la formation de sensibilisation est complétée à l'entrée en fonction et annuellement, que la formation propre aux rôles est offerte et que les achèvements sont suivis.",
 "related":["Politique de sécurité du personnel — entrée en fonction déclenchant la formation.","Politique de contrôle d'accès — formation complétée avant l'accès aux CUI.","Politique et plan de réponse aux incidents — comment signaler les incidents.","Plan de sécurité du système (SSP) — rôles exigeant une formation propre aux rôles."],
 "mapping_intro":"Les identifiants proviennent du NIST SP 800-171 Rev 3 (famille 03.02); ils s'appliquent également au CMMC 2.0 niveau 2 et à l'ITSP.10.171 (CPCSC).",
 "mapping":[
   ["03.02.01  Littératie et sensibilisation","PS-1, PS-2, PS-4 — sensibilisation; hameçonnage; politiques/CUI","Registres de sensibilisation; résultats de simulations"],
   ["03.02.02  Formation propre aux rôles","PS-3, PS-5 — formation propre aux rôles; suivi","Registres de formation propre aux rôles; suivi des achèvements"],
 ]})

for s in S: B.build_fr(s); print("  ", s["path"].split("/")[-1])
print(f"FR batch4: {len(S)}")
