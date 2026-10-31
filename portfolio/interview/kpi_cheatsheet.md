<!-- Generated from docs/interview/kpi_cheatsheet.md; edit canonical source. -->

# KPI cheat sheet

Always name the grain, eligible population, window, null policy and owner. Define zero denominators as unavailable, not perfect performance. These are operational definitions for rehearsal; implemented catalogs remain authoritative.

| KPI | Numerator / denominator or definition | Main caution |
|---|---|---|
| Campaign conversion | Mature converted contacts / mature sent contacts | Distinct-customer funnel counts are a different grain |
| CTR | Clicked contacts / sent contacts | Click-to-open is a separate rate |
| Open rate | Opened contacts / sent contacts | Open tracking can be incomplete |
| Product penetration | Customers owning a product / eligible customer population | Date and active-ownership definition matter |
| Product depth | Active product holdings / customers, at a snapshot | Define distinct product types versus individual accounts |
| Salary domiciliation | Current salary-domiciliation customers / selected customers | First adoption conversion needs eligible nonowners and dates |
| Service activation | Activated eligible offers / eligible offers in a window | Offered, eligible and customer-grain denominators differ |
| Digital period retention | Cohort members meaningfully active at age m / observable cohort members at age m | Reactivation is allowed; future months absent |
| Product retention | Cohort members retaining dated product ownership / observable cohort members | Service-state history is unavailable here |
| Churn | Confirmed attrition / population at risk in a defined interval | Project model predicts inactivity, not confirmed closure |
| NPS | 100 × (promoter share − detractor share), respondents only | Standard 9–10/0–6 categories; report response bias and sample |
| Engagement | Configured activity composite or meaningful-active rate | Proprietary score, not a universal banking standard |
| Campaign ROI proxy | (Assumed observed value − contact cost) / contact cost | Synthetic units; attribution is not causal value |
| Cost per conversion | Contact cost / observed conversions | Not cost per incremental conversion |
| Incremental conversion | Treatment rate − control rate | Percentage points versus relative lift must be explicit |
| Incremental conversions | Rate contrast × treatment population | An estimate, with uncertainty and design assumptions |
| Cost per incremental conversion | Treatment campaign cost / estimated incremental conversions in current economics mart | Null if nonpositive incremental conversions; other conventions must be labeled |

Example: the re-engagement simulation goes from 27.67% to 35.73%, approximately **+8.06 percentage points**, not “8.06% more revenue.” Current reports show separate observational and randomized economics. See metric definitions (repository reference) and analytics methods (repository reference).
