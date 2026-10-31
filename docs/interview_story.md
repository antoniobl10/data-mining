> Scope: Original nine-page BI rehearsal; use interview/ for the complete platform. For current totals and execution boundaries, see [final health](../reports/final_project_health.md) and [documentation index](README.md). Historical counts below are not current platform totals.

# Banking customer analytics interview story

Use the current build and disclose the execution boundary: the pipeline ran locally; textual Power BI artifacts were authored and structurally validated; native Desktop refresh, DAX and interactions are pending. Do not claim deployment or measured native performance. Speaking times depend on pace.

## 60–90 seconds

“I built an end-to-end banking customer analytics project using an existing Excel dataset. Python ingests the source into Bronze, applies explicit quality rules in Silver, and publishes business-ready dimensions, a customer snapshot fact and analytical marts in Gold. Of 1,999 source records, 1,439 are accepted and 560 are quarantined, with reasons retained rather than silently discarded.

For the reporting layer, I authored a Power BI project with five dimensions, single-direction relationships and a dedicated DAX measure table. Five main pages cover the executive portfolio, customer profile, financial patterns, segmentation and customer exploration, with tooltip and customer-detail definitions.

The accepted portfolio has about 68.55 million in observed balances. France has the most customers, while Germany has the largest observed balance. I distinguish missing balances from zero and label the customer-value score as an analytical proxy rather than CLV.

The pipeline and independent reference calculations pass validation. Desktop is unavailable here, so native refresh and interactions remain an explicit acceptance step. The project demonstrates how I connect trustworthy data engineering to explainable business analysis.”

## Three-minute explanation

“The business question was how to understand a banking customer portfolio consistently: who the customers are, where balances are concentrated, how credit characteristics differ and which groups merit further analysis. I started with the data that actually exists rather than promising churn, campaign ROI or profitability from a dataset that has none of those outcomes.

The architecture follows Excel, Bronze, Silver, Gold and then the Power BI semantic model. Bronze preserves ingestion and provenance. Silver applies quality rules and retains quarantined records with their reasons. There are 1,999 source rows, 1,439 accepted customers and 560 quarantined rows. Gold publishes immutable builds containing five dimensions, a fact at one customer per snapshot and analytical marts. Quality checks cover keys, grain, relationships and reconciliations, and independent SQL calculations are compared with Python before publication.

The reporting model uses one-to-many, single-direction relationships. All measures count or aggregate fact rows so country, credit, age and tenure filters reach the calculations consistently. Typed Power Query imports preserve the large integer keys, and technical fields are hidden. A dedicated measure table organizes 61 measures, including customer counts, financial averages, observed-value coverage, selected-country shares and rankings, segment comparisons and concentration.

I authored five main report pages with consistent navigation, a restrained banking theme, slicer synchronization and reset definitions. Executive Overview gives a quick portfolio picture. Customer Profile explains demographics. Financial Analysis examines balances, salary and credit, including customer-level scatter plots. Segmentation compares primary groups and value tiers. Customer Explorer and the hidden detail page support authorized investigation. Tooltip pages add context, and a hidden quality page exposes source acceptance and reconciliation.

The current data shows roughly 68.55 million in observed balances. France leads customer count and Germany leads observed balances. Only 931 customers have observed balances, which matters: average observed balance and balance per all customers answer different questions. The proxy score has 888 complete records; 551 remain Unknown rather than receiving invented values.

Validation is deliberately layered. Microsoft libraries round-trip the TMDL model, JSON schemas validate the report definitions and 557 independent reference comparisons cover twelve filter scenarios. These do not execute DAX. Since Desktop is unavailable here, native refresh and interaction acceptance are documented as pending. That boundary is part of making the project explainable and credible.”

## Five-minute technical explanation

“I approached this as an analytics product with a traceable path from source to decision. The source is an Excel customer snapshot. It contains demographic, balance, estimated salary, credit and tenure attributes. It does not contain transactions, product ownership, campaign outcomes or a meaningful business date. Those boundaries determine what the report can responsibly answer.

