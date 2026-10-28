# Current semantic model

The active project is ../BankingCustomerAnalytics.pbip with TMDL in ../BankingCustomerAnalytics.SemanticModel/definition/. The older banking_model.bim is historical.

The six-table core star uses five one-to-many, single-direction relationships. Balance Concentration, Pipeline Status and Gold Validation are disconnected helpers; _Measures contains all 61 measures. Summary marts are not joined to the customer snapshot fact.

model.source.json is the generated Microsoft TOM input. column_mapping.json documents exact source mappings, types, visibility and sorting; relationships.json supplies relationship mappings; report_inventory.json inventories nine pages. Run python -m tools.build_powerbi from the repository root to regenerate. Preserve intentional report edits first.

Keys import directly as Int64. Technical keys are hidden, financial averages exclude missing values, and all-customer denominators remain distinct. Customer identifiers require governed access even when hidden. Native Desktop refresh and interaction acceptance remain pending.

See [dashboard guide](../../docs/powerbi_dashboard.md), [DAX catalog](../dax/measures.md) and [validation evidence](../../docs/powerbi_validation.md).
