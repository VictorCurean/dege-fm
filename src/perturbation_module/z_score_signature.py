def get_avg_zscore_drug_cutoff(drug_name, sig_info, expression_data, gene_info, zscore_cutoff):
    signatures = sig_info[sig_info['pert_iname'].str.contains(drug_name)]
    if len(signatures) == 0:
        return None

    if len(list(signatures['pert_iname'].unique())) != 1:
        print(f"Drug name is ambiguous: {drug_name}")
        return None

    sig_to_keep = list(signatures['sig_id'])

    gene_values = expression_data[sig_to_keep].copy()
    gene_values['mean_z_score'] = gene_values.mean(axis=1)
    gene_values['mean_abs_z_score'] = gene_values['mean_z_score'].abs()

    gene_values = gene_values[gene_values['mean_abs_z_score'] >= percentile_value]
    gene_values = gene_values[gene_values['mean_abs_z_score'] >= zscore_cutoff]

    gene_index = list()
    for gene_id in list(gene_values.index):
        row = gene_info[gene_info['pr_gene_id'] == int(gene_id)]
        name = row['pr_gene_symbol'].iloc[0]
        gene_index.append(name)

    gene_values.index = gene_index

    gene_values = gene_values.sort_values(by='mean_abs_z_score')
    return gene_values

def get_avg_zscore_drug_cutoff_percentile(drug_name, sig_info, expression_data, gene_info, percentile):
    signatures = sig_info[sig_info['pert_iname'].str.contains(drug_name)]
    if len(signatures) == 0:
        return None

    if len(list(signatures['pert_iname'].unique())) != 1:
        print(f"Drug name is ambiguous: {drug_name}")
        return None

    sig_to_keep = list(signatures['sig_id'])

    gene_values = expression_data[sig_to_keep].copy()
    gene_values['mean_z_score'] = gene_values.mean(axis=1)
    gene_values['mean_abs_z_score'] = gene_values['mean_z_score'].abs()

    percentile_value = gene_values['mean_abs_z_score'].quantile(percentile)
    gene_values = gene_values[gene_values['mean_abs_z_score'] >= percentile_value]

    gene_index = list()
    for gene_id in list(gene_values.index):
        row = gene_info[gene_info['pr_gene_id'] == int(gene_id)]
        name = row['pr_gene_symbol'].iloc[0]
        gene_index.append(name)

    gene_values.index = gene_index

    gene_values = gene_values.sort_values(by='mean_abs_z_score')
    return gene_values