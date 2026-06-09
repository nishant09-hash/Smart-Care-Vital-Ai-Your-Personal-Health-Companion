#!/usr/bin/env python3
"""Simple smoke-test for the exported decision-tree model.json

Usage:
  # run with default sample ages
  python test_model.py

  # run with custom ages
  python test_model.py --ages 5 12 18 24 30

This script uses only the Python standard library and reads `model.json` from
the same folder. It evaluates the JSON tree and prints predicted class labels.
"""
import json
import os
import argparse


def load_model(path):
    with open(path, 'r', encoding='utf-8') as f:
        return json.load(f)


def eval_tree(node, features):
    if node.get('is_leaf'):
        return int(node.get('class'))
    feat = node.get('feature')
    thr = node.get('threshold')
    if feat not in features:
        raise KeyError(f'Missing feature {feat} in input {features}')
    try:
        val = float(features[feat])
    except Exception:
        val = features[feat]
    if val <= thr:
        return eval_tree(node['left'], features)
    else:
        return eval_tree(node['right'], features)


def predict(model, features):
    idx = eval_tree(model['tree'], features)
    return model['class_names'][idx]


def main():
    here = os.path.dirname(__file__)
    model_path = os.path.join(here, 'model.json')
    if not os.path.exists(model_path):
        print('model.json not found at', model_path)
        return

    model = load_model(model_path)
    # try to load optional label_map.json
    label_map_path = os.path.join(here, 'label_map.json')
    label_map = {}
    if os.path.exists(label_map_path):
        try:
            label_map = load_model(label_map_path)
            print('Loaded label_map.json with', len(label_map), 'entries')
        except Exception:
            label_map = {}
    parser = argparse.ArgumentParser()
    parser.add_argument('--ages', nargs='*', type=float, help='List of ages to predict')
    args = parser.parse_args()

    sample_ages = args.ages if args.ages else [5, 8, 12, 15, 18, 22, 27, 35]

    print('Model feature names:', model.get('feature_names'))
    print('Class names (first 20):', model.get('class_names')[:20])
    print('\nPredictions:')
    for a in sample_ages:
        # Build features dict for this sample that includes all feature_names expected by model
        features = {}
        # sensible defaults
        default_height = 1.65  # meters
        default_weight = 65.0  # kg
        default_bmi = round(default_weight / (default_height * default_height), 1)

        for fn in model.get('feature_names', []):
            key = fn.lower()
            if 'age' in key:
                features[fn] = float(a)
            elif 'height' in key:
                features[fn] = default_height
            elif 'weight' in key:
                features[fn] = default_weight
            elif 'bmi' in key:
                # compute BMI from defaults to keep consistency
                features[fn] = default_bmi
            else:
                # unknown feature -> 0
                features[fn] = 0

        try:
            pred = predict(model, features)
            # map to friendly name if available
            key = str(pred)
            friendly = label_map.get(key) if label_map else None
            if not friendly and key.isdigit():
                friendly = 'Diet ' + key
            if friendly:
                display = f'{friendly} (raw: {key})'
            else:
                display = str(pred)
        except Exception as e:
            display = f'ERROR: {e}'
        print(f' age={a:>5} -> {display}   (features used: {features})')


if __name__ == '__main__':
    main()
