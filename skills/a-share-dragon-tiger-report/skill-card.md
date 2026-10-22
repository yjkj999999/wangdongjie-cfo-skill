## Description:

Generates A-share limit-up and Dragon-Tiger research reports with a four-layer L1 to L2.5 to L3 screening funnel, wealth-password strategy scoring, and report outputs. Ships two interchangeable layouts sharing one calculation core: style A (classic, single-column A4 portrait, ECharts, HTML/PDF/PPTX) and style B (bii, BlackRock-style two-column A4 landscape with left text column and right chart column, inlined Chart.js, HTML/PDF, 14 pages). Style B is the daily default and is self-contained: its final page renders five next-day falsifiable predictions (each with an explicit claim plus a falsification threshold) so the same document can be verified against the following trading day without a second report.

This skill is for research and development only.

## Publisher:

[yjkj999999](https://clawhub.ai/user/yjkj999999)

### License/Terms of Use:

MIT-0

## Use Case:

External users and developers use this skill to generate A-share Dragon-Tiger board reports, daily market reviews, four-layer screening results, strategy scoring tables, and risk-aware trading checklists. It is framed as education and research material and states that its outputs are not investment advice.

### Deployment Geography for Use:

Global

## Known Risks and Mitigations:

Risk: Rendered reports may include unsafe or unescaped content from JSON or upstream market snapshots.

Mitigation: Run in an isolated project or virtual environment and use only trusted data until HTML escaping and a restrictive browser configuration are added.

Risk: Generated PPTX output may contain sample or stale hardcoded data.

Mitigation: Verify report dates and source data manually before sharing or relying on generated PPTX files. PPTX is produced by style A only.

Risk: Style B launches a headless system browser (Chrome/Edge/Chromium) with a temporary profile to render and export PDFs.

Mitigation: The browser is started with an isolated temporary user-data-dir, is scoped to a local file:// document, and is terminated when the run ends. Run in an isolated project or virtual environment and use only trusted data.

Risk: Charts may render blank while the page still exports "successfully", producing a report that looks complete but has no visuals.

Mitigation: The bundled pipeline verifies chart ink coverage, per-page height against the real paper size, and that PDF page count equals the HTML section count before delivering. It refuses to export a PDF when any check fails.

Risk: A report section may render empty while every automated geometric check still passes (for example a table whose rows silently resolve to an empty list), producing a page that looks valid but carries no content.

Mitigation: Automated checks cover geometry only. After changing any page structure, visually spot-check the affected page of the exported PDF (render it to an image) before treating the run as complete.

Risk: Style B renders the next-day prediction page from a JSON contract supplied at generation time; malformed or wrong-day input could attach predictions to the wrong trading day.

Mitigation: The generator hard-validates the contract (exactly 5 items, each requiring both a claim and a falsification threshold) and exits without producing a page if validation fails. A mismatch between the prediction date and the report date raises a warning that must be reviewed.

Risk: Finance report outputs could be mistaken for actionable investment advice.

Mitigation: Keep the education/research disclaimer visible and review data freshness, assumptions, and risk controls before use.

## Reference(s):

- [ClawHub skill page](https://clawhub.ai/yjkj999999/skills/a-share-dragon-tiger-report)
- [Publisher profile](https://clawhub.ai/user/yjkj999999)
- [Project homepage](https://github.com/yjkj999999/a-share-dragon-tiger-strategy)
- [README](README.md)
- [Wealth Password Strategy Guide](docs/wealth-password-strategy.md)

## Skill Output:

**Output Type(s):** [Text, Markdown, Code, Shell commands, Configuration, Guidance, Files]

**Output Format:** [Markdown guidance with shell commands plus generated HTML, PDF, and PPTX report files]

**Output Parameters:** [1D]

**Other Properties Related to Output:** [Outputs may use local sample data when live market sources are unavailable; generated reports should display data date, source, and delay. Style A emits HTML/PDF/PPTX; style B emits HTML/PDF only. Both styles are self-contained and offline-openable. Style B is the daily default and includes a next-day falsifiable-prediction page; when no prediction data is supplied the page is rendered as an explicitly labelled placeholder rather than omitted.]

## Skill Version(s):

2.2.0 (source: server release evidence)

## Ethical Considerations:

Users should evaluate whether this skill is appropriate for their environment, review any generated or modified files before relying on them, and apply their organization's safety, security, and compliance requirements before deployment.
