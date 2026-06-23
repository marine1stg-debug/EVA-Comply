# -*- coding: utf-8 -*-
import sys; sys.path.insert(0,'tools')
import policy_builder as B
P="policy_library/"
S=[]
S.append({"title":"Politique de protection des supports","path":P+"Media_Protection_Policy.fr.docx",
 "purpose":"La présente politique établit comment [Nom de l'organisation] protège, manipule, stocke, transporte et assainit les supports numériques et physiques contenant de l'information contrôlée non classifiée (CUI). Les supports — des disques durs et clés USB aux documents imprimés et sauvegardes — se perdent, se volent ou se jettent facilement de façon inappropriée. Cette politique garantit que les CUI sur supports sont protégés au repos, en transport et en fin de vie.",
 "scope":["Tous les supports numériques (disques, SSD, clés USB, supports optiques, supports de sauvegarde) et physiques (documents imprimés) contenant des CUI.","Tout le stockage, le transport, la réutilisation et l'élimination de ces supports.","Tout le personnel qui manipule des supports contenant des CUI."],
 "definitions":[("Support","Matériel numérique ou physique sur lequel l'information est enregistrée (disques, USB, optique, papier, sauvegardes)."),("Assainissement","Rendre les données irrécupérables par effacement cryptographique, écrasement, démagnétisation ou destruction."),("Support amovible","Stockage portatif pouvant être branché/débranché (p. ex. clés USB)."),("Marquage des supports","Étiqueter les supports pour indiquer la sensibilité de leur contenu (p. ex. CUI).")],
 "roles":[["[Gestionnaire TI / ISSO]","Être propriétaire de la politique; approuver les méthodes d'assainissement et d'élimination; autoriser l'usage des supports."],["[Administrateur système]","Mettre en œuvre le chiffrement et les contrôles des supports amovibles; effectuer ou vérifier l'assainissement; gérer les sauvegardes."],["Tous les utilisateurs","Manipuler, stocker et transporter les supports CUI selon la politique; signaler immédiatement tout support perdu ou volé."],["[Haute direction / RSSI]","Approuver la politique; accepter le risque résiduel pour les exceptions documentées."]],
 "statements":[
   ("PS-1  Stockage et accès aux supports","Les supports contenant des CUI doivent être stockés de façon sécurisée (physiquement et logiquement) et l'accès restreint au personnel autorisé."),
   ("PS-2  Marquage des supports","Les supports contenant des CUI doivent être marqués ou étiquetés pour indiquer leur sensibilité, sauf si l'environnement rend le marquage inutile et que cela est documenté."),
   ("PS-3  Chiffrement des CUI sur supports","Les CUI au repos sur des supports portatifs et amovibles doivent être protégés par un chiffrement validé (disque intégral et/ou au niveau des fichiers), afin que la perte ou le vol n'entraîne pas de divulgation."),
   ("PS-4  Contrôle des supports amovibles","L'usage de supports amovibles sur les systèmes contenant des CUI doit être restreint par politique et contrôle technique (p. ex. bloquer par défaut le stockage de masse USB non approuvé); seuls des appareils approuvés et chiffrés peuvent être utilisés, et leur usage journalisé."),
   ("PS-5  Transport des supports","Les supports contenant des CUI transportés hors des zones contrôlées doivent être protégés (chiffrés et/ou dans des contenants approuvés), et les activités de transport suivies."),
   ("PS-6  Assainissement et élimination","Les supports contenant des CUI doivent être assainis par une méthode approuvée (effacement cryptographique, écrasement, démagnétisation ou destruction) avant élimination, cession ou réutilisation, avec conservation des registres/certificats."),
   ("PS-7  Protection des sauvegardes","Les sauvegardes contenant des CUI doivent être protégées par un chiffrement cohérent avec les CUI qu'elles contiennent, et l'accès aux sauvegardes contrôlé."),
 ],
 "procedures":[
   ("6.1  Manipulation et contrôle",["Marquer et stocker de façon sécurisée les supports CUI; restreindre l'accès.","Appliquer les contrôles des supports amovibles; n'autoriser que des appareils chiffrés approuvés."],"Inventaire/marquage des supports; configuration des supports amovibles; registres d'approbation d'appareils."),
   ("6.2  Transport, assainissement et sauvegardes",["Chiffrer et suivre les supports en transport.","Assainir les supports avant élimination/réutilisation et conserver les certificats; protéger les sauvegardes par chiffrement."],"Registres de transport; certificats d'assainissement/destruction; configuration de chiffrement des sauvegardes."),
 ],
 "compliance_focus":"en vérifiant que les supports CUI sont marqués, chiffrés, à accès contrôlé, transportés de façon sécurisée, assainis avant élimination, et que les sauvegardes sont protégées par chiffrement.",
 "related":["Politique de maintenance des systèmes — assainissement des équipements avant entretien hors site.","Politique de protection des systèmes et des communications — normes de chiffrement.","Politique de protection physique — zones de stockage sécurisées.","Plan de sécurité du système (SSP) — catégories et emplacements des CUI."],
 "mapping_intro":"Les identifiants proviennent du NIST SP 800-171 Rev 3 (famille 03.08); ils s'appliquent également au CMMC 2.0 niveau 2 et à l'ITSP.10.171 (CPCSC).",
 "mapping":[
   ["03.08.01  Stockage des supports","PS-1 — stockage sécurisé","Contrôles de stockage; registres d'accès"],
   ["03.08.02  Accès aux supports","PS-1 — accès restreint","Preuves de contrôle d'accès"],
   ["03.08.03  Assainissement des supports","PS-6 — assainissement/élimination","Certificats d'assainissement/destruction"],
   ["03.08.04  Marquage des supports","PS-2 — marquage","Exemples de supports marqués; procédure"],
   ["03.08.05  Transport des supports","PS-5 — transport protégé","Suivi du transport; preuves de chiffrement"],
   ["03.08.07  Utilisation des supports","PS-3, PS-4 — chiffrement; contrôle des amovibles","Config des amovibles; preuves de chiffrement"],
   ["03.08.09  Sauvegarde – protection cryptographique","PS-7 — sauvegardes protégées","Configuration de chiffrement des sauvegardes"],
 ]})

