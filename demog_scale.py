import pandas as pd

def demog_scale():
    vec1 = pd.read_csv('demog_vectors.csv')
    vec1_copy = vec1.copy()
    vec1 = vec1.rename_axis('age').reset_index()
    vec1_copy = vec1_copy.rename_axis('age').reset_index()

    # Define new age scaling
    new_max_age = 60
    old_max_age = vec1['age'].max()
    scale_factor = new_max_age / old_max_age

    # Store original values
    original_age = vec1_copy['age']
    original_values = {param: vec1_copy[param] for param in ['fertparm', 'mortscale', 'fertscale', 'mstar', 'phi', 'm0', 'pstar', 'p0']}

    # Shrink only the x-axis (age), keeping y-values the same
    new_ages = original_age * scale_factor

    # Create a new DataFrame with rescaled ages
    rescaled_df = pd.DataFrame({'age_rescaled': new_ages})
    for param in original_values.keys():
        rescaled_df[param] = original_values[param]  # Keep y-values unchanged

    df_rebinned = rescaled_df[['pstar', 'p0']].groupby(rescaled_df.index // 2).mean().reset_index(drop=True)
    df_other_para = vec1_copy.loc[:, ~vec1_copy.columns.isin(['pstar', 'p0'])][:60]
    df_merged = pd.concat([df_rebinned, df_other_para], axis=1)


    # vec1_copy.to_csv('demog_vectors_scaled.csv')
    df_merged.to_csv('demog_vectors_scaled.csv')
