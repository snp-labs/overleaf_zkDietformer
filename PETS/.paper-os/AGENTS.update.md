# paper-writing-os workspace additions

- If `.paper-os/paper_os_config.yaml` exists, read it before substantive manuscript work.
- Treat `.paper-os/claim_scope.md` as the authority for the paper's strongest claim and explicit non-claims.
- Treat `.paper-os/evidence_log.md` as the authority for numeric claims, benchmark references, and result source paths.
- Before editing the manuscript or bibliography paths named in `.paper-os/paper_os_config.yaml`, read `.paper-os/writing_status.md` and any relevant state file touched by the request (`outline.json`, `intro_related_work_plan.json`, `plotting_plan.json`, `illustration_plan.json`, `citation_map.json`, `review_audit.json`, `reviewer_feedback.json`, `worklog.json`).
- Treat `plotting_plan.json` as the figure-planning layer. Only use `illustration_plan.json` and explicit image generation when the user asks for `"그림 생성"` or `image_gen`.
- Treat `.paper-os/review_audit.json` as advisory reviewer/auditor findings; do not treat suggested experiments, citations, or baselines as verified evidence until they are checked against source files or external sources.
- Do not invent experiments, citations, or reviewer comments. If evidence is missing, record the gap in `.paper-os/writing_status.md` or `.paper-os/evidence_log.md`.
- After substantial paper-writing work, update `.paper-os/writing_status.md` with completed work, open risks, and next actions.