S.append({"title":"Politique de sécurité du personnel","path":P+"Personnel_Security_Policy.fr.docx",
 "purpose":"La présente politique établit comment [Nom de l'organisation] gère les risques de sécurité associés au personnel qui accède aux systèmes et à l'information contrôlée non classifiée (CUI), au moyen de la vérification, des ententes et de processus rigoureux d'entrée en fonction, de mutation et de départ. Les personnes sont à la fois le plus grand atout de l'organisation et une source fréquente de risque; cette politique garantit que l'accès est accordé à des personnes dignes de confiance et retiré promptement lorsqu'il n'est plus justifié.",
 "scope":["Tous les employés, sous-traitants et tiers à qui un accès aux systèmes visés ou aux CUI est accordé.","Toutes les activités d'embauche, de mutation et de départ qui touchent cet accès.","Toutes les ententes régissant l'usage acceptable et la confidentialité."],
 "definitions":[("Vérification","Contrôle préalable à l'accès, adapté au rôle et à la sensibilité de l'information consultée."),("Usage acceptable / Règles de conduite","Les règles documentées que les utilisateurs s'engagent à suivre pour accéder aux systèmes et aux CUI."),("Départ","La fin de l'emploi ou de l'engagement d'une personne."),("Mutation","Un changement de rôle pouvant modifier les besoins d'accès.")],
 "roles":[["[Ressources humaines]","Effectuer la vérification; obtenir les ententes signées; aviser les TI des embauches, mutations et départs dans le délai défini."],["[Gestionnaire TI / ISSO]","Être propriétaire de la politique; assurer l'approvisionnement et le retrait des accès avec les RH; tenir les registres."],["[Gestionnaire de service / Superviseur]","Définir les besoins d'accès du rôle; confirmer le moindre privilège; initier les mutations/départs."],["Tous les utilisateurs","Respecter les ententes d'usage acceptable; protéger les CUI; signaler les préoccupations."],["[Haute direction / RSSI]","Approuver la politique; accepter le risque résiduel pour les exceptions documentées."]],
 "statements":[
   ("PS-1  Vérification du personnel","Les personnes doivent être vérifiées en fonction de la sensibilité de l'information et des systèmes auxquels elles accéderont, avant que l'accès aux CUI soit accordé, conformément à la loi et au contrat applicables."),
   ("PS-2  Ententes d'usage acceptable et de confidentialité","Avant l'octroi de l'accès, les personnes doivent signer des ententes d'usage acceptable / de règles de conduite et de confidentialité couvrant la protection des CUI."),
   ("PS-3  Accès à l'embauche","L'accès doit être attribué au moindre privilège seulement après la vérification et les ententes, et l'initiation de la formation de sensibilisation à la sécurité."),
   ("PS-4  Mutation du personnel","Lorsqu'une personne change de rôle, ses accès doivent être révisés et ajustés au nouveau rôle dans les [défini par l'organisation : 5 jours ouvrables; recommandé : 5 jours ouvrables]."),
   ("PS-5  Départ du personnel","Au départ, l'accès doit être révoqué promptement (recommandé : le jour même), les identifiants et authentifiants désactivés, et les biens de l'organisation (y compris les CUI) récupérés. Les RH doivent aviser les TI dans les [1 jour ouvrable]."),
   ("PS-6  Personnel tiers","Le personnel des sous-traitants et fournisseurs doit satisfaire à des exigences équivalentes de vérification et d'ententes et être soumis à la même discipline de retrait d'accès."),
 ],
 "procedures":[
   ("6.1  Entrée en fonction",["Vérifier la personne; obtenir les ententes signées; attribuer un accès au moindre privilège; assigner la formation.","Consigner l'achèvement avant l'accès aux CUI."],"Dossiers de vérification; ententes signées; formulaires de demande d'accès; assignations de formation."),
   ("6.2  Mutation et départ",["À la mutation, réviser et ajuster l'accès au nouveau rôle.","Au départ, révoquer l'accès le jour même, désactiver les identifiants et récupérer les biens."],"Listes de vérification de mutation/départ; registres de révocation d'accès; registres de retour des biens."),
 ],
 "compliance_focus":"en vérifiant que la vérification et les ententes sont complétées avant l'accès, que les mutations ajustent l'accès et que les départs entraînent un retrait prompt de l'accès.",
 "related":["Politique de contrôle d'accès — approvisionnement, moindre privilège et cessation des accès.","Politique d'identification et d'authentification — émission et révocation des identifiants.","Politique de sensibilisation et de formation en sécurité — formation à l'entrée en fonction.","Plan de sécurité du système (SSP) — rôles et contexte d'accès aux CUI."],
 "mapping_intro":"Les identifiants proviennent du NIST SP 800-171 Rev 3 (famille 03.09); ils s'appliquent également au CMMC 2.0 niveau 2 et à l'ITSP.10.171 (CPCSC).",
 "mapping":[
   ["03.09.01  Vérification du personnel","PS-1, PS-6 — vérification avant l'accès","Dossiers de vérification; vérification des fournisseurs"],
   ["03.09.02  Départ et mutation du personnel","PS-4, PS-5 — actions de mutation et de départ","Listes de vérification; registres de révocation d'accès"],
 ]})

