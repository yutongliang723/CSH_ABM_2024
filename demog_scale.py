import pandas as pd

vec1 = pd.read_csv('demog_vectors.csv')
vec1 = vec1.rename_axis('age').reset_index()
new_max_age = 60
old_max_age = vec1['age'].max()
scale_factor = new_max_age / old_max_age
scaler = 5
other_para = ['rho', 'pstar', 'mortparms']
bins = pd.cut(vec1['age'], bins=new_max_age)
binned_vec = pd.DataFrame()
for col in other_para:
    binned_col = vec1.groupby(bins, observed=False).agg({col: 'mean'}).reset_index()
    binned_col[col] = binned_col[col] * scale_factor * scaler
    binned_vec[col] = binned_col[col]

bin_centers = [interval.mid for interval in binned_col['age']]
binned_vec = binned_vec.rename_axis('age_new').reset_index()
binned_vec.loc[binned_vec['age_new'] <= 3, 'pstar'] *= 0.5


binned_vec['mstar'] = vec1['mstar'] * scaler # fertility scale
binned_vec['fertparm'] = vec1['fertparm'] * scaler
binned_vec['mortscale'] = vec1['mortscale'] * scaler
binned_vec['fertscale'] = vec1['fertscale'] *scaler
binned_vec['phi'] = vec1['phi']
vec1 = binned_vec

vec1.to_csv('demog_vectors_scaled.csv')