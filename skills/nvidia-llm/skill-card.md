## Description: <br>
Routes prompts across 50+ NVIDIA NIM-hosted large language models with fallback, circuit breaking, latency tracking, subscription gating, WeChat payment, and invitation rewards. <br>

This skill is ready for commercial/non-commercial use. <br>

## Publisher: <br>
[yjkj999999](https://clawhub.ai/user/yjkj999999) <br>

### License/Terms of Use: <br>
MIT-0 <br>


## Use Case: <br>
Developers and agents use this skill to send chat and streaming prompts to NVIDIA-hosted LLM endpoints while automatically selecting scenario-specific models and falling back when requests fail. It is also used to inspect model health, manage local quota status, and run subscription-related CLI flows. <br>

### Deployment Geography for Use: <br>
Global <br>

## Known Risks and Mitigations: <br>
Risk: Prompts are sent from the local machine to NVIDIA-hosted model calls. <br>
Mitigation: Avoid sensitive prompts unless the deployment and data handling terms are acceptable for the intended use case. <br>
Risk: The artifact includes an undisclosed shared NVIDIA API key. <br>
Mitigation: Remove the hardcoded key and require each installation to provide its own NVIDIA_API_KEY before use. <br>
Risk: The skill uses local machine-bound license and usage files under the user's home directory. <br>
Mitigation: Review the local quota and license behavior before installing in managed, shared, or privacy-sensitive environments. <br>
Risk: Subscription payment is handled through an off-platform WeChat flow. <br>
Mitigation: Use the payment flow only when the publisher and off-platform payment process have been independently accepted by the user or organization. <br>


## Reference(s): <br>
- [ClawHub skill page](https://clawhub.ai/yjkj999999/skills/nvidia-llm) <br>
- [Publisher profile](https://clawhub.ai/user/yjkj999999) <br>
- [NVIDIA NIM API endpoint used by artifact](https://integrate.api.nvidia.com/v1) <br>


## Skill Output: <br>
**Output Type(s):** [text, markdown, code, shell commands, configuration, guidance] <br>
**Output Format:** [Python return values, streamed text chunks, and CLI text output] <br>
**Output Parameters:** [1D] <br>
**Other Properties Related to Output:** [May include selected model alias, model ID, latency, usage metadata, reasoning text, access status, and error details.] <br>

## Skill Version(s): <br>
1.1.0 (source: server release evidence, SKILL.md frontmatter, pyproject.toml) <br>

## Ethical Considerations: <br>
Users should evaluate whether this skill is appropriate for their environment, review any generated or modified files before relying on them, and apply their organization's safety, security, and compliance requirements before deployment. <br>
