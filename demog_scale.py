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
    original_values = {param: vec1_copy[param] for param in list(vec1_copy.columns)}

    # Shrink only the x-axis (age), keeping y-values the same
    new_ages = original_age * scale_factor

    # Create a new DataFrame with rescaled ages
    rescaled_df = pd.DataFrame({'age_rescaled': new_ages})
    for param in original_values.keys():
        rescaled_df[param] = original_values[param]  # Keep y-values unchanged

    # vec1_copy.to_csv('demog_vectors_scaled.csv')
    rescaled_df.to_csv('demog_vectors_scaled.csv')
