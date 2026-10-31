> Scope: Original nine-page / 61-measure BI baseline. For current totals and execution boundaries, see [final health](../reports/final_project_health.md) and [documentation index](README.md). Historical counts below are not current platform totals.

# Banking Customer Analytics — Power BI project

The current deliverable is a textual PBIP project with a TOM-validated TMDL semantic model, enhanced PBIR report definition, typed Power Query imports and a 61-measure catalog. The report is authored against the real accepted Gold customer snapshot. No synthetic business results or fabricated dates were introduced.

**Native validation status (updated):** Desktop 2.159.883.0 now loads the repaired report. All ten partitions refreshed to Ready, all 61 measures evaluated and 360 core comparisons across twelve filter scenarios passed. Native captures succeeded for all nine pages; selected populated captures were inspected. Specific interaction/accessibility acceptance remains pending. See [native repair evidence](powerbi_native_repair.md). Static images under powerbi/previews remain Python design previews.

## Open and refresh

1. Install current Power BI Desktop on Windows. Enable Power BI Project/enhanced report format options if your version requires them.
2. From the repository root run `python run_pipeline.py --stage all` to produce the complete current pipeline, or `python run_pipeline.py --stage gold` to reuse published accepted Silver.
3. Run `python -m tools.build_powerbi` when regenerating the project from the current Gold schema. This optional authoring command needs .NET 10 SDK, Node.js and the validation dependencies described in docs/powerbi_validation.md. The committed PBIP/TMDL files can be opened without these developer tools.
4. Run `python -m tools.prepare_powerbi`. It creates a **fresh ignored local copy**, sets its GoldDataPath to the current immutable Gold CSV export folder, and prints the PBIP path. It does not overwrite earlier local copies or open Desktop automatically.
5. Open that printed `BankingCustomerAnalytics.pbip` in Desktop, inspect the parameter and refresh all tables. Review native errors rather than assuming a schema-valid project has already been refreshed.

Alternatively open `powerbi/BankingCustomerAnalytics.pbip`, set the required **GoldDataPath** parameter manually, and refresh. Its tracked default is deliberately empty: no developer-specific absolute path or credentials are committed. Use the `powerbi_path` from `data/reports/latest_gold.json`, pointing to `<Gold build>/powerbi`, not the repository's `powerbi` project folder. The sibling Gold manifest and `_quality` report must remain in their normal build structure for metadata queries.

Refresh uses one immutable build for every table. A newer pipeline run does not mutate an already-bound model; prepare a new local copy or deliberately update GoldDataPath before refresh. Build timestamps are technical lineage, not customer observation dates.

## Semantic model

| Table | Role |
|---|---|
| Dim Customer | One accepted customer; gender, value tier, primary segment and quality status |
| Dim Country | Standardized country slicer; Unknown member retained |
| Dim Age Group | Configured ordered age groups |
| Dim Credit Band | Configured ordered credit bands |
| Dim Tenure Band | Configured ordered tenure bands |
| Fact Customer Financials | One customer in the current snapshot; financial measures, flags and value components |
| _Measures | Dedicated host for all 61 measures; hidden physical placeholder column |
| Balance Concentration | Disconnected four-row cohort selector; dynamic concentration recomputes from selected fact rows |
| Pipeline Status | Disconnected build/source/accepted/quarantine/source-quality metadata |
| Gold Validation | Disconnected recorded Gold checks and outcomes |

There are five active dimension **1 → many** fact relationships with single-direction filtering. No dimension-to-dimension, bidirectional or many-to-many relationship is used. Financial and key copies in Dim Customer are hidden; report financial measures read the fact. All keys are int64 and must never be inferred as floating point. Customer IDs are text and hidden from the general field list, but are explicitly used in the authorized Explorer/drill-through visuals. Hidden fields are not access controls.

Age, tenure and credit scores use whole-number model types; balances, salaries and proxy scores use decimal-number types; flags use logical types. Power Query converts blank numeric cells to null and explicitly types CSV key text as Int64. It does not redo Gold validation, segmentation or value scoring. Its only derived column is a presentation sort order for value tiers Low, Medium, High, Premium, Unknown. Age/credit/tenure labels sort by their configured Sort Order.

## Measures and semantics

The complete [measure catalog](../powerbi/dax/measures.md) includes expression, description, display folder, format and intended page for every measure. Folders cover Customers, Balances, Credit, Salary, Customer Value, Segments, Percentages, Comparisons, Coverage, Titles, Narrative, Formatting and Data Quality.

