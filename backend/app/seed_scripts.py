"""Seed hand-written bilingual recording scripts for the CMMC controls.

Run once: `python -m app.seed_scripts` (inside the api container).
Idempotent: it overwrites the script fields for the listed control refs only.
Scripts remain editable in the app (Training → Control preview).
"""
import asyncio
import re
from sqlalchemy import select

from app.core.database import AsyncSessionLocal
from app.models.framework import Framework, Control

FRAMEWORK = "CMMC 2.0"


def aerate(text: str) -> str:
    """Break a single-paragraph script into ~2-sentence paragraphs, keeping the
    final 'Key takeaway' / 'Point clé' line on its own."""
    raw = [l.strip() for l in text.strip().split("\n") if l.strip()]
    take = ""
    if raw and (raw[-1].startswith("Key takeaway") or raw[-1].startswith("Point clé")):
        take = raw[-1]
        body = " ".join(raw[:-1])
    else:
        body = " ".join(raw)
    sents = re.split(r"(?<=[.!?…]) +", body)
    paras, cur = [], []
    for s in sents:
        cur.append(s)
        if len(cur) >= 2:
            paras.append(" ".join(cur)); cur = []
    if cur:
        paras.append(" ".join(cur))
    out = "\n\n".join(paras)
    return out + ("\n\n" + take if take else "")

