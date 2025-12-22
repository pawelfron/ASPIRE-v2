import re
import pandas as pd


def get_query_rel_judgements(qrels: pd.DataFrame):
    relevance_counts = (
        qrels.groupby(["query_id", "relevance"]).size().unstack(fill_value=0)
    )

    if 0 not in relevance_counts.columns:
        relevance_counts[0] = 0

    relevance_counts.columns = [
        "Irrelevant" if col == 0 else f"Relevance_Label_{col}"
        for col in relevance_counts.columns
    ]

    results = {}
    for query_id in relevance_counts.index:
        results[query_id] = {
            "irrelevant": int(relevance_counts.loc[query_id, "Irrelevant"]),
            "relevant": {},
        }
        for column in relevance_counts.columns:
            if column != "Irrelevant":
                results[query_id]["relevant"][column] = int(
                    relevance_counts.loc[query_id, column]
                )

    return relevance_counts, results


def sort_query_ids(query_ids):
    def extract_number(query_id):
        match = re.search(r"\d+", query_id)
        return int(match.group()) if match else float("inf")

    return sorted(query_ids, key=extract_number)
