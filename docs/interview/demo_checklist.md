# Interview-day checklist and fallback

## Before the interview

- [ ] Read the measured health report and known limitations; distinguish current evidence from historical phase results.
- [ ] Run the TEST workflow and relevant checks using docs/reproduce.md; run DEV only with the authorized local workbook/models.
- [ ] Open the stable local PBIP, refresh and save; confirm Executive Overview contains 1,439 customers before introducing filters.
- [ ] Test country/segment selection, reset, page navigation and drill-through. Native numeric checks do not prove these interactions.
- [ ] Check synthetic banners and screenshot provenance. Avoid customer-level identifiers and do not describe an earlier capture as the final report.
- [ ] Open the simplified architecture, computed experiment figure, KPI definitions and payroll business case.
- [ ] Open the local repository/README in advance. Remote repository settings or publication have not been changed.
- [ ] Rehearse the 60-second pitch, five-minute sequence, ML baseline explanation and one STAR story.
- [ ] Prepare to explain “below planned sample” and “guardrail failure” without claiming commercial impact.

## If Desktop does not work

Use portfolio/interview/README.md as the entry point. Show the earlier native executive capture with its label, then the computed synthetic experiment chart and aggregate KPI snapshot. Explain the simplified architecture and payroll case from Markdown. Offline model metrics remain available in the model summary; no live MLflow or network connection is required for the story.

Do not spend the interview repairing software. Say: “The local numeric validation is recorded; this capture is from an earlier verified page. I can explain the pipeline and decision evidence from the offline pack.” Be candid that final Desktop visual/cache acceptance is a distinct check.

## Fix an empty local PBIP

The tracked PBIP is a portable definition with empty data-path parameters. A freshly prepared project can also lack imported data until Refresh. Run `python -m tools.prepare_powerbi`, then open `powerbi/.local/BankingCustomerAnalytics.pbip`. Preparation now restores a saved cache only when data paths, table names and measure names match. Otherwise use **Home → Refresh**, then **Ctrl+S**. Close and reopen after an external cache copy; Desktop does not reload that file into an already open project.

[Microsoft cache behavior](https://learn.microsoft.com/en-us/power-bi/developer/projects/projects-dataset/) explains why the model/report can open without imported data. If refresh fails, record the actual error before changing paths or permissions. Never disable privacy/security controls merely to make a demo load.
