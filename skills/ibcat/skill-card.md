## Description: <br>
IBCAT helps agents translate PDFs into layout-preserving bilingual side-by-side and monolingual Chinese PDF outputs using BabelDOC and an LLM translation bridge. <br>

This skill is ready for commercial/non-commercial use. <br>

## Publisher: <br>
[yjkj999999](https://clawhub.ai/user/yjkj999999) <br>

### License/Terms of Use: <br>
MIT <br>


## Use Case: <br>
Developers, translators, and document-processing teams use this skill to convert source PDFs into bilingual English/Chinese PDFs while preserving layout, extracting text segments for LLM translation, rendering translated PDFs, and verifying Chinese font output. <br>

### Deployment Geography for Use: <br>
Global <br>

## Known Risks and Mitigations: <br>
Risk: The skill persistently patches BabelDOC font and CMap security checks to support offline CJK font loading. <br>
Mitigation: Review the patching script before use, run it only in a disposable virtual environment or container, and avoid applying it to a shared Python installation. <br>
Risk: PDF text, segment files, translations, logs, and other work files may be saved in the configured work directory during translation. <br>
Mitigation: Use a dedicated isolated work directory, do not process confidential PDFs unless this storage is acceptable, and clean up work files after review. <br>
Risk: Cleanup and cache commands delete BabelDOC cache and work files, which can remove prior translation state. <br>
Mitigation: Back up important inputs and translation artifacts before running cleanup steps, and keep BabelDOC cache isolated from other workflows. <br>


## Reference(s): <br>
- [BabelDOC](https://github.com/funstory-ai/BabelDOC) <br>
- [pdfplumber](https://github.com/jsvine/pdfplumber) <br>
- [Noto CJK Fonts](https://github.com/notofonts/noto-cjk) <br>
- [ClawHub Skill Page](https://clawhub.ai/yjkj999999/skills/ibcat) <br>


## Skill Output: <br>
**Output Type(s):** [Markdown, Shell commands, Code, Configuration, Guidance, Files] <br>
**Output Format:** [Markdown guidance with shell commands, Python scripts, JSON work files, CSV glossary templates, and generated PDF files] <br>
**Output Parameters:** [1D] <br>
**Other Properties Related to Output:** [Produces intermediate segment and translation JSON files, logs, bilingual .dual.pdf output, monolingual .mono.pdf output, and PDF verification results.] <br>

## Skill Version(s): <br>
1.0.0 (source: release metadata and artifact documentation) <br>

## Ethical Considerations: <br>
Users should evaluate whether this skill is appropriate for their environment, review any generated or modified files before relying on them, and apply their organization's safety, security, and compliance requirements before deployment. <br>
