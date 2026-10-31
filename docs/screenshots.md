# Screenshot plan and Power BI page catalog

Capture after refresh, verify the current total/filter selection, use a consistent canvas fit and keep synthetic labels legible. Close editing panes where practical. Never publish customer-level identifiers or pretend a Python rendering is a Power BI capture.

| Required view | Demonstrates / interviewer should notice | Capture status and guidance |
|---|---|---|
| Executive Overview | Accepted population, observed balances and missingness | Earlier native capture available; EUR is display-only |
| Digital Business Overview | Product/payroll/engagement breadth and synthetic labels | Capture final Desktop page after refresh |
| Segmentation | Current value groups and Unknown scores | Capture aggregate view; no individual identifiers |
| Campaigns | Contact denominator and channel performance | Capture with window/filters visible |
| Predictive Analytics | Eligible scores separated from offline evaluation | Call out weak model signal |
| Next Best Action | Ownership/contact gates and no-action outcomes | Mask all individual rows before publication |
| Experimentation | Uncertainty, sample adequacy and stop/winner decisions | Capture all three decisions without implying real lift |
| Architecture Diagram | Preserve, validate, model, measure, decide | Mermaid source plus labeled architecture figure available |

## Existing evidence

Two earlier native screenshots exist in powerbi/screenshots: Executive Overview and Financial Analysis. They show aggregate values, not the final expanded report. The original overview uses unverified EUR formatting and a visible filter pane. Python images in powerbi/previews are design previews. The experiment confidence-interval figure and retention heatmap are computed analytical figures. Final native captures of the digital, ML and experimentation pages remain pending because the desktop helper failed; no missing capture is fabricated.

## Authored page inventory

Generated from powerbi/model/report_inventory.json. Hidden supporting pages count toward the total; a reader should not expect all 26 as visible tabs.

| Page | Navigation | Visuals |
|---|---|---:|
| Executive Overview | Visible | 31 |
| Customer Profile | Visible | 27 |
| Financial Analysis | Visible | 28 |
| Segmentation | Visible | 25 |
| Customer Explorer | Visible | 20 |
| Customer Detail | Hidden | 12 |
| Country Tooltip | Hidden | 8 |
| Segment Tooltip | Hidden | 8 |
| Data Quality | Hidden | 11 |
| Digital Business Overview | Visible | 28 |
| Campaign Performance | Visible | 26 |
| Digital Engagement | Visible | 27 |
| Primary Banking | Visible | 26 |
| Value-Added Services | Visible | 25 |
| Customer Satisfaction | Visible | 26 |
| Predictive Analytics | Visible | 24 |
| Next Best Action | Visible | 23 |
| Model Performance | Visible | 22 |
| Customer Journeys | Visible | 17 |
| Customer Funnels | Visible | 18 |
| Cohorts & Retention | Visible | 19 |
| Experimentation | Visible | 21 |
| Experiment Detail | Hidden | 7 |
| Marketing Attribution | Visible | 22 |
| Customer Opportunities | Visible | 23 |
| Growth & Opportunities | Visible | 24 |

## Acceptance before public capture

Check reset/country/segment filters, drill-through, tooltips, titles, blanks and contrast separately from numeric reconciliation. For an empty project use the stable local entry, restore/refresh data, save and reopen. Capture the final pages only once that acceptance is complete. [Demo checklist](interview/demo_checklist.md).
