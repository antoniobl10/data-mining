# Power BI design rationale

The [report specification](../powerbi/dashboard_specification.md) is the authoritative four-page layout and field mapping. The [semantic model](../powerbi/model/README.md) defines relationship directions, fact grain, types, measures and import procedure.

Visual hierarchy progresses from portfolio totals to demographics, financial relationships and segment hypotheses. Country uses bars because a small categorical set is easier to compare than map areas. Missingness and score coverage remain visible because observed financial totals are incomplete. Scatters distinguish cohort averages from individual observations; neither establishes causality.

Use consistent customer counts and valid-observation financial averages. Keep Unknown categories visible, use meaningful titles and show denominators in tooltips. A primary segment is exclusive; overlapping behavioral flags are exploratory filters. Financial metric copies in dimensions are hidden to avoid accidental inconsistent aggregation.

The theme provides restrained banking colors and readable typography. Layout calls for consistent margins, limited visuals, compact monetary scales and full tooltip values. No decorative gauges, false temporal comparisons, fabricated profit metrics or unnecessary customer detail belong in this report.

This repository contains construction-ready model assets and an explicit report design. A native report file, published workspace, security configuration and Desktop interaction/rendering validation require the Power BI authoring environment.
