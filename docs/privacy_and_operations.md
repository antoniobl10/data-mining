# Privacy and operations

Customer IDs and joined financial/demographic data are sensitive even without names. The public hash namespace used for deterministic keys does not anonymize IDs or prevent dictionary attacks. A real implementation needs governed tokenization or a protected keyed mapping, source-level access restrictions, least-privilege roles, managed secrets, encryption in transit/at rest, retention controls and access/audit logging.

General report users should receive aggregate reports. Hiding a column is a usability feature, not an access control. Restrict Build permission, export, Analyze in Excel and customer drill-through; create a separate aggregate model where customer-level access is unnecessary. If geography-based access is required, implement and test a governed security mapping and row-level roles before deployment. No working RLS identity policy is invented in this project.

GDPR compliance and legal basis, minimization, retention and rights handling require organization-specific privacy review. The repository describes engineering requirements, not a compliance certification. Gender/age differences are descriptive and do not justify discriminatory eligibility or marketing decisions.

Source data, generated exports, local logs, quarantine and warehouses are Git-ignored. Existing tracked source files are not removed or rewritten. Before making this repository public, review the rights to the original workbook and notebook outputs, including Git history. Use synthetic data if the source is not cleared for sharing.

Each local run emits JSON log records with stage, timestamp, status, batch and counts/error messages; logs contain no full customer row dumps. Errors return a nonzero CLI status. The report directory has per-check results and per-batch analytical artifacts. Add centralized audit storage, owner notifications, retention and quality service-level monitoring for a deployment.

The local batch-pointer publication assumes one writer and cooperative readers. Read only the batch selected by `latest_success.json`. Keep prior batches for rollback; repoint BI to a validated prior folder when necessary. Re-ingest for retries after partial curated writes. Do not combine tables from different batch folders. Backup the original source and configuration alongside governed run records.

Git is already initialized in the supplied workspace. This project does not auto-stage or commit private artifacts. Dependencies have compatible ranges for readability; a deployment should lock and security-review resolved versions in its own build environment. GitHub Actions tests use synthetic records and no banking secrets.