- Total Customers counts fact rows, returning zero for no matching customers. Counting Dim Customer would fail to respect direct country/age/credit/tenure slicers in this star.
- Average Balance averages observed balances. Balance per Customer divides the observed total by **all** selected customers. They intentionally differ under missingness.
- Premium/High Value percentages use all selected customers, including Unknown scores. Score Coverage and Balance Coverage disclose unavailable inputs.
- Country ranks use selected countries and exclude empty members/blank metrics. Contribution shares use the selected visual total, preserving external slicers.
- Overall comparison baselines deliberately clear report dimension/fact filters. Country Average Balance on drill-through uses the customer's country cohort after clearing personal filters. None of these functions bypasses security roles.
- Dynamic concentration follows the Gold top-ceil(1/5/10%) and bottom-floor(50%) observed-balance definitions. Negative or nonpositive totals yield blank shares. Missing balances are not zeroes. Uniform scatter size represents one customer; using a missing value score as point size would silently omit valid unscored balance observations.

There are no YTD/MTD/YoY/MoM measures, calendar trend lines or fake economic outcomes. Requested EUR format strings are display assumptions; source currency and salary period remain unverified.

## Report pages

| Page | Question / content |
|---|---|
| Executive Overview | Portfolio size, observed balances, credit/salary averages, Premium share, country/value/credit/age/segment distributions and dynamic narrative |
| Customer Profile | Who the customers are: country, gender, ordered age and tenure distributions; observed balance/salary by age and an age/credit/tenure/coverage matrix |
| Financial Analysis | Country totals/averages, credit/tenure balance profiles, dynamic concentration and two customer-level scatter plots with valid pair counts in previews |
| Segmentation | Primary mix, balance contribution, Premium by country, High Value by age and a profile matrix covering customer share and observed financial/value averages |
| Customer Explorer | Authorized customer table with filters, raw ID, demographics, credit, financial values, value tier and primary segment; conditional text emphasis |
| Customer Detail (hidden) | Customer-ID drill-through, source-quality label, observed financial profile and country/overall balance comparisons |
| Country Tooltip (hidden) | Country count, balance, credit, Premium share and balance coverage |
| Segment Tooltip (hidden) | Segment financial/value profile and score coverage |
| Data Quality (hidden) | Source/accepted/quarantine counts, original-source failed checks, Gold pass/fail checks and technical lineage |

The two profile matrices consolidate several related averages rather than repeating eight near-identical charts. All pages use the neutral navy/teal theme, consistent spacing, meaningful titles and restrained conditional formatting. Design previews mask customer IDs; the native Explorer is intentionally restricted analyst detail.

## Slicers, navigation and actions

Country, gender and value selections are synchronized where their slicers appear. Profile adds age/tenure/credit; Financial uses credit/tenure/value; Segmentation uses primary and value segments. Not every slicer appears on every page. All selections start at All.

Consistent navigation buttons link the five main pages and show the active page. Reset Filters applies a report bookmark that clears captured slicer state without navigating away. A footer button opens Data Quality. Customer Explorer supports right-click → Drill through → Customer Detail; the detail page has a return-to-Explorer button. Country/primary-segment charts and matrices link to their report tooltip pages.

Explicit DataFilter interactions avoid relying on default cross-highlighting. Concentration is recomputed from slicers but isolated from arbitrary chart-click contexts to avoid an unclear changing rank denominator. Native actions, sync propagation, tooltip filter flow, conditional formatting and bookmark reset still require the manual Desktop acceptance checks below; JSON schema validation alone cannot prove their runtime behavior.

## Accessibility and performance

Visuals have titles, alt-text metadata and sequential tab order. Buttons use clear labels, rectangular rounded shapes and adequate height. Navy text on pale backgrounds and white text on teal use readable contrast; values/labels communicate meaning in addition to color. Public visuals show aggregates rather than source IDs.

The model imports one small customer fact, not duplicated summary facts. Explicit measures replace implicit aggregations. No unsupported time table or expensive unnecessary calculated columns exist. Country ranks iterate only a few dimension members. Dynamic TOPN concentration can become more expensive on a much larger population; benchmark with Performance Analyzer before production scaling.

## Privacy and release acceptance

The shared project contains customer-level data after refresh. Hiding Explorer or Customer ID is insufficient security. Publish aggregate-only content to general executives where possible, restrict Build/export permissions and authorize analysts separately. RLS and role membership need actual business access requirements; no artificial identity rules are invented. Govern masking, encryption, audit/retention, least privilege and GDPR review. Review source sharing rights before publishing any screenshot or model cache.

Follow [the native demo/QA checklist](dashboard_demo_checklist.md), capture actual screenshots under `powerbi/screenshots/` only after native review, and clearly distinguish them from design previews. [Validation status](powerbi_validation.md) records what was actually tested. [Databricks architecture](powerbi_databricks_architecture.md) describes production connection choices.

References: [PBIP overview](https://learn.microsoft.com/en-us/power-bi/developer/projects/projects-overview), [public PBIR format](https://learn.microsoft.com/en-us/power-bi/developer/projects/projects-report), [TMDL](https://learn.microsoft.com/en-us/analysis-services/tmdl/tmdl-overview), [Microsoft M parser](https://github.com/microsoft/powerquery-parser).