S.append({"title":"Politique de protection physique","path":P+"Physical_Protection_Policy.fr.docx",
 "purpose":"La présente politique établit comment [Nom de l'organisation] contrôle l'accès physique aux installations, à l'équipement et à l'infrastructure de soutien qui abritent les systèmes et l'information contrôlée non classifiée (CUI). Les contrôles logiques peuvent être contournés si un attaquant obtient un accès physique. Cette politique garantit que seules les personnes autorisées peuvent atteindre physiquement les systèmes contenant des CUI, que l'accès est surveillé et que les scénarios hors site et de transmission sont pris en compte.",
 "scope":["Toutes les installations, zones de travail, salles de serveurs/réseau et équipements qui stockent ou traitent des CUI.","Les visiteurs et tiers nécessitant un accès physique.","Les sites de travail alternatifs et la protection des lignes/équipements de transmission des CUI lorsque applicable."],
 "definitions":[("Zone contrôlée","Un espace dont l'accès est limité aux personnes autorisées."),("Autorisation d'accès physique","Droit approuvé d'une personne d'entrer dans une zone contrôlée."),("Visiteur","Une personne sans autorisation d'accès physique permanente."),("Site de travail alternatif","Un lieu hors des installations principales (p. ex. bureau à domicile) où le travail est effectué.")],
 "roles":[["[Gestionnaire TI / ISSO] / Installations","Être propriétaire de la politique; autoriser l'accès physique; tenir les listes d'accès; superviser la surveillance."],["[Administrateur système]","Protéger l'équipement dans les zones contrôlées; gérer l'accès aux salles de serveurs/réseau."],["Tous les utilisateurs","Suivre les règles de sécurité physique; interpeller/escorter les visiteurs; protéger les CUI aux sites alternatifs; signaler les incidents."],["[Haute direction / RSSI]","Approuver la politique; accepter le risque résiduel pour les exceptions documentées."]],
 "statements":[
   ("PS-1  Autorisations d'accès physique","L'accès physique aux zones contrôlées abritant des systèmes contenant des CUI doit être limité aux personnes autorisées au moyen d'une liste approuvée, les justificatifs (badges/clés) étant émis et révoqués par un processus contrôlé."),
   ("PS-2  Contrôle d'accès physique","L'entrée dans les zones contrôlées doit être appliquée par serrures, lecteurs de badge ou l'équivalent, et les listes d'accès révisées [défini par l'organisation : au moins trimestriellement; recommandé : trimestriellement]."),
   ("PS-3  Surveillance de l'accès physique","L'accès physique doit être surveillé (p. ex. journaux, alarmes, vidéo lorsque approprié) et tout accès non autorisé investigué."),
   ("PS-4  Contrôle des visiteurs","Les visiteurs doivent être identifiés, autorisés, consignés et escortés dans les zones contrôlées; les registres de visiteurs doivent être conservés."),
   ("PS-5  Sites de travail alternatifs","Les CUI consultés ou stockés aux sites de travail alternatifs (p. ex. télétravail) doivent être protégés par des mesures équivalentes (rangement verrouillé, écran de confidentialité, chiffrement des appareils)."),
   ("PS-6  Protection des dispositifs de transmission et de sortie","Le câblage, l'équipement réseau et les dispositifs de sortie (p. ex. imprimantes) traitant des CUI doivent être protégés contre l'accès physique non autorisé et l'interception lorsque applicable."),
 ],
 "procedures":[
   ("6.1  Accès et surveillance",["Tenir les listes d'accès autorisé; émettre/révoquer les badges; réviser les listes trimestriellement.","Surveiller l'accès; consigner et investiguer les anomalies."],"Listes d'accès (datées); émission/révocation de badges; journaux d'accès; approbations de revue."),
   ("6.2  Visiteurs et télétravail",["Consigner et escorter les visiteurs dans les zones contrôlées.","Fournir les mesures de protection des sites alternatifs et les accusés de réception."],"Registres de visiteurs; accusés de sécurité du télétravail."),
 ],
 "compliance_focus":"en vérifiant que les listes d'accès sont à jour et révisées, que les zones contrôlées sont physiquement sécurisées et surveillées, que les visiteurs sont escortés et consignés, et que les sites alternatifs sont protégés.",
 "related":["Politique de contrôle d'accès — accès logique complétant les contrôles physiques.","Politique de protection des supports — stockage physique des supports CUI.","Politique de protection des systèmes et des communications — protection des lignes de transmission.","Plan de sécurité du système (SSP) — contexte des installations et des CUI."],
 "mapping_intro":"Les identifiants proviennent du NIST SP 800-171 Rev 3 (famille 03.10); ils s'appliquent également au CMMC 2.0 niveau 2 et à l'ITSP.10.171 (CPCSC).",
 "mapping":[
   ["03.10.01  Autorisations d'accès physique","PS-1 — liste d'accès autorisé","Listes d'accès; registres d'émission de badges"],
   ["03.10.02  Surveillance de l'accès physique","PS-3 — surveillance","Journaux d'accès; registres d'alarme/vidéo"],
   ["03.10.06  Site de travail alternatif","PS-5 — mesures pour sites alternatifs","Accusés de télétravail; mesures de protection"],
   ["03.10.07  Contrôle d'accès physique","PS-2, PS-4 — entrée appliquée; contrôle des visiteurs","Config serrures/badges; registres de visiteurs; revues de listes"],
   ["03.10.08  Contrôle d'accès pour la transmission","PS-6 — protéger câblage/équipement","Protection physique du câblage/des dispositifs de sortie"],
 ]})

