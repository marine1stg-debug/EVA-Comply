const fs = require("fs");
const {
  Document, Packer, Paragraph, TextRun, Table, TableRow, TableCell,
  Header, Footer, AlignmentType, LevelFormat, TableOfContents, HeadingLevel,
  BorderStyle, WidthType, ShadingType, PageNumber, PageBreak,
} = require("docx");

const SKY = "1A8FD1", DARK = "0D2A43", GREY = "5A6B7B", LINE = "CCCCCC";
const HEADFILL = "D5E8F0", SOFTFILL = "EEF6FB";
const CONTENT_W = 9360;
const border = { style: BorderStyle.SINGLE, size: 1, color: LINE };
const borders = { top: border, left: border, bottom: border, right: border };

// pick by language
function build(lang, includeAnnex, outName) {
  const L = (en, fr) => (lang === "fr" ? fr : en);

  function H1(t) { return new Paragraph({ heading: HeadingLevel.HEADING_1, children: [new TextRun(t)] }); }
  function H2(t) { return new Paragraph({ heading: HeadingLevel.HEADING_2, children: [new TextRun(t)] }); }
  function P(t, o = {}) { return new Paragraph({ spacing: { after: 140, line: 276 }, children: [new TextRun({ text: t, size: 22, ...o })] }); }
  function runs(ch, s = 140) { return new Paragraph({ spacing: { after: s, line: 276 }, children: ch }); }
  function bullet(t) { return new Paragraph({ numbering: { reference: "bullets", level: 0 }, spacing: { after: 60, line: 268 }, children: [new TextRun({ text: t, size: 22 })] }); }
  function bulletRuns(ch) { return new Paragraph({ numbering: { reference: "bullets", level: 0 }, spacing: { after: 60, line: 268 }, children: ch }); }
  function num(t) { return new Paragraph({ numbering: { reference: "steps", level: 0 }, spacing: { after: 80, line: 268 }, children: [new TextRun({ text: t, size: 22 })] }); }
  function mono(text) {
    const cb = { style: BorderStyle.SINGLE, size: 4, color: "D8E2EC" };
    const lines = String(text).split("\n");
    return new Table({
      width: { size: CONTENT_W, type: WidthType.DXA }, columnWidths: [CONTENT_W],
      rows: [new TableRow({ children: [new TableCell({
        borders: { top: cb, left: cb, bottom: cb, right: cb },
        shading: { fill: "F2F5F8", type: ShadingType.CLEAR },
        margins: { top: 100, bottom: 100, left: 160, right: 160 },
        width: { size: CONTENT_W, type: WidthType.DXA },
        children: lines.map(l => new Paragraph({ spacing: { after: 0, line: 264 }, children: [new TextRun({ text: l || " ", font: "Consolas", size: 20, color: DARK })] })),
      })] })],
    });
  }
  function cell(content, { w, fill, head = false, center = false } = {}) {
    const kids = Array.isArray(content) ? content : [content];
    return new TableCell({
      borders, width: { size: w, type: WidthType.DXA },
      shading: fill ? { fill, type: ShadingType.CLEAR } : undefined,
      margins: { top: 70, bottom: 70, left: 120, right: 120 },
      children: kids.map(t => new Paragraph({ alignment: center ? AlignmentType.CENTER : AlignmentType.LEFT, children: [new TextRun({ text: t, size: 20, bold: head, color: head ? DARK : undefined })] })),
    });
  }
  function table(widths, rows) {
    return new Table({
      width: { size: CONTENT_W, type: WidthType.DXA }, columnWidths: widths,
      rows: rows.map((r, i) => new TableRow({ tableHeader: i === 0, children: r.map((c, j) => cell(c.text, { w: widths[j], fill: i === 0 ? HEADFILL : c.fill, head: i === 0, center: c.center })) })),
    });
  }
  function callout(title, lines) {
    const kids = [
      new Paragraph({ spacing: { after: 60 }, children: [new TextRun({ text: title, bold: true, size: 22, color: DARK })] }),
      ...lines.map(l => new Paragraph({ spacing: { after: 40, line: 268 }, children: [new TextRun({ text: l, size: 21 })] })),
    ];
    return new Table({
      width: { size: CONTENT_W, type: WidthType.DXA }, columnWidths: [CONTENT_W],
      rows: [new TableRow({ children: [new TableCell({
        borders: { top: { style: BorderStyle.SINGLE, size: 1, color: "BBD9EC" }, left: { style: BorderStyle.SINGLE, size: 18, color: SKY }, bottom: { style: BorderStyle.SINGLE, size: 1, color: "BBD9EC" }, right: { style: BorderStyle.SINGLE, size: 1, color: "BBD9EC" } },
        shading: { fill: SOFTFILL, type: ShadingType.CLEAR },
        margins: { top: 120, bottom: 120, left: 200, right: 160 },
        width: { size: CONTENT_W, type: WidthType.DXA }, children: kids,
      })] })],
    });
  }

  const c = [];

  // Title
  c.push(
    new Paragraph({ spacing: { before: 1600, after: 0 }, children: [new TextRun({ text: "EVA Comply", bold: true, size: 30, color: SKY })] }),
    new Paragraph({ spacing: { before: 200, after: 0 }, children: [new TextRun({ text: L("How Maturity Is Calculated", "Comment la maturité est calculée"), bold: true, size: 48, color: DARK })] }),
    new Paragraph({ spacing: { before: 160, after: 0 }, children: [new TextRun({ text: L("A plain-language guide to your maturity score", "Un guide en langage clair de votre cote de maturité"), size: 25, color: GREY })] }),
    new Paragraph({ spacing: { before: 600 }, children: [new TextRun({ text: includeAnnex ? L("Internal / reviewer edition — includes the technical annex.", "Édition interne / réviseur — comprend l’annexe technique.") : L("Client edition.", "Édition client."), size: 20, italics: true, color: GREY })] }),
    new Paragraph({ spacing: { before: 120 }, children: [new TextRun({ text: L("Version 1.0  ·  June 2026", "Version 1.0  ·  Juin 2026"), size: 20, color: GREY })] }),
    new Paragraph({ children: [new PageBreak()] }),
  );

  // 1
  c.push(H1(L("1. The idea in one sentence", "1. L’idée en une phrase")));
  c.push(P(L(
    "Maturity answers a simple question for every area of a framework: how completely, and how reliably, are the required controls actually in place? We show it on a 0 to 5 scale, the same five-rung ladder used across cybersecurity maturity models, and we calculate it from real audit evidence rather than from opinion.",
    "La maturité répond à une question simple pour chaque domaine d’un cadre : à quel point les contrôles requis sont-ils réellement en place, de façon complète et fiable ? Nous l’exprimons sur une échelle de 0 à 5, la même échelle à cinq niveaux utilisée par les modèles de maturité en cybersécurité, et nous la calculons à partir de véritables preuves d’audit plutôt que d’une opinion.")));
  c.push(callout(L("The core principle", "Le principe de base"), [L(
    "Assessed maturity is earned, not entered. A domain’s score rises only as the controls inside it are verified by evidence. This keeps the number defensible: every point traces back to controls that were actually demonstrated.",
    "La maturité évaluée se mérite, elle ne se saisit pas. La cote d’un domaine augmente uniquement à mesure que ses contrôles sont vérifiés par des preuves. Le chiffre reste ainsi défendable : chaque point renvoie à des contrôles réellement démontrés.")]));

  // 2
  c.push(H1(L("2. The 0 to 5 maturity scale", "2. L’échelle de maturité de 0 à 5")));
  c.push(P(L("Every rating, whether assessed by EVA or perceived by you, sits on the same ladder, so the two can be compared directly on one chart.",
    "Chaque cote, qu’elle soit évaluée par EVA ou perçue par vous, repose sur la même échelle; les deux se comparent donc directement sur un même graphique.")));
  c.push(table([900, 2400, 6060], [
    [{ text: L("Level", "Niveau"), center: true }, { text: L("Name", "Nom") }, { text: L("What it means", "Ce que cela signifie") }],
    [{ text: "5", center: true }, { text: L("Optimized", "Optimisé") }, { text: L("Formal, organization-wide, and continuously improved; fully implemented across all systems and reviewed regularly.", "Formel, à l’échelle de l’organisation et amélioré en continu; entièrement mis en œuvre sur tous les systèmes et révisé régulièrement.") }],
    [{ text: "4", center: true }, { text: L("Managed", "Géré") }, { text: L("Implemented and monitored for critical systems; nearly complete, with only minor gaps.", "Mis en œuvre et surveillé pour les systèmes critiques; presque complet, avec seulement des lacunes mineures.") }],
    [{ text: "3", center: true }, { text: L("Defined", "Défini") }, { text: L("Documented and applied consistently for key systems and areas.", "Documenté et appliqué de façon cohérente pour les systèmes et domaines clés.") }],
    [{ text: "2", center: true }, { text: L("Initial", "Initial") }, { text: L("Informal or ad hoc; partial and inconsistent coverage.", "Informel ou ponctuel; couverture partielle et incohérente.") }],
    [{ text: "1", center: true }, { text: L("None", "Aucun") }, { text: L("No process or capability in place for this control.", "Aucun processus ni aucune capacité en place pour ce contrôle.") }],
    [{ text: "0", center: true }, { text: L("Not started", "Non amorcé"), fill: "F7F7F7" }, { text: L("Assessed value only: no control in this domain is verified yet.", "Valeur évaluée seulement : aucun contrôle de ce domaine n’est encore vérifié."), fill: "F7F7F7" }],
  ]));
  c.push(P(L("The default improvement Target is level 4 (Managed): solid, monitored coverage of what matters, a realistic and audit-ready objective for most organizations. Targets can be raised or lowered per domain.",
    "La cible d’amélioration par défaut est le niveau 4 (Géré) : une couverture solide et surveillée de l’essentiel, un objectif réaliste et prêt pour l’audit pour la plupart des organisations. Les cibles peuvent être relevées ou abaissées par domaine."), { italics: true }));

  // 3
  c.push(H1(L("3. The four numbers we track for each domain", "3. Les quatre chiffres suivis pour chaque domaine")));
  c.push(P(L("A framework (for example CMMC 2.0) is divided into domains (Access Control, Incident Response, and so on). For each domain we keep up to four readings, all on the same 0 to 5 scale:",
    "Un cadre (par exemple CMMC 2.0) est divisé en domaines (Contrôle d’accès, Réponse aux incidents, etc.). Pour chaque domaine, nous conservons jusqu’à quatre mesures, toutes sur la même échelle de 0 à 5 :")));
  c.push(bulletRuns([new TextRun({ text: L("Assessed (Current) ", "Évaluée (actuelle) "), bold: true, size: 22 }), new TextRun({ text: L("the evidence-based score EVA calculates from how many controls are verified. This is the headline maturity number.", "la cote fondée sur les preuves que EVA calcule selon le nombre de contrôles vérifiés. C’est le chiffre de maturité principal."), size: 22 })]));
  c.push(bulletRuns([new TextRun({ text: L("Perceived ", "Perçue "), bold: true, size: 22 }), new TextRun({ text: L("your own self-rating, captured through the maturity questionnaire. It shows how your organization sees itself.", "votre propre auto-évaluation, recueillie au moyen du questionnaire de maturité. Elle montre comment votre organisation se perçoit."), size: 22 })]));
  c.push(bulletRuns([new TextRun({ text: L("Target ", "Cible "), bold: true, size: 22 }), new TextRun({ text: L("where the domain should be (default level 4). The distance to target drives the risk score and the roadmap.", "où le domaine devrait se situer (niveau 4 par défaut). L’écart par rapport à la cible alimente le score de risque et la feuille de route."), size: 22 })]));
  c.push(bulletRuns([new TextRun({ text: L("Previous ", "Antérieure "), bold: true, size: 22 }), new TextRun({ text: L("the assessed level frozen at the last snapshot, so progress over time is visible.", "le niveau évalué figé lors du dernier instantané, pour visualiser les progrès dans le temps."), size: 22 })]));
  c.push(callout(L("Why both Assessed and Perceived?", "Pourquoi à la fois Évaluée et Perçue ?"), [L(
    "The gap between the two is one of the most useful signals. When an organization perceives itself well above its assessed score, it usually points to a blind spot, or to controls believed to be in place but not yet evidenced.",
    "L’écart entre les deux est l’un des signaux les plus utiles. Lorsqu’une organisation se perçoit bien au-dessus de sa cote évaluée, cela révèle souvent un angle mort, ou des contrôles que l’on croit en place mais qui ne sont pas encore prouvés.")]));

  // 4
  c.push(H1(L("4. How the Assessed (Current) level is calculated", "4. Comment le niveau Évalué (actuel) est calculé")));
  c.push(P(L("This is the heart of the method. For a given domain we look at every control you are subscribed to in that domain, and count how many are compliant.",
    "C’est le cœur de la méthode. Pour un domaine donné, nous examinons chaque contrôle auquel vous êtes abonné dans ce domaine et comptons combien sont conformes.")));
  c.push(H2(L("Step 1 — When is a control \"compliant\"?", "Étape 1 — Quand un contrôle est-il « conforme » ?")));
  c.push(P(L("A control becomes compliant when its required evidence is in and accepted: all of its expected evidence items are accepted and none have been sent back for rework. A reviewer can also confirm a control’s status manually (for example, accepting a compensating control). In short, compliant means demonstrated, not merely claimed.",
    "Un contrôle devient conforme lorsque ses preuves requises sont reçues et acceptées : tous ses éléments de preuve attendus sont acceptés et aucun n’a été retourné pour correction. Un réviseur peut aussi confirmer le statut d’un contrôle manuellement (par exemple, accepter un contrôle compensatoire). Bref, conforme veut dire démontré, et non simplement déclaré.")));
  c.push(H2(L("Step 2 — Convert the compliance ratio to a 0 to 5 level", "Étape 2 — Convertir le taux de conformité en niveau de 0 à 5")));
  c.push(P(L("Within the domain we take the share of controls that are compliant and place it on the 0 to 5 scale:",
    "Dans le domaine, nous prenons la proportion de contrôles conformes et la plaçons sur l’échelle de 0 à 5 :")));
  c.push(mono(L("domain level = round( compliant controls / total controls × 5 )",
    "niveau du domaine = arrondi( contrôles conformes / total des contrôles × 5 )")));
  c.push(P(L("So a domain where 8 of 10 controls are verified scores round(0.8 × 5) = 4 (Managed). A domain with nothing verified scores 0; everything verified scores 5.",
    "Ainsi, un domaine où 8 contrôles sur 10 sont vérifiés obtient arrondi(0,8 × 5) = 4 (Géré). Un domaine sans aucun contrôle vérifié obtient 0; tout vérifié donne 5.")));
  c.push(table([3120, 3120, 3120], [
    [{ text: L("Compliant in domain", "Conformes dans le domaine"), center: true }, { text: L("Ratio", "Taux"), center: true }, { text: L("Assessed level", "Niveau évalué"), center: true }],
    [{ text: L("0 of 12", "0 sur 12"), center: true }, { text: "0%", center: true }, { text: "0", center: true }],
    [{ text: L("3 of 12", "3 sur 12"), center: true }, { text: "25%", center: true }, { text: "1", center: true }],
    [{ text: L("6 of 12", "6 sur 12"), center: true }, { text: "50%", center: true }, { text: "3", center: true }],
    [{ text: L("9 of 12", "9 sur 12"), center: true }, { text: "75%", center: true }, { text: "4", center: true }],
    [{ text: L("12 of 12", "12 sur 12"), center: true }, { text: "100%", center: true }, { text: "5", center: true }],
  ]));
  c.push(P(L("This value updates on its own as evidence is accepted, so the maturity picture stays current without anyone re-scoring it by hand. An EVA or MSP reviewer can also adjust a domain’s level or its target when expert judgment calls for it, and any such adjustment is clearly flagged.",
    "Cette valeur se met à jour d’elle-même à mesure que les preuves sont acceptées : le portrait de maturité reste donc à jour sans qu’on ait à le recalculer manuellement. Un réviseur EVA ou IGS peut aussi ajuster le niveau d’un domaine ou sa cible lorsque le jugement d’expert le justifie, et tout ajustement de ce type est clairement indiqué."), { italics: true }));

  // 5 perceived
  c.push(H1(L("5. How the Perceived level is calculated", "5. Comment le niveau Perçu est calculé")));
  c.push(P(L("Perceived maturity comes from your answers to the maturity questionnaire. Each control carries a question whose five answer choices map exactly onto the 0 to 5 ladder (None through Optimized). The perceived level for a domain is simply the average of the levels you selected for the controls in that domain.",
    "La maturité perçue provient de vos réponses au questionnaire de maturité. Chaque contrôle comporte une question dont les cinq choix de réponse correspondent exactement à l’échelle de 0 à 5 (d’Aucun à Optimisé). Le niveau perçu d’un domaine est simplement la moyenne des niveaux que vous avez choisis pour les contrôles de ce domaine.")));
  c.push(P(L("Only answered controls count; unanswered ones are ignored rather than treated as zero, so a partially completed self-assessment is not unfairly penalized.",
    "Seuls les contrôles auxquels vous avez répondu comptent; les autres sont ignorés plutôt que comptés comme zéro, afin qu’une auto-évaluation partielle ne soit pas pénalisée injustement.")));

  // 6 risk
  c.push(H1(L("6. The risk score", "6. Le score de risque")));
  c.push(P(L("Maturity tells you where you are; the risk score tells you how much the remaining gap matters. It weights each domain’s shortfall by the severity of the controls in it, because falling short on a critical domain is not the same as falling short on a low-risk one.",
    "La maturité indique où vous en êtes; le score de risque indique l’importance de l’écart qui reste. Il pondère le déficit de chaque domaine selon la sévérité de ses contrôles, car être en deçà de la cible dans un domaine critique n’équivaut pas à l’être dans un domaine à faible risque.")));
  c.push(P(L("Each domain takes the highest severity it contains (Critical = 4, High = 3, Medium = 2, Low = 1) as its weight, and its gap is how far it sits below target (never negative). The framework risk score combines every domain’s weighted gap into a single 0 to 100% figure: 0% means every domain has reached its target; higher values flag concentrations of high-severity, low-maturity domains.",
    "Chaque domaine prend comme poids la sévérité la plus élevée qu’il contient (Critique = 4, Élevée = 3, Moyenne = 2, Faible = 1), et son écart correspond à la distance sous la cible (jamais négative). Le score de risque du cadre combine l’écart pondéré de chaque domaine en un seul pourcentage de 0 à 100 % : 0 % signifie que chaque domaine a atteint sa cible; une valeur plus élevée signale une concentration de domaines à sévérité élevée et à faible maturité.")));
  c.push(mono(L("risk score (%) = round( Σ (gap × weight) / Σ (4 × weight) × 100 )",
    "score de risque (%) = arrondi( Σ (écart × poids) / Σ (4 × poids) × 100 )")));

  // 7 rollups
  c.push(H1(L("7. From domain to framework to organization", "7. Du domaine au cadre à l’organisation")));
  c.push(P(L("The scores aggregate in three layers, each a clear average:", "Les cotes s’agrègent en trois couches, chacune une moyenne simple :")));
  c.push(num(L("Domain level — calculated from the compliance ratio (section 4).", "Niveau du domaine — calculé à partir du taux de conformité (section 4).")));
  c.push(num(L("Framework overall — the average of its domain levels.", "Cadre global — la moyenne des niveaux de ses domaines.")));
  c.push(num(L("Organization overall — the average across every framework you are subscribed to. The organization-level gap is Perceived minus Assessed.", "Organisation globale — la moyenne de tous les cadres auxquels vous êtes abonné. L’écart au niveau de l’organisation est Perçue moins Évaluée.")));

  // 8 snapshots
  c.push(H1(L("8. Tracking progress over time", "8. Suivre les progrès dans le temps")));
  c.push(P(L("A reviewer can take a dated snapshot of a framework, which freezes each domain’s current level as a labeled baseline. From then on, the platform shows that baseline as the Previous series next to the live Current value, so improvement since the last review is visible at a glance.",
    "Un réviseur peut prendre un instantané daté d’un cadre, qui fige le niveau actuel de chaque domaine comme référence étiquetée. Par la suite, la plateforme affiche cette référence comme série Antérieure à côté de la valeur Actuelle en direct, de sorte que les progrès depuis la dernière revue sont visibles d’un coup d’œil.")));

  // 9 worked example
  c.push(H1(L("9. Worked example", "9. Exemple concret")));
  c.push(P(L("Consider a CMMC 2.0 assessment with three domains:", "Prenons une évaluation CMMC 2.0 comportant trois domaines :")));
  c.push(table([2760, 1650, 1650, 1650, 1650], [
    [{ text: L("Domain", "Domaine") }, { text: L("Verified", "Vérifiés"), center: true }, { text: L("Assessed", "Évaluée"), center: true }, { text: L("Target", "Cible"), center: true }, { text: L("Severity", "Sévérité"), center: true }],
    [{ text: L("Access Control", "Contrôle d’accès") }, { text: L("9 / 12", "9 / 12"), center: true }, { text: "4", center: true }, { text: "4", center: true }, { text: L("Critical", "Critique"), center: true }],
    [{ text: L("Incident Response", "Réponse aux incidents") }, { text: "3 / 10", center: true }, { text: "2", center: true }, { text: "4", center: true }, { text: L("High", "Élevée"), center: true }],
    [{ text: L("Awareness & Training", "Sensibilisation et formation") }, { text: "5 / 8", center: true }, { text: "3", center: true }, { text: "4", center: true }, { text: L("Low", "Faible"), center: true }],
  ]));
  c.push(P(L("Framework overall Assessed = average(4, 2, 3) = 3.0, against a Target of 4.0.",
    "Évaluée globale du cadre = moyenne(4, 2, 3) = 3,0, pour une cible de 4,0.")));
  c.push(runs([new TextRun({ text: L("Weighted gaps: Access Control 0×4 = 0; Incident Response 2×3 = 6; Awareness 1×1 = 1. Risk score = round((0+6+1) / (4×(4+3+1)) × 100) = ",
    "Écarts pondérés : Contrôle d’accès 0×4 = 0; Réponse aux incidents 2×3 = 6; Sensibilisation 1×1 = 1. Score de risque = arrondi((0+6+1) / (4×(4+3+1)) × 100) = "), size: 22 }),
    new TextRun({ text: "22%", bold: true, size: 22, color: DARK }), new TextRun({ text: ".", size: 22 })]));
  c.push(P(L("The reading: overall maturity is solid at 3.0 of 5, but the residual risk concentrates in Incident Response, a high-severity domain still well below target. That is where the roadmap should focus next.",
    "Lecture : la maturité globale est solide à 3,0 sur 5, mais le risque résiduel se concentre dans la Réponse aux incidents, un domaine à sévérité élevée encore bien sous la cible. C’est là que la feuille de route devrait se concentrer ensuite."), { italics: true }));

  // 10 why
  c.push(H1(L("10. Why this approach", "10. Pourquoi cette approche")));
  const why = [
    [L("Evidence-driven and defensible. ", "Fondée sur les preuves et défendable. "), L("The assessed score moves only when controls are verified, so it stands up to external audit scrutiny.", "La cote évaluée ne bouge que lorsque les contrôles sont vérifiés; elle résiste donc à l’examen d’un audit externe.")],
    [L("Standard and familiar. ", "Standard et familière. "), L("The 0 to 5 ladder mirrors widely used maturity models, so it is easy to understand.", "L’échelle de 0 à 5 reprend des modèles de maturité largement utilisés; elle est donc facile à comprendre.")],
    [L("Self-maintaining. ", "Auto-entretenue. "), L("Because the score derives from evidence, the maturity picture stays current with no manual re-scoring.", "Comme la cote découle des preuves, le portrait de maturité reste à jour sans recalcul manuel.")],
    [L("Risk-aware. ", "Axée sur le risque. "), L("Severity weighting sends attention to the gaps that carry real exposure.", "La pondération par sévérité dirige l’attention vers les écarts qui présentent une exposition réelle.")],
    [L("Honest about perception. ", "Honnête sur la perception. "), L("Tracking perceived alongside assessed reveals blind spots a single number would hide.", "Suivre la perçue en parallèle de l’évaluée révèle des angles morts qu’un seul chiffre masquerait.")],
  ];
  why.forEach(([b, t]) => c.push(bulletRuns([new TextRun({ text: b, bold: true, size: 22 }), new TextRun({ text: t, size: 22 })])));

  // ── Annex (admin only) ──
  if (includeAnnex) {
    c.push(new Paragraph({ children: [new PageBreak()] }));
    c.push(H1(L("Technical annex", "Annexe technique")));
    c.push(P(L("For the internal team. Exact formulas, data fields, edge cases, and what is configurable. Reflects the implementation in the maturity service.",
      "Pour l’équipe interne. Formules exactes, champs de données, cas limites et éléments paramétrables. Reflète l’implémentation du service de maturité."), { italics: true }));

    c.push(H2(L("A. Inputs and data sources", "A. Entrées et sources de données")));
    c.push(table([3000, 6360], [
      [{ text: L("Source", "Source") }, { text: L("Role in the calculation", "Rôle dans le calcul") }],
      [{ text: "Control.domain" }, { text: L("Groups controls into domains. Null domain falls back to the label \"General\".", "Regroupe les contrôles en domaines. Un domaine nul retombe sur l’étiquette « General ».") }],
      [{ text: "Control.risk_rating" }, { text: L("low / medium / high / critical, mapped to weights 1 / 2 / 3 / 4.", "low / medium / high / critical, associés aux poids 1 / 2 / 3 / 4.") }],
      [{ text: "OrgControl.audit_status" }, { text: L("Per client-control status. \"compliant\" counts toward the assessed level. Auto-derived from evidence, or pinned via manual status mode.", "Statut par contrôle-client. « compliant » compte dans le niveau évalué. Dérivé automatiquement des preuves, ou fixé via le mode de statut manuel.") }],
      [{ text: "SelfAssessment.answers" }, { text: L("The client’s questionnaire answers; numeric levels 1-5 per control feed the perceived score.", "Les réponses du client au questionnaire; des niveaux 1 à 5 par contrôle alimentent la cote perçue.") }],
      [{ text: "MaturityAssessment" }, { text: L("Per domain reviewer overrides: current_level, target_level, note.", "Substitutions par domaine du réviseur : current_level, target_level, note.") }],
      [{ text: "MaturitySnapshot" }, { text: L("Frozen per-domain levels (payload) plus taken_at; latest one supplies the Previous series.", "Niveaux par domaine figés (payload) et taken_at; le plus récent fournit la série Antérieure.") }],
    ]));

    c.push(H2(L("B. Exact formulas", "B. Formules exactes")));
    c.push(P(L("Assessed level for a domain (auto):", "Niveau évalué d’un domaine (auto) :")));
    c.push(mono("auto = 0 if total == 0 else round(compliant / total * 5)"));
    c.push(P(L("compliant = controls in the domain with audit_status == \"compliant\"; total = subscribed controls in the domain.",
      "compliant = contrôles du domaine avec audit_status == « compliant »; total = contrôles abonnés du domaine.")));
    c.push(P(L("Effective current and target per domain:", "Actuel et cible effectifs par domaine :")));
    c.push(mono("current = override.current_level if set else auto\ntarget  = override.target_level  if set else 4   # DEFAULT_TARGET"));
    c.push(P(L("Compliant auto-derivation (evidence layer):", "Dérivation automatique de la conformité (couche preuves) :")));
    c.push(mono("audit_status = \"compliant\" if (total_evidence > 0\n               and accepted == total_evidence\n               and no item returned)\n               else \"in_progress\"   # unless manually pinned"));
    c.push(P(L("Perceived:", "Perçue :")));
    c.push(mono("perceived(control)  = mean of answered question levels (1-5)\nperceived(domain)   = round(mean of its control perceived values, 1)\nperceived(overall)  = round(mean over ALL answered controls, 1)"));
    c.push(P(L("Risk (per framework):", "Risque (par cadre) :")));
    c.push(mono("weight(domain) = max risk weight among its controls (default 1)\ngap(domain)    = max(0, target - current)\nrisk_score     = round( Σ(gap*weight) / Σ(4*weight) * 100 )  # 0 if denom 0"));
    c.push(P(L("Roll-ups:", "Agrégations :")));
    c.push(mono("framework.current  = round(mean of domain currents, 1)\nframework.target   = round(mean of domain targets, 1)\nframework.previous = round(mean of domain previous, 1)  # current if no snapshot value\norg.assessed       = round(mean of framework currents, 1)\norg.perceived      = round(mean of framework perceived, 1)\norg.gap            = round(perceived - assessed, 1)"));

    c.push(H2(L("C. Edge cases and conventions", "C. Cas limites et conventions")));
    [L("Empty domain (total == 0): assessed level is 0.", "Domaine vide (total == 0) : niveau évalué de 0."),
     L("Perceived with no answers: returns null (not 0); excluded from averages so partial questionnaires are not penalized.", "Perçue sans réponse : retourne null (pas 0); exclue des moyennes pour ne pas pénaliser les questionnaires partiels."),
     L("Previous series: if a domain has no value in the latest snapshot, its current value is used in the previous-average; overall previous is null when no snapshot exists at all.", "Série antérieure : si un domaine n’a pas de valeur dans le dernier instantané, sa valeur actuelle sert dans la moyenne antérieure; l’antérieure globale est null s’il n’existe aucun instantané."),
     L("Risk denominator uses the fixed DEFAULT_TARGET of 4, not the per-domain target override, so the 0-100% scale stays comparable even when targets are customized.", "Le dénominateur du risque utilise la valeur fixe DEFAULT_TARGET de 4, et non la cible substituée par domaine, afin que l’échelle de 0 à 100 % reste comparable même avec des cibles personnalisées."),
     L("Domain risk weight defaults to 1 (low) if a control’s risk rating is missing.", "Le poids de risque du domaine vaut 1 (faible) par défaut si la cote de risque d’un contrôle est absente."),
     L("Level bounds: overrides are validated to 0-5; ladder labels run 1 (None) to 5 (Optimized), with 0 reserved for an un-started assessed domain.", "Bornes des niveaux : les substitutions sont validées de 0 à 5; les étiquettes vont de 1 (Aucun) à 5 (Optimisé), 0 étant réservé à un domaine évalué non amorcé."),
    ].forEach(t => c.push(bullet(t)));

    c.push(H2(L("D. What is configurable", "D. Éléments paramétrables")));
    c.push(table([3400, 5960], [
      [{ text: L("Item", "Élément") }, { text: L("How / who", "Comment / qui") }],
      [{ text: L("Current level (per domain)", "Niveau actuel (par domaine)") }, { text: L("Reviewer override; clear to revert to auto. Roles: Super Admin, EVA Auditor, MSP Admin, MSP Analyst.", "Substitution par le réviseur; effacer pour revenir à l’auto. Rôles : Super Admin, Auditeur EVA, Admin IGS, Analyste IGS.") }],
      [{ text: L("Target level (per domain)", "Niveau cible (par domaine)") }, { text: L("Reviewer-set, 0-5; defaults to 4 when unset.", "Défini par le réviseur, 0 à 5; valeur par défaut de 4 si non défini.") }],
      [{ text: L("Domain note", "Note de domaine") }, { text: L("Free-text rationale attached to an override.", "Justification en texte libre jointe à une substitution.") }],
      [{ text: L("Snapshots / baseline", "Instantanés / référence") }, { text: L("Reviewer takes a dated, optionally labeled snapshot to set the Previous series.", "Le réviseur prend un instantané daté, éventuellement étiqueté, pour définir la série Antérieure.") }],
      [{ text: L("Self-assessment questions", "Questions d’auto-évaluation") }, { text: L("Default is one generated 5-rung ladder question per control; authored, control-specific sets take precedence when present.", "Par défaut, une question d’échelle à 5 niveaux générée par contrôle; des jeux rédigés propres à un contrôle ont préséance lorsqu’ils existent.") }],
      [{ text: L("Control severity & domain", "Sévérité et domaine du contrôle") }, { text: L("Defined in the framework catalog; drives risk weight and grouping.", "Définis dans le catalogue du cadre; déterminent le poids de risque et le regroupement.") }],
    ]));
    c.push(P(L("Not configurable by design: the compliance-to-level formula, the risk normalization base (4), and the requirement that a control be fully evidenced to count as compliant. These are fixed to keep assessed maturity consistent and auditable across all clients.",
      "Non paramétrables par conception : la formule conformité-vers-niveau, la base de normalisation du risque (4) et l’exigence qu’un contrôle soit entièrement prouvé pour compter comme conforme. Ces éléments sont fixes afin que la maturité évaluée reste cohérente et auditable pour tous les clients."), { italics: true }));
  }

  const headerTxt = L("EVA Comply  ·  How Maturity Is Calculated", "EVA Comply  ·  Comment la maturité est calculée");
  const doc = new Document({
    creator: "EVA Comply",
    title: headerTxt,
    styles: {
      default: { document: { run: { font: "Arial", size: 22, color: "1F2933" } } },
      paragraphStyles: [
        { id: "Heading1", name: "Heading 1", basedOn: "Normal", next: "Normal", quickFormat: true,
          run: { size: 30, bold: true, font: "Arial", color: DARK },
          paragraph: { spacing: { before: 320, after: 160 }, outlineLevel: 0, border: { bottom: { style: BorderStyle.SINGLE, size: 6, color: SKY, space: 4 } } } },
        { id: "Heading2", name: "Heading 2", basedOn: "Normal", next: "Normal", quickFormat: true,
          run: { size: 25, bold: true, font: "Arial", color: SKY }, paragraph: { spacing: { before: 220, after: 100 }, outlineLevel: 1 } },
      ],
    },
    numbering: { config: [
      { reference: "bullets", levels: [{ level: 0, format: LevelFormat.BULLET, text: "•", alignment: AlignmentType.LEFT, style: { paragraph: { indent: { left: 540, hanging: 280 } } } }] },
      { reference: "steps", levels: [{ level: 0, format: LevelFormat.DECIMAL, text: "%1.", alignment: AlignmentType.LEFT, style: { paragraph: { indent: { left: 540, hanging: 300 } } } }] },
    ] },
    sections: [{
      properties: { page: { size: { width: 12240, height: 15840 }, margin: { top: 1440, right: 1440, bottom: 1440, left: 1440 } } },
      headers: { default: new Header({ children: [new Paragraph({ alignment: AlignmentType.RIGHT, border: { bottom: { style: BorderStyle.SINGLE, size: 4, color: "D8E2EC", space: 4 } }, children: [new TextRun({ text: headerTxt, size: 16, color: GREY })] })] }) },
      footers: { default: new Footer({ children: [new Paragraph({ alignment: AlignmentType.CENTER, children: [new TextRun({ text: L("Page ", "Page "), size: 16, color: GREY }), new TextRun({ children: [PageNumber.CURRENT], size: 16, color: GREY })] })] }) },
      children: c,
    }],
  });

  return Packer.toBuffer(doc).then(buffer => { fs.writeFileSync(outName, buffer); console.log("written", outName); });
}

(async () => {
  await build("en", false, "maturity_how_it_works_client_en.docx");
  await build("fr", false, "maturity_how_it_works_client_fr.docx");
  await build("en", true, "maturity_how_it_works_admin_en.docx");
  await build("fr", true, "maturity_how_it_works_admin_fr.docx");
})();
