import json

with open('01_data_engineering.ipynb', 'r', encoding='utf-8') as f:
    nb = json.load(f)

for cell in nb['cells']:
    if cell['cell_type'] == 'code':
        for i, line in enumerate(cell['source']):
            # Add fillna in Phase 4 after reading rfm_features.csv
            if "features = pd.read_csv(SAVE_PATH + 'rfm_features.csv')" in line:
                cell['source'][i] = line + "\nfeatures.fillna(0, inplace=True)\n"
            
            # Add fillna in Phase 3 before saving
            if "features.to_csv(SAVE_PATH + 'rfm_features.csv', index=False)" in line:
                cell['source'][i] = "features.fillna(0, inplace=True)\n" + line

with open('01_data_engineering.ipynb', 'w', encoding='utf-8') as f:
    json.dump(nb, f, indent=1)

print('Fixed!')
