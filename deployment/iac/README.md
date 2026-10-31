# Optional infrastructure implementation boundary

No Terraform resources are applied or fabricated. The Azure reference needs a resource group, ADLS Gen2 with hierarchical namespace, Unity Catalog storage credentials/external locations, a Databricks workspace/metastore attachment, Key Vault and approved private-network/identity controls. Existing enterprise resources should be reused where appropriate.

Before an executable IaC module is chosen, obtain subscription/tenant/resource ownership, region, network topology, retention, redundancy, identity and cost requirements. Keep Terraform state in a protected remote backend; use workload identity rather than committed client secrets. CI should validate/plan separately from an environment-approved apply. Storage names and credentials must be supplied by deployment configuration, never invented in this repository.
