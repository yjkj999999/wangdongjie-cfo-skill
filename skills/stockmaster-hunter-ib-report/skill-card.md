## Description:

Generates bilingual English and Chinese A-share investment research reports with fundamental analysis, technical breakout analysis, valuation scenarios, charts, HTML, and PDF outputs.

This skill is ready for commercial/non-commercial use.

## Publisher:

[yjkj999999](https://clawhub.ai/user/yjkj999999)

### License/Terms of Use:

MIT-0

## Use Case:

External users and analysts use this skill to produce structured A-share company research reports from a stock code or company name, including market data collection, technical analysis, valuation framing, risk review, and report packaging.

### Deployment Geography for Use:

Global

## Known Risks and Mitigations:

Risk: Generated investment reports may include sensitive portfolio or position details in persistent local files or public upload links.

Mitigation: Keep delivery local-only unless the user explicitly requests public links, and avoid including sensitive portfolio details in prompts or generated artifacts.

Risk: The skill can produce directive trading guidance based on market data and technical rules.

Mitigation: Review outputs as informational analysis, require source citations for financial data, and preserve disclaimers that the report is not investment advice.

Risk: The security verdict is suspicious despite no discrete risk findings.

Mitigation: Review the skill before installation and confirm that report generation, file persistence, and any upload delivery behavior are acceptable for the intended environment.

## Reference(s):

- [Report Structure Template](artifact/references/report_structure.md)
- [Wu Zhaohui Breakout Point Technical System](artifact/references/technical_analysis.md)
- [Valuation Framework](artifact/references/valuation_framework.md)
- [ClawHub Skill Page](https://clawhub.ai/yjkj999999/skills/stockmaster-hunter-ib-report)
- [Publisher Profile](https://clawhub.ai/user/yjkj999999)

## Skill Output:

**Output Type(s):** [text, markdown, code, shell commands, configuration, guidance, files]

**Output Format:** [Markdown guidance plus generated PNG charts, HTML reports, and PDF reports]

**Output Parameters:** [1D]

**Other Properties Related to Output:** [May save persistent local report artifacts and can deliver generated report assets through public URLs when the user requests upload delivery.]

## Skill Version(s):

1.0.0 (source: evidence.release.version)

## Ethical Considerations:

Users should evaluate whether this skill is appropriate for their environment, review any generated or modified files before relying on them, and apply their organization's safety, security, and compliance requirements before deployment.