S.append({"title":"Politique d'évaluation des risques","path":P+"Risk_Assessment_Policy.fr.docx",
 "purpose":"La présente politique établit comment [Nom de l'organisation] cerne, évalue, priorise et traite les risques de cybersécurité pour ses opérations, ses actifs et les personnes, y compris les risques pour l'information contrôlée non classifiée (CUI), de façon récurrente. L'évaluation des risques concentre des ressources limitées sur les menaces les plus importantes et oriente les décisions de correction. Cette politique relie la gestion des vulnérabilités à la prise de décision fondée sur le risque.",
 "scope":["Tous les systèmes, processus et relations avec des tiers qui touchent la confidentialité, l'intégrité ou la disponibilité des CUI.","Les évaluations des risques récurrentes et ponctuelles et l'analyse des vulnérabilités.","Les décisions de réponse au risque et de correction."],
 "definitions":[("Risque","La probabilité et l'impact qu'une menace exploite une vulnérabilité."),("Évaluation des risques","Une analyse structurée des menaces, vulnérabilités, probabilité et impact."),("Vulnérabilité","Une faiblesse qui pourrait être exploitée pour compromettre un système."),("Réponse au risque","La décision d'atténuer, de transférer, d'éviter ou d'accepter un risque.")],
 "roles":[["[Gestionnaire TI / ISSO]","Être propriétaire de la politique; mener/superviser les évaluations et l'analyse; prioriser la correction; signaler le risque à la direction."],["[Administrateur système]","Exécuter les analyses de vulnérabilités; corriger les constats; fournir l'information des systèmes."],["[Haute direction / RSSI]","Approuver la politique; accepter ou orienter la réponse au risque résiduel; fournir les ressources."],["Tous les utilisateurs","Signaler les risques et faiblesses observés."]],
 "statements":[
   ("PS-1  Évaluation des risques récurrente","[Nom de l'organisation] doit réaliser une évaluation des risques documentée des systèmes traitant des CUI [défini par l'organisation : au moins annuellement et lors d'un changement important; recommandé : annuellement], consignant les menaces, vulnérabilités, probabilité et impact."),
   ("PS-2  Surveillance et analyse des vulnérabilités","Les systèmes doivent être analysés à la recherche de vulnérabilités selon un calendrier défini et après tout changement important; les résultats doivent être suivis jusqu'à résolution avec des délais selon la gravité."),
   ("PS-3  Priorisation des risques","Les risques et vulnérabilités identifiés doivent être priorisés selon le risque (impact × probabilité, en tenant compte de l'efficacité des contrôles) pour cibler la correction."),
   ("PS-4  Réponse et correction du risque","Pour chaque risque important, l'organisation doit sélectionner et documenter une réponse (atténuer, transférer, éviter ou accepter) avec responsables et échéances; les risques acceptés doivent être approuvés au niveau approprié."),
   ("PS-5  Entrées sur les menaces et vulnérabilités","Les évaluations doivent tenir compte de l'information actuelle sur les menaces, des avis des fournisseurs et de l'inventaire des composants afin d'évaluer rapidement les nouvelles vulnérabilités divulguées."),
   ("PS-6  Lien avec le POA&M","Les éléments de correction et les risques acceptés touchant des CUI doivent être reflétés dans le plan d'action et de jalons (POA&M)."),
 ],
 "procedures":[
   ("6.1  Évaluation et analyse",["Mener l'évaluation périodique; documenter menaces/probabilité/impact.","Analyser selon le calendrier et après les changements; suivre les constats avec des délais par gravité."],"Rapport d'évaluation des risques (daté); rapports d'analyse; registre des vulnérabilités."),
   ("6.2  Réponse",["Prioriser et assigner la correction; documenter les décisions de réponse et les approbations.","Refléter les éléments dans le POA&M."],"Billets de correction; approbations d'acceptation du risque; POA&M."),
 ],
 "compliance_focus":"en vérifiant que les évaluations sont à jour, que l'analyse des vulnérabilités a lieu selon le calendrier, que les constats sont suivis jusqu'à résolution par gravité et que les réponses au risque sont documentées.",
 "related":["Politique d'évaluation de la sécurité et de surveillance continue — évaluation des contrôles et POA&M.","Politique d'intégrité des systèmes et de l'information — délais de correction des failles.","Politique de gestion de la configuration — inventaire alimentant l'analyse.","Politique de gestion des risques liés à la chaîne d'approvisionnement — risque des fournisseurs."],
 "mapping_intro":"Les identifiants proviennent du NIST SP 800-171 Rev 3 (famille 03.11); ils s'appliquent également au CMMC 2.0 niveau 2 et à l'ITSP.10.171 (CPCSC).",
 "mapping":[
   ["03.11.01  Évaluation des risques","PS-1, PS-3 — évaluation périodique et priorisée","Rapport d'évaluation des risques (daté)"],
   ["03.11.02  Surveillance et analyse des vulnérabilités","PS-2, PS-5 — analyse et entrées sur les menaces","Rapports d'analyse; registre des vulnérabilités"],
   ["03.11.04  Réponse au risque","PS-4, PS-6 — réponse documentée; POA&M","Décisions de réponse; POA&M"],
 ]})

for s in S: B.build_fr(s); print("  ", s["path"].split("/")[-1])
print(f"FR batch3: {len(S)}")
