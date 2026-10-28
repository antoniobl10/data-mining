# Interview demonstration and native Power BI acceptance

The textual project is authored and locally validated. Desktop is unavailable here, so the native checks below are intentionally pending. Do not describe them as passed or present `powerbi/previews/*.png` as Desktop screenshots.

## Prepare

- Run the complete pipeline, pytest and Gold validation.
- Create a fresh local project with `python -m tools.prepare_powerbi`; open its printed PBIP path.
- Confirm GoldDataPath identifies one immutable Gold build and refresh every table.
- Verify five single-direction relationships, Int64 keys, hidden technical fields and the _Measures folders.
- Confirm 1,439 customers, 68,552,786.88 observed balance, 73,633.50 average observed balance, 222 Premium and 444 High Value customers for the current unchanged source.
- Confirm that Average Balance differs from Balance per Customer because only 931 balances are observed.

## Native report checks — not yet executed

- [ ] Every page renders without an error, overlapping visual, clipped title, bad font or unexpected blank.
- [ ] Country, gender, age, tenure, credit, value and primary-segment slicers filter the expected populations; multi-select works.
- [ ] Synchronized slicers persist across navigation and Reset Filters restores All without changing the active page.
- [ ] Country/age/credit/tenure sorting follows model sort columns; value tiers are Low, Medium, High, Premium, Unknown.
- [ ] Rank/share measures preserve slicer selections and respond to row context; use the expected values in `powerbi/validation/filter_context_reference.csv`.
- [ ] Global comparison measures deliberately clear report filters; detail Country Average Balance compares with the selected customer's full country cohort.
- [ ] Dynamic narrative handles All, single country, multi-country and no-match contexts without unsupported claims.
- [ ] Concentration matches Gold unfiltered and recomputes sensibly under slicers; no negative/nonpositive denominator produces a misleading share.
- [ ] Salary/balance scatter retains 931 complete pairs and credit/balance 924 before additional filters; unscored customers are not dropped merely because score is missing.
- [ ] Hover country/segment visuals: the correct tooltip context and observed denominators flow.
- [ ] Right-click a customer in Explorer → Drill through → Customer Detail; verify identity and comparison context, then return.
- [ ] Explorer conditional formatting is subtle, and native scrolling/column widths keep all requested columns accessible.
- [ ] DQ shows 1,999 source rows, 1,439 accepted, 560 quarantine, three original-source aggregate failures, 69 passing Gold checks and zero failing Gold checks.
- [ ] Keyboard tab order, alt text, contrast and navigation are usable at normal zoom.
- [ ] Review Performance Analyzer and any credential/privacy-level prompts before publishing.
- [ ] Review analyst authorization, Build/export access, screenshot masking and source-data sharing rights.

## Recommended interview sequence

1. Architecture and lineage: explain why the project begins before the dashboard.
2. Executive Overview: portfolio size, observed country balances, Premium share and coverage.
3. Customer Profile: ordered groups and differences with sample/coverage limits.
4. Financial Analysis: observed associations and 22.8% balance share among the top 10% of 931 observed-balance customers.
5. Segmentation: show exclusive primary labels versus overlapping flags, then the score sensitivity limitation.
6. Authorized Explorer/drill-through: show one approved/masked customer, not a broad dump of real IDs.
7. Data Quality: explain quarantine, source failures, reconciliation and successful-build publication.

## Native screenshot slots

After completing the pending checks, capture `01_overview.png`, `02_customer_profile.png`, `03_financial.png`, `04_segments.png`, `05_explorer_masked.png`, `06_customer_detail_masked.png`, `07_country_tooltip.png`, `08_segment_tooltip.png`, `09_data_quality.png` under `powerbi/screenshots/`. No fake image files are supplied as placeholders. Record Desktop version, Gold build ID and filters with the captures.
