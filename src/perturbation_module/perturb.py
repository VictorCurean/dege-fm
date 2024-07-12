def perturb_adata_using_zscores(adata, z_scores, drug):
    perturbed_adata = adata.copy()
    perturbed_adata_norm = perturbed_adata.copy()
    sc.pp.normalize_total(perturbed_adata_norm, target_sum=1e4)

    for gene in [g for g in list(z_scores.index) if g in list(adata.var_names)]:
        gene_index = list(perturbed_adata.var_names).index(gene)
        normalized_counts = list(perturbed_adata_norm.X[:, gene_index])

        mean_z_score = z_scores.loc[gene, 'mean_z_score']

        mean = statistics.mean(normalized_counts)
        stdev = statistics.stdev(normalized_counts)
        mu = (mean_z_score * stdev) + mean

        if mu <= 0:
            mu = 0.05

        poisson_dist = poisson(mu=mu)

        gene_vector = list()

        for cell_index in range(len(list(perturbed_adata_norm.obs_names))):
            total_raw_counts = perturbed_adata.X[cell_index].sum()

            sampled_val = poisson_dist.rvs(size=1)[0]

            perturbed_val = math.ceil(sampled_val * (total_raw_counts / 1e4))

            gene_vector.append(perturbed_val)

        assert len(gene_vector) == len(list(perturbed_adata.obs_names))  # sanity check
        perturbed_adata.X[:, gene_index] = np.array(gene_vector)

    perturbed_adata.obs['condition'] = drug
    return perturbed_adata