# ref -> {"en": script, "fr": script}.  Each ends with a "Key takeaway" line.
SCRIPTS = {
    "AC.1.001": {
        "en": (
            "Let's talk about limiting system access to authorized users. Think of your company's systems like an office "
            "building — you wouldn't hand a key to just anyone. Only people who work there get in, and only to the rooms "
            "they actually need. This control does the same thing digitally: it makes sure only approved users, and the "
            "devices and programs acting for them, can reach your systems. Why does it matter? Because a huge share of "
            "incidents start with access that should never have been granted, or was never removed when someone left. To "
            "comply, keep a current list of who is allowed in, grant access based on a person's job, and remove it the "
            "moment they change roles or leave. An auditor will look for that access list, proof of how access is approved, "
            "and evidence that old accounts get disabled.\n"
            "Key takeaway: Only approved users and devices should reach your systems, and access should be granted, "
            "reviewed, and removed deliberately."
        ),
        "fr": (
            "Parlons de la limitation de l'accès aux seuls utilisateurs autorisés. Imaginez vos systèmes comme un immeuble "
            "de bureaux : vous ne donneriez pas une clé à n'importe qui. Seules les personnes qui y travaillent entrent, et "
            "uniquement dans les pièces dont elles ont besoin. Ce contrôle fait la même chose côté numérique : seuls les "
            "utilisateurs approuvés, et les appareils et programmes qui agissent en leur nom, peuvent accéder à vos "
            "systèmes. Pourquoi est-ce important ? Parce qu'une grande part des incidents commence par un accès qui "
            "n'aurait jamais dû être accordé, ou jamais retiré. Pour vous conformer, tenez à jour la liste des personnes "
            "autorisées, accordez l'accès selon le rôle, et retirez-le dès qu'une personne change de poste ou part. "
            "L'auditeur cherchera cette liste, la preuve du processus d'approbation et la preuve que les anciens comptes "
            "sont désactivés.\n"
            "Point clé : Seuls les utilisateurs et appareils approuvés devraient accéder à vos systèmes, et l'accès doit "
            "être accordé, révisé et retiré de façon délibérée."
        ),
    },
    "AC.1.002": {
        "en": (
            "This control is about limiting what people can do once they're inside — not just whether they can get in. "
            "Think of a hotel: your keycard opens your room and the gym, but not the manager's office or the cash drawer. "
            "In your systems, each person should only be able to perform the transactions and functions their job actually "
            "requires. This matters because even trusted users can cause harm by accident, and an attacker who steals one "
            "account should be boxed into a small space, not handed the keys to everything. To comply, define what each "
            "role is allowed to do, give people the least access they need, and review those permissions regularly. An "
            "auditor will look for documented roles and permissions and proof they match what people can actually do.\n"
            "Key takeaway: Limit each user to only the actions their role requires — nothing more."
        ),
        "fr": (
            "Ce contrôle vise à limiter ce que les gens peuvent faire une fois à l'intérieur — pas seulement s'ils peuvent "
            "entrer. Pensez à un hôtel : votre carte ouvre votre chambre et la salle de sport, mais pas le bureau du "
            "gérant ni la caisse. Dans vos systèmes, chaque personne ne devrait pouvoir effectuer que les transactions et "
            "fonctions que son poste exige. C'est important car même un utilisateur de confiance peut nuire par accident, "
            "et un pirate qui vole un compte doit rester confiné à un petit espace. Pour vous conformer, définissez ce que "
            "chaque rôle peut faire, accordez le minimum d'accès nécessaire et révisez régulièrement ces droits. "
            "L'auditeur cherchera des rôles et permissions documentés, et la preuve qu'ils correspondent à la réalité.\n"
            "Point clé : Limitez chaque utilisateur aux seules actions exigées par son rôle — rien de plus."
        ),
    },
    "IA.1.076": {
        "en": (
            "Let's look at identifying users and processes. Before you can control access, you need to know exactly who — "
            "or what — is asking. This control requires that every user, and every automated process acting for them, has "
            "its own unique identity. Shared logins are the enemy here: if five people use one account, you can't tell who "
            "did what, and you can't hold anyone accountable. It's like a building where everyone signs in as \"staff\" — "
            "useless if something goes wrong. To comply, give each person their own account, give services their own "
            "identities too, and ban shared or generic logins. An auditor will look for a list of accounts tied to real "
            "individuals and evidence that shared accounts aren't in use.\n"
            "Key takeaway: Every user and process must have its own unique identity — no shared accounts."
        ),
        "fr": (
            "Parlons de l'identification des utilisateurs et des processus. Avant de contrôler l'accès, il faut savoir "
            "exactement qui — ou quoi — fait la demande. Ce contrôle exige que chaque utilisateur, et chaque processus "
            "automatisé agissant pour lui, ait une identité unique. Les comptes partagés sont l'ennemi : si cinq personnes "
            "utilisent un même compte, impossible de savoir qui a fait quoi, ni de tenir quiconque responsable. C'est comme "
            "un immeuble où tout le monde signe « personnel » — inutile en cas de problème. Pour vous conformer, donnez à "
            "chaque personne son propre compte, attribuez aussi une identité aux services, et interdisez les comptes "
            "partagés ou génériques. L'auditeur cherchera une liste de comptes liés à des personnes réelles.\n"
            "Point clé : Chaque utilisateur et processus doit avoir une identité unique — aucun compte partagé."
        ),
    },
    "IA.2.078": {
        "en": (
            "This control is about password strength. Passwords are still the front-door lock for most systems, and weak "
            "ones are like a lock anyone can pick. The goal is simple: make passwords hard to guess and hard to reuse. "
            "Attackers run automated tools that try millions of common passwords a second, so \"summer2024\" won't survive "
            "long. To comply, require a minimum length and a mix of character types when passwords are created, and require "
            "real change when they're updated. Even better, pair this with multi-factor authentication so a stolen password "
            "alone isn't enough. An auditor will look for your password policy and proof that systems actually enforce it — "
            "not just a document that says so.\n"
            "Key takeaway: Require strong, hard-to-guess passwords and make sure your systems actually enforce the rule."
        ),
        "fr": (
            "Ce contrôle porte sur la robustesse des mots de passe. Le mot de passe reste la serrure de la porte d'entrée, "
            "et un mot de passe faible se crochète en un instant. L'objectif est simple : des mots de passe difficiles à "
            "deviner et à réutiliser. Les pirates utilisent des outils qui testent des millions de combinaisons par "
            "seconde — « ete2024 » ne tiendra pas. Pour vous conformer, exigez une longueur minimale et un mélange de types "
            "de caractères à la création, et un vrai changement à la mise à jour. Mieux encore, ajoutez l'authentification "
            "multifacteur pour qu'un mot de passe volé ne suffise pas. L'auditeur cherchera votre politique de mots de "
            "passe et la preuve que les systèmes l'appliquent réellement.\n"
            "Point clé : Exigez des mots de passe forts et assurez-vous que vos systèmes appliquent vraiment la règle."
        ),
    },
    "CM.2.061": {
        "en": (
            "Let's talk about baseline configurations. A baseline is simply a known-good, secure setup for a type of system "
            "— like a recipe you follow every time so every dish comes out the same. Without one, every laptop and server "
            "is configured a little differently, security settings drift, and weaknesses creep in unnoticed. This control "
            "asks you to define that secure standard for each type of system, keep an inventory of what you have, and build "
            "new systems from the baseline. It matters because consistent, documented configurations are far easier to "
            "secure, monitor, and recover. To comply, document your baselines, keep an up-to-date asset inventory, and "
            "track changes. An auditor will look for the baseline documents and the inventory.\n"
            "Key takeaway: Define a secure standard configuration for each system type and keep an inventory of what you run."
        ),
        "fr": (
            "Parlons des configurations de référence. Une configuration de référence, c'est tout simplement un réglage "
            "sécurisé et reconnu pour un type de système — comme une recette qu'on suit à chaque fois pour un résultat "
            "constant. Sans elle, chaque poste et serveur est réglé un peu différemment, les paramètres de sécurité "
            "dérivent et des failles s'installent sans qu'on le voie. Ce contrôle demande de définir ce standard sécurisé "
            "pour chaque type de système, de tenir un inventaire de votre parc, et de déployer les nouveaux systèmes à "
            "partir de la référence. C'est important car des configurations cohérentes et documentées sont bien plus "
            "faciles à sécuriser, surveiller et restaurer. Pour vous conformer, documentez vos références, tenez un "
            "inventaire à jour et suivez les changements. L'auditeur cherchera ces documents et l'inventaire.\n"
            "Point clé : Définissez une configuration standard sécurisée par type de système et tenez un inventaire."
        ),
    },
    "IR.2.092": {
        "en": (
            "This control is about handling security incidents properly. An incident is any event that could harm your "
            "systems or data — malware, a lost laptop, a suspicious login. Things will go wrong eventually; what matters is "
            "that you notice, write it down, and tell the right people. Think of a fire: detecting it early and calling for "
            "help makes all the difference. This control asks you to track incidents, document what happened and what you "
            "did, and report them to the designated people or authorities. It matters because a quick, organized response "
            "limits damage and meets legal obligations. To comply, keep an incident log and a simple response procedure. An "
            "auditor will look for that procedure and records of real incidents and how they were handled.\n"
            "Key takeaway: Detect, record, and report security incidents to the right people, every time."
        ),
        "fr": (
            "Ce contrôle porte sur la bonne gestion des incidents de sécurité. Un incident, c'est tout événement pouvant "
            "nuire à vos systèmes ou données — un logiciel malveillant, un portable perdu, une connexion suspecte. Des "
            "problèmes surviendront tôt ou tard ; l'important est de les remarquer, de les consigner et d'avertir les "
            "bonnes personnes. Comme pour un incendie : détecter tôt et appeler à l'aide change tout. Ce contrôle demande "
            "de suivre les incidents, de documenter ce qui s'est passé et ce que vous avez fait, et de les signaler aux "
            "personnes ou autorités désignées. C'est important car une réponse rapide et organisée limite les dégâts et "
            "respecte vos obligations. Pour vous conformer, tenez un journal des incidents et une procédure simple. "
            "L'auditeur cherchera cette procédure et les enregistrements des incidents réels.\n"
            "Point clé : Détectez, consignez et signalez les incidents de sécurité aux bonnes personnes, à chaque fois."
        ),
    },
    "AU.2.041": {
        "en": (
            "Let's look at traceability — being able to tie actions on your systems back to the person who did them. Think "
            "of security-camera footage: if something goes missing, you can review who was there and when. In your systems, "
            "that footage is your logs. This control requires that individual users' actions can be uniquely traced, so you "
            "have accountability and can investigate problems. It matters because without good logs, a breach is invisible "
            "and you can't prove what happened — to yourself or an auditor. To comply, turn on logging across important "
            "systems, make sure each entry records who did what and when, and protect those logs from tampering. An auditor "
            "will look for log settings and sample logs that clearly attribute actions to individuals.\n"
            "Key takeaway: Log who did what and when, so every action can be traced to a specific person."
        ),
        "fr": (
            "Parlons de traçabilité — pouvoir relier les actions sur vos systèmes à la personne qui les a faites. Pensez "
            "aux images de vidéosurveillance : si quelque chose disparaît, vous pouvez revoir qui était là et quand. Dans "
            "vos systèmes, ces images, ce sont vos journaux. Ce contrôle exige que les actions de chaque utilisateur "
            "puissent être tracées individuellement, pour assurer la responsabilité et permettre les enquêtes. C'est "
            "important car sans bons journaux, une intrusion est invisible et vous ne pouvez rien prouver — ni à vous, ni à "
            "un auditeur. Pour vous conformer, activez la journalisation sur les systèmes importants, veillez à ce que "
            "chaque entrée indique qui a fait quoi et quand, et protégez ces journaux contre toute altération. L'auditeur "
            "cherchera les réglages de journalisation et des exemples attribuant clairement les actions.\n"
            "Point clé : Journalisez qui a fait quoi et quand, pour que chaque action soit traçable à une personne précise."
        ),
    },
    "SI.1.210": {
        "en": (
            "This control is about fixing flaws — finding and patching weaknesses before attackers use them. Software has "
            "bugs, and some are security holes. Vendors release fixes, but a fix only protects you once you install it. "
            "Leaving systems unpatched is like knowing a window lock is broken and never repairing it. This control asks you "
            "to identify flaws, report them, and correct them in a timely way. It matters because most real-world attacks "
            "exploit known vulnerabilities that already had a patch available. To comply, keep systems and software "
            "updated, scan for vulnerabilities regularly, and have a process to apply important fixes quickly. An auditor "
            "will look for patch records, scan results, and a defined timeline for fixing serious issues.\n"
            "Key takeaway: Find and fix security flaws promptly — keep your systems patched and up to date."
        ),
        "fr": (
            "Ce contrôle porte sur la correction des failles — trouver et corriger les vulnérabilités avant que les pirates "
            "ne les exploitent. Les logiciels ont des bogues, et certains sont des failles de sécurité. Les éditeurs "
            "publient des correctifs, mais un correctif ne protège qu'une fois installé. Laisser des systèmes non corrigés, "
            "c'est comme savoir qu'un loquet de fenêtre est cassé sans jamais le réparer. Ce contrôle demande d'identifier "
            "les failles, de les signaler et de les corriger rapidement. C'est important car la plupart des attaques réelles "
            "exploitent des vulnérabilités connues pour lesquelles un correctif existait déjà. Pour vous conformer, gardez "
            "vos systèmes et logiciels à jour, recherchez régulièrement les vulnérabilités, et disposez d'un processus pour "
            "appliquer vite les correctifs importants. L'auditeur cherchera les enregistrements de correctifs et les "
            "résultats d'analyses.\n"
            "Point clé : Trouvez et corrigez rapidement les failles — gardez vos systèmes à jour."
        ),
    },
}


async def run():
    async with AsyncSessionLocal() as db:
        fw = (await db.execute(select(Framework).where(Framework.name == FRAMEWORK))).scalar_one_or_none()
        if not fw:
            print(f"Framework '{FRAMEWORK}' not found — nothing to do.")
            return
        updated = 0
        for ref, s in SCRIPTS.items():
            c = (await db.execute(
                select(Control).where(Control.framework_id == fw.id, Control.ref == ref)
            )).scalar_one_or_none()
            if not c:
                print(f"  (skip) control {ref} not found")
                continue
            c.video_script_en = aerate(s["en"])
            c.video_script_fr = aerate(s["fr"])
            updated += 1
        await db.commit()
        print(f"Seeded scripts for {updated} CMMC controls.")


if __name__ == "__main__":
    asyncio.run(run())