The pipeline preserves the Medallion separation. Bronze records source ingestion and lineage. Silver applies established validation rules, preserving accepted records and quarantining rejected ones with their reasons. The source has 1,999 records; 1,439 are accepted and 560 quarantined. I did not weaken those rules to improve the headline acceptance rate. Gold consumes the accepted population and publishes a coherent immutable build with a manifest. A report must consume all tables from the same build to avoid inconsistent dimensions and totals.

Gold contains five dimensions: customer, country, age group, credit band and tenure band. The fact grain is one customer in the current snapshot. There are also purpose-specific marts for summaries, segmentation, concentration and scoring diagnostics. The Power BI interactive model uses the core star rather than combining redundant aggregates with customer-level filtering. Snapshot controls are disconnected and clearly labeled so report slicers cannot imply that pipeline processing counts change with a business selection.

Keys are stable integer surrogates. Some require up to sixty bits, so importing CSV keys through floating point could round them and break relationships. The M queries enforce Int64 directly from CSV text. Numeric blanks become null, not zero. Monetary amounts and scores have explicit types, while customer identifiers are text. The model declares five one-to-many relationships with single-direction filtering, logical band sorting and hidden technical keys. Power Query remains an import and typing layer; segmentation and scoring logic stay upstream.

The dedicated measure table contains 61 measures with descriptions, folders and format strings. Total Customers counts the filtered customer-grain fact, which lets all five dimensions affect it consistently. Average Balance uses observed values. Balance per Customer divides the observed total by the full selected population. That distinction is substantial because only 931 of 1,439 customers have an observed balance. Percentages use safe division. Country contributions and rankings use selected-country context, while overall comparison measures deliberately clear the documented dimension filters. Dynamic concentration recalculates the cohort within the selected customer population rather than presenting a fixed precomputed number as slicer responsive.

The customer-value score is a relative analytical proxy. It combines balance, estimated salary, tenure and credit percentile ranks with weights of forty, twenty-five, twenty and fifteen percent. Complete inputs are required: 888 customers have scores and 551 remain Unknown. Quartiles produce 222 customers in each scored tier. I keep overlapping flags distinct from the mutually exclusive primary segment, because a long-tenure flag and a primary Long Term label can have different counts. Neither this score nor estimated salary proves profitability, salary domiciliation or primary-bank status.

The report has five main pages plus customer detail, two tooltips and a quality page. The overview prioritizes a small number of portfolio KPIs and comparative charts. Financial Analysis includes scatter plots at customer grain, with count-based bubble sizing to avoid excluding customers simply because their proxy score is missing. Segmentation includes a profile matrix. Explorer exposes identifiers only for an authorized analytical audience. Hiding fields is not security; deployment still needs least privilege, appropriate masking and any business-approved row-level restrictions.

Real findings are modest and reproducible. The accepted population has about 68.55 million in observed balances. France has the most customers, while Germany has the largest observed balance. The top ten percent of customers with observed balances hold about 22.8 percent of those balances. Currency is not confirmed by the source, so the requested euro display is an explicit presentation assumption.

I separated validation evidence from claims about execution. The pipeline ran, 69 Gold checks passed, twelve SQL/Pandas tables reconciled, and the Python suite contains 103 passing tests. Microsoft TOM round-trips ten model tables and five relationships; public JSON schemas validate the report files; Microsoft's M parser checks syntax. Independent Pandas and DuckDB calculations agree on 557 references across twelve filter scenarios. Nine design previews support layout review. None of those is native DAX execution. Desktop is unavailable here, so the refresh, interaction, accessibility and screenshot checklist remains the native acceptance gate.

For production, I would assess Databricks SQL Warehouse Import or DirectQuery against freshness, volume and concurrency requirements. Future product, campaign and digital-event facts would need defined grains, conformed dimensions and governed metric definitions. Any synthetic demonstrator would remain explicitly labeled and separate from the real-data report.”

## Demonstration prompts

Show architecture, overview, one country filter, segment matrix, authorized customer detail and quality controls. Explain one denominator decision and one limitation. Use [the demonstration checklist](dashboard_demo_checklist.md) to capture verified native screenshots and [the extension plan](powerbi_future_extensions.md) to discuss Digital Business use cases.
