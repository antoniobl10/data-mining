"""Task names match the reference Databricks job graph."""

TASKS = {
    "01_source_validation": [],
    "02_bronze_ingestion": ["01_source_validation"],
    "03_silver_transformation": ["02_bronze_ingestion"],
    "04_silver_quality": ["03_silver_transformation"],
    "05_gold_dimensions": ["04_silver_quality"],
    "06_gold_facts": ["05_gold_dimensions"],
    "07_customer_360": ["06_gold_facts", "04_silver_quality"],
    "08_feature_engineering": ["07_customer_360"],
    "09_ml_scoring": ["08_feature_engineering"],
    "10_gold_prediction_marts": ["09_ml_scoring"],
    "11_gold_quality": ["06_gold_facts", "07_customer_360", "10_gold_prediction_marts"],
    "12_export_powerbi": ["11_gold_quality"],
    "13_pipeline_validation": ["12_export_powerbi"],
}
ALIASES = {
    "source": ["01_source_validation"],
    "bronze": ["02_bronze_ingestion"],
    "silver": ["03_silver_transformation", "04_silver_quality"],
    "gold": ["05_gold_dimensions", "06_gold_facts"],
    "customer_360": ["07_customer_360"],
    "features": ["08_feature_engineering"],
    "score": ["09_ml_scoring"],
    "export": ["12_export_powerbi"],
    "validate": ["13_pipeline_validation"],
}


def order(graph=None):
    graph = graph or TASKS
    remaining = dict(graph)
    result = []
    while remaining:
        ready = sorted(k for k, deps in remaining.items() if set(deps) <= set(result))
        if not ready:
            raise ValueError("Task graph contains a cycle or unknown dependency")
        for name in ready:
            result.append(name)
            remaining.pop(name)
    return result


def select(stage=None, from_stage=None, to_stage=None):
    ordered = order()

    def resolve(value):
        if value in ALIASES:
            return ALIASES[value]
        if value in TASKS:
            return [value]
        raise ValueError("Unknown stage: " + str(value))

    if stage and (from_stage or to_stage):
        raise ValueError("Use --stage or a --from-stage/--to-stage range")
    if stage:
        selected = set(resolve(stage))
    else:
        start = min(ordered.index(n) for n in resolve(from_stage)) if from_stage else 0
        end = max(ordered.index(n) for n in resolve(to_stage)) if to_stage else len(ordered) - 1
        if start > end:
            raise ValueError("Start stage must precede end stage")
        selected = set(ordered[start : end + 1])
    # Ancestors are explicit even for partial runs; validated resume checkpoints avoid recompute.
    pending = list(selected)
    while pending:
        for dependency in TASKS[pending.pop()]:
            if dependency not in selected:
                selected.add(dependency)
                pending.append(dependency)
    return [name for name in ordered if name in selected]
