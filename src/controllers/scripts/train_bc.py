#!/usr/import/env python3
import os
import sys
import glob
import argparse
import numpy as np
import torch
import torch.nn as nn
from torch.utils.data import TensorDataset, DataLoader
import matplotlib.pyplot as plt

sys.path.insert(0, os.path.dirname(__file__))
from policy_network import PolicyNetwork

def main():
    parser = argparse.ArgumentParser(description='Train behaviour cloning policy')
    parser.add_argument('--epochs', type=int, default=300)
    parser.add_argument('--lr', type=float, default=1e-3)
    parser.add_argument('--batch-size', type=int, default=64)
    parser.add_argument('--filter-zeros', action='store_true', default=True,
                        help='Drop frames where both action components are zero')
    args = parser.parse_args()

    pkg_root = os.path.expanduser('~/dagger_ws/src/controllers')
    data_dir = os.path.join(pkg_root, 'data', 'bc_data')
    weights_dir = os.path.join(pkg_root, 'weights')
    os.makedirs(weights_dir, exist_ok=True)

    all_scans = []
    all_actions = []

    files = sorted(glob.glob(os.path.join(data_dir, 'lap_*.npz')))
    if not files:
        print(f'[ERROR] No lap_*.npz files found in: {data_dir}')
        sys.exit(1)

    for fpath in files:
        data = np.load(fpath)
        scans = data['scans'].astype(np.float32)
        actions = data['actions'].astype(np.float32)

        if args.filter_zeros:
            valid = np.any(actions != 0.0, axis=1)
            scans = scans[valid]
            actions = actions[valid]
            dropped = (~valid).sum()
            print(f'  Loaded {os.path.basename(fpath)}: '
                  f'{len(scans)} samples  ({dropped} zero-action frames dropped)')
        else:
            print(f'  Loaded {os.path.basename(fpath)}: {len(scans)} samples')

        all_scans.append(scans)
        all_actions.append(actions)

    scans = np.vstack(all_scans)
    actions = np.vstack(all_actions)

    N, D = scans.shape
    print(f'\nDataset: {N} samples, {D} LiDAR rays')
    
    MAX_RANGE = 3.5
    scans = np.clip(scans / MAX_RANGE, 0.0, 1.0)

    split = int(0.9 * N)
    idx = np.random.permutation(N)
    train_idx = idx[:split]
    val_idx = idx[split:]

    train_ds = TensorDataset(torch.tensor(scans[train_idx]), torch.tensor(actions[train_idx]))
    val_ds = TensorDataset(torch.tensor(scans[val_idx]), torch.tensor(actions[val_idx]))

    train_loader = DataLoader(train_ds, batch_size=args.batch_size, shuffle=True)
    val_loader = DataLoader(val_ds, batch_size=256)

    device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
    model = PolicyNetwork(input_dim=D, output_dim=2).to(device)
    optimizer = torch.optim.Adam(model.parameters(), lr=args.lr)
    loss_fn = nn.MSELoss()
    scheduler = torch.optim.lr_scheduler.ReduceLROnPlateau(optimizer, mode='min', patience=10, factor=0.5)

    best_val_loss = float('inf')
    best_epoch = 1
    patience = 50
    patience_counter = 0
    save_path = os.path.join(weights_dir, 'bc_policy.pt')

    for epoch in range(1, args.epochs + 1):
        model.train()
        train_loss = 0.0
        for obs, act in train_loader:
            obs, act = obs.to(device), act.to(device)
            pred = model(obs)
            loss = loss_fn(pred, act)
            optimizer.zero_grad()
            loss.backward()
            optimizer.step()
            train_loss += loss.item() * len(obs)
        train_loss /= len(train_ds)

        model.eval()
        val_loss = 0.0
        with torch.no_grad():
            for obs, act in val_loader:
                obs, act = obs.to(device), act.to(device)
                pred = model(obs)
                val_loss += loss_fn(pred, act).item() * len(obs)
        val_loss /= max(len(val_ds), 1)
        scheduler.step(val_loss)

        if epoch % 10 == 0 or epoch == 1:
            print(f'Epoch {epoch:03d} | Train: {train_loss:.4f} | Val: {val_loss:.4f}')

        if val_loss < best_val_loss:
            best_val_loss = val_loss
            best_epoch = epoch
            patience_counter = 0
            torch.save(model.state_dict(), save_path)
        else:
            patience_counter += 1
            if patience_counter >= patience:
                print(f'Early stopping at epoch {epoch}. Best was epoch {best_epoch}.')
                break

    print(f'Saved: {save_path}')

if __name__ == '__main__':
    main()
