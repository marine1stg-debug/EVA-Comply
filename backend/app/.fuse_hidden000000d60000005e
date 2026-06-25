# -*- coding: utf-8 -*-
"""Backfill the 8 demo CMMC controls (NovLogix demo client) with French
translations AND a Best-practices field, so the demo experience is fully
bilingual and shows both the Best-practices and Expected-evidence boxes.

SAFE / idempotent: only updates the matched demo controls by ref.

USAGE (inside the api container):
    docker compose exec api python -m app.seed_demo_fr          # dry run
    docker compose exec api python -m app.seed_demo_fr --yes
"""
import argparse
import asyncio
from sqlalchemy import select
from app.core.database import AsyncSessionLocal
from app.models import framework, evidence  # noqa: F401 — register mappers
from app.models.framework import Control

# ref -> all the EN/FR fields to set
DATA = {
 "AC.1.001": {
   "title_fr": "Limiter l’accès aux systèmes aux utilisateurs autorisés",
   "description_fr": "Limiter l’accès aux systèmes d’information aux utilisateurs autorisés, aux processus agissant pour le compte d’utilisateurs autorisés et aux appareils.",
   "objective_fr": "Veiller à ce que seuls les utilisateurs et appareils autorisés puissent accéder aux systèmes de l’organisation.",
   "plain_language_fr": "Voyez cela comme un système de cartes d’accès : seules les personnes munies du bon badge peuvent entrer. Ce contrôle fait en sorte que vos systèmes informatiques fonctionnent de la même façon.",
   "best_practices": "Maintain an up-to-date list of who is allowed on each system\nGive each person a unique login (no shared accounts)\nRemove access the same day someone leaves or changes role\nReview the access list at least quarterly",
   "best_practices_fr": "Tenir à jour la liste des personnes autorisées sur chaque système\nAttribuer à chacun un identifiant unique (aucun compte partagé)\nRetirer l’accès le jour même d’un départ ou d’un changement de rôle\nRéviser la liste des accès au moins chaque trimestre",
   "evidence_best_practices_fr": "Politique de contrôle d’accès signée et datée\nListe actuelle des utilisateurs exportée de votre fournisseur d’identité\nCapture d’écran de l’inscription au MFA pour les comptes privilégiés\nExemples de journaux d’accès des 90 derniers jours",
 },
 "AC.1.002": {
   "title_fr": "Limiter l’accès aux types de transactions permises",
   "description_fr": "Limiter l’accès aux systèmes d’information aux types de transactions et de fonctions que les utilisateurs autorisés ont la permission d’exécuter.",
   "objective_fr": "Veiller à ce que les utilisateurs ne puissent effectuer que les actions autorisées pour leur rôle.",
   "plain_language_fr": "Les utilisateurs ne devraient pouvoir faire que ce que leur travail exige — rien de plus.",
   "best_practices": "Define roles and what each can do\nGrant the lowest access that still lets people work\nAvoid giving everyone administrator rights",
   "best_practices_fr": "Définir les rôles et ce que chacun peut faire\nAccorder le plus bas niveau d’accès permettant quand même de travailler\nÉviter d’accorder les droits d’administrateur à tout le monde",
   "evidence_best_practices_fr": "Politique de contrôle d’accès basé sur les rôles\nMatrice des rôles montrant les permissions par type d’utilisateur\nPreuve que les comptes surprivilégiés ont été révoqués",
 },
 "IA.1.076": {
   "title_fr": "Identifier les utilisateurs et les processus du système",
   "description_fr": "Identifier les utilisateurs des systèmes d’information, les processus agissant pour le compte d’utilisateurs ou les appareils.",
   "objective_fr": "Veiller à ce que chaque utilisateur et chaque processus soit identifié individuellement.",
   "plain_language_fr": "Chaque personne et chaque processus automatisé doit avoir un identifiant unique. Les comptes partagés sont interdits.",
   "best_practices": "Issue unique usernames; never share accounts\nKeep an inventory of service / system accounts",
   "best_practices_fr": "Attribuer des noms d’utilisateur uniques; ne jamais partager de comptes\nTenir un inventaire des comptes de service / système",
   "evidence_best_practices_fr": "Liste des comptes d’utilisateurs avec identifiants uniques\nPolitique interdisant les comptes partagés\nInventaire des comptes de service",
 },
 "IA.2.078": {
   "title_fr": "Appliquer une complexité minimale des mots de passe",
   "description_fr": "Imposer une complexité minimale des mots de passe et un changement de caractères lors de la création de nouveaux mots de passe.",
   "objective_fr": "Empêcher les accès non autorisés dus à des mots de passe faibles ou réutilisés.",
   "plain_language_fr": "Les mots de passe doivent être difficiles à deviner : au moins 12 caractères, avec majuscules et minuscules, chiffres et symboles.",
   "best_practices": "Set complexity / length rules (12+ characters)\nEnable MFA, especially for admins and remote access\nLock accounts after repeated failed attempts",
   "best_practices_fr": "Définir des règles de complexité/longueur (12 caractères et plus)\nActiver le MFA, surtout pour les administrateurs et l’accès à distance\nVerrouiller les comptes après plusieurs tentatives échouées",
   "evidence_best_practices_fr": "Document de politique de mots de passe\nConfiguration système montrant l’application des règles\nPreuve du dernier cycle de changement des mots de passe",
 },
 "CM.2.061": {
   "title_fr": "Établir et maintenir des configurations de référence",
   "description_fr": "Établir et maintenir des configurations de référence et des inventaires des systèmes d’information de l’organisation.",
   "objective_fr": "Prévenir la dérive de configuration et garantir un déploiement sécurisé des systèmes.",
   "plain_language_fr": "Créez une configuration standard et sécurisée pour chaque type de système, et documentez-la.",
   "best_practices": "Document baseline configs per system type\nUse hardening guides (e.g. CIS)\nKeep an asset inventory",
   "best_practices_fr": "Documenter les configurations de référence par type de système\nUtiliser des guides de renforcement (p. ex. CIS)\nTenir un inventaire des actifs",
   "evidence_best_practices_fr": "Documents de configuration de référence par type de système\nProcessus de gestion des changements\nComparaison des configurations actuelles avec la référence",
 },
 "IR.2.092": {
   "title_fr": "Suivre, documenter et signaler les incidents",
   "description_fr": "Suivre, documenter et signaler les incidents aux responsables désignés et/ou aux autorités.",
   "objective_fr": "Veiller à ce que les incidents soient détectés, documentés et escaladés de façon appropriée.",
   "plain_language_fr": "Lorsqu’un incident de sécurité survient, il doit être consigné et escaladé.",
   "best_practices": "Keep an incident register\nDefine reporting timelines and escalation contacts",
   "best_practices_fr": "Tenir un registre des incidents\nDéfinir les délais de signalement et les contacts d’escalade",
   "evidence_best_practices_fr": "Procédure de réponse aux incidents\nRegistre/journal des incidents\nListe de contacts pour l’escalade",
 },
 "AU.2.041": {
   "title_fr": "Veiller à ce que les actions des utilisateurs soient traçables",
   "description_fr": "Veiller à ce que les actions des utilisateurs individuels puissent être rattachées de façon unique à ceux-ci.",
   "objective_fr": "Assurer la responsabilisation et la capacité d’analyse forensique des actions sur le système.",
   "plain_language_fr": "Chaque action sur le système doit être journalisée avec l’auteur et le moment où elle a eu lieu.",
   "best_practices": "Log usernames with actions\nProtect logs from tampering\nDefine a retention period",
   "best_practices_fr": "Journaliser les noms d’utilisateur avec les actions\nProtéger les journaux contre l’altération\nDéfinir une période de conservation",
   "evidence_best_practices_fr": "Capture d’écran de la configuration des journaux d’audit\nExemple d’export de journal montrant l’activité des utilisateurs\nPolitique de conservation des journaux",
 },
 "SI.1.210": {
   "title_fr": "Identifier et corriger les failles des systèmes",
   "description_fr": "Identifier, signaler et corriger en temps opportun les failles des systèmes d’information.",
   "objective_fr": "Réduire la surface d’attaque en maintenant des systèmes à jour et corrigés.",
   "plain_language_fr": "Lorsqu’une vulnérabilité logicielle est découverte, corrigez-la rapidement.",
   "best_practices": "Turn on automatic updates where possible\nApply critical patches within a defined window\nTrack which systems need patching",
   "best_practices_fr": "Activer les mises à jour automatiques lorsque c’est possible\nAppliquer les correctifs critiques dans un délai défini\nSuivre les systèmes qui doivent être corrigés",
   "evidence_best_practices_fr": "Rapport d’analyse de vulnérabilités\nPolitique de gestion des correctifs\nPreuve qu’un correctif a été appliqué dans les délais (SLA)",
 },
}


async def run(commit: bool):
    async with AsyncSessionLocal() as db:
        print(f"Mode: {'COMMIT' if commit else 'DRY RUN'}\n")
        rows = (await db.execute(select(Control).where(Control.ref.in_(DATA.keys())))).scalars().all()
        n = 0
        for c in rows:
            d = DATA.get(c.ref)
            if not d:
                continue
            for attr, val in d.items():
                setattr(c, attr, val)
            n += 1
            print(f"  updated {c.ref}")
        if commit:
            await db.commit()
            print(f"\nCommitted {n} demo controls.")
        else:
            print(f"\nWould update {n} demo controls. Re-run with --yes.")


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--yes", action="store_true")
    args = ap.parse_args()
    asyncio.run(run(args.yes))
