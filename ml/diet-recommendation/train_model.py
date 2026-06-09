"""Train a Decision Tree from the provided Diet.xls and export a JSON model.

This script looks for common column name variants and uses age, height, weight,
and BMI where available. It writes model.json compatible with the front-end
decision-tree evaluator.
"""
import os
import json
import argparse
import numpy as np

try:
    import pandas as pd
    from sklearn.preprocessing import LabelEncoder
    from sklearn.tree import DecisionTreeClassifier
    from sklearn.model_selection import train_test_split
except Exception as e:
    raise RuntimeError('Missing Python dependencies. Please install pandas and scikit-learn.')


ROOT = os.path.dirname(__file__)
DEFAULT_EXCEL = os.path.join(ROOT, 'Diet.xls')
OUT_PATH = os.path.join(ROOT, 'model.json')

ALIASES = {
    'age': ['age', 'Age', 'AGE'],
    'height': ['height', 'height(cm)', 'height(m)', 'Height', 'Height_cm', 'height_cm', 'height_m', 'Height(m)'],
    'weight': ['weight', 'weight(kg)', 'Weight', 'weight_kg', 'Weight(kg)'],
    'bmi': ['bmi', 'Bmi', 'BMI', 'BodyMassIndex'],
    'goal': ['goal', 'Goal', 'target_goal', 'goal_type']
}


def find_columns(df):
    found = {}
    for key, variants in ALIASES.items():
        for v in variants:
            if v in df.columns:
                found[key] = v
                break
    return found


def tree_to_dict(clf, feature_names):
    T = clf.tree_

    def node(i):
        if T.children_left[i] == T.children_right[i]:
            value = T.value[i][0].tolist()
            class_idx = int(np.argmax(value))
            return {'is_leaf': True, 'value': value, 'class': class_idx}
        else:
            feat_idx = T.feature[i]
            feat_name = feature_names[feat_idx]
            thr = float(T.threshold[i])
            return {
                'is_leaf': False,
                'feature': feat_name,
                'threshold': thr,
                'left': node(T.children_left[i]),
                'right': node(T.children_right[i])
            }

    return node(0)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--csv', default=DEFAULT_EXCEL, help='Path to dataset (Excel or CSV)')
    parser.add_argument('--out', default=OUT_PATH, help='Path to output model.json')
    parser.add_argument('--target', default='Label', help='Target column name')
    args = parser.parse_args()

    path = args.csv
    out = args.out
    target = args.target

    if not os.path.exists(path):
        raise SystemExit('Dataset not found: %s' % path)

    # read excel or csv; try xlrd engine for old .xls, fallback to csv
    if path.lower().endswith('.xls') or path.lower().endswith('.xlsx'):
        # Try reading as Excel (xlrd/openpyxl). If that fails, try reading as CSV because
        # the file may be a CSV with an .xls extension.
        try:
            df = pd.read_excel(path, engine='xlrd')
        except Exception:
            try:
                df = pd.read_excel(path, engine='openpyxl')
            except Exception:
                # fallback to CSV read
                df = pd.read_csv(path)
    else:
        df = pd.read_csv(path)

    print('Loaded', df.shape, 'columns:', list(df.columns)[:20])

    if target not in df.columns:
        raise SystemExit('Target column %s not found in dataset' % target)

    cols = find_columns(df)
    print('Detected columns mapping:', cols)

    feature_cols = []
    # prefer age,height,weight,bmi in that order
    for k in ['age', 'height', 'weight', 'bmi', 'goal']:
        if k in cols:
            feature_cols.append(cols[k])

    if not feature_cols:
        # fallback: use numeric columns except target
        feature_cols = [c for c in df.columns if c != target and np.issubdtype(df[c].dtype, np.number)]

    X = df[feature_cols].copy()
    y = df[target].astype(str).copy()

    encoders = {}
    for col in X.columns:
        if X[col].dtype == object or X[col].dtype.name == 'category':
            le = LabelEncoder()
            X[col] = le.fit_transform(X[col].astype(str))
            encoders[col] = {cls: int(idx) for idx, cls in enumerate(le.classes_)}

    # fill numeric NaNs
    for col in X.columns:
        if np.issubdtype(X[col].dtype, np.number):
            X[col] = X[col].fillna(X[col].mean())

    t_le = LabelEncoder()
    y_enc = t_le.fit_transform(y)
    class_names = [str(c) for c in t_le.classes_]

    print('Training features:', list(X.columns))
    print('Target classes:', class_names)

    X_train, X_test, y_train, y_test = train_test_split(X.values, y_enc, test_size=0.15, random_state=42, stratify=y_enc)

    clf = DecisionTreeClassifier(max_depth=6, random_state=42)
    clf.fit(X_train, y_train)

    acc = clf.score(X_test, y_test)
    print('Test accuracy:', acc)

    model = {
        'feature_names': list(X.columns),
        'class_names': class_names,
        'encodings': encoders,
        'tree': tree_to_dict(clf, list(X.columns))
    }

    with open(out, 'w', encoding='utf-8') as f:
        json.dump(model, f, indent=2)

    print('Wrote model to', out)


if __name__ == '__main__':
    main()
