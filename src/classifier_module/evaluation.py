def get_drug_stats(adata, model):
    results = dict()

    drugs_found = list(adata.obs['condition'].unique())
    for drug in drugs_found:
        adata_drug = adata[adata.obs['condition'] == drug].copy()
        X_drug = adata_drug.obsm['X_uce']
        y_pred = model.predict(X_drug)
        y_pred_prob = model.predict_proba(X_drug)
        results[drug] = dict()
        results[drug]['pred_reprogrammed'] = list(y_pred).count(1)
        results[drug]['pred_control'] = list(y_pred).count(0)
        results[drug]['pred'] = list(y_pred)
        results[drug]['pred_prob'] = y_pred_prob

    return results