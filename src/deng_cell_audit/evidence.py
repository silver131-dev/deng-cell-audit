"""Identifier and missingness checks without replacing scientific decisions."""
import math
import re
from .checks import names, require

VALUE_STATUSES = {"OBSERVED", "AGGREGATE_ONLY_RATIO_OF_SUMS", "NOT_EMITTED_BY_ENGINE", "UNDEFINED_IN_ENGINE"}


def migrate_ids(master, aliases, key="target_id"):
    old = names([r["old_id"] for r in aliases], "old aliases")
    new = names([r["new_id"] for r in aliases], "new aliases")
    master_ids = names([r[key] for r in master], "master IDs")
    require(set(master_ids) == set(old), "alias coverage differs from master")
    lookup = dict(zip(old, new))
    return [{**row, "historical_target_id": row[key], key: lookup[row[key]]} for row in master]


def external_catalog(records, master):
    names([r["target_gene"] for r in master], "master symbols")
    names([r["target_id"] for r in master], "master IDs")
    by_symbol = {r["target_gene"]: r["target_id"] for r in master}
    catalog = {}
    for row in records:
        ensembl, symbol = row["ensembl_id"], row["target_gene"]
        names([ensembl], "external gene ID")
        names([symbol], "external symbol")
        if ensembl in catalog:
            require(catalog[ensembl]["target_gene"] == symbol, "conflicting external symbol")
            continue
        catalog[ensembl] = {"evidence_target_id": "DENG-RESEARCH-" + ensembl,
                            "ensembl_id": ensembl, "target_gene": symbol,
                            "master471_target_id": by_symbol.get(symbol),
                            "mapping_basis": "EXACT_SUPPLIED_SYMBOL_ONLY_NO_ALIAS_RESOLUTION"}
    return list(catalog.values())


def validate_evidence(rows, catalog):
    keys = set(names([r["evidence_target_id"] for r in catalog], "research IDs"))
    seen = set()
    for row in rows:
        require(row["evidence_target_id"] in keys, "orphan research foreign key")
        key = tuple(row[k] for k in ("dataset", "job_id", "context", "evidence_target_id", "metric"))
        require(all(isinstance(k, str) and k for k in key), "empty evidence key")
        require(key not in seen, "duplicate evidence key")
        seen.add(key)
        require(row["value_status"] in VALUE_STATUSES, "unknown missingness status")
        require(row["direction"] in {"minimize", "maximize"}, "unknown metric direction")
        require(isinstance(row["axis_hash"], str) and re.fullmatch(r"[0-9a-f]{64}", row["axis_hash"]), "invalid axis SHA-256")
        require(isinstance(row["split_status"], str) and bool(row["split_status"]), "missing split status")
        if row["value_status"] == "OBSERVED":
            require(type(row["value"]) in (int, float) and math.isfinite(row["value"]), "observed value is not finite")
        else:
            require(row["value"] is None, "missing/aggregate-only target value must be null")
    return {"rows": len(rows), "foreign_keys": "PASS", "missingness": "PASS", "model_use": "HOLD"}

