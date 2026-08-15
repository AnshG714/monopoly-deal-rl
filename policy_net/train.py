"""Minimal policy-net training on materialized visit-share examples."""

from __future__ import annotations

import argparse
from pathlib import Path

import torch
import torch.nn.functional as F
from torch.utils.data import DataLoader, Dataset

from policy_net.model import PolicyNet

DEFAULT_DATA = (
    Path(__file__).resolve().parent.parent / "data" / "encoded" / "smoke_policy.pt"
)
CKPT = Path(__file__).resolve().parent.parent / "outputs" / "best_policy_net.pth"
EPOCHS = 20
LR = 1e-3
WEIGHT_DECAY = 1e-3
VAL_FRACTION = 0.2


class PolicyExampleDataset(Dataset):
    def __init__(self, examples: list[dict]):
        self.examples = examples

    def __len__(self) -> int:
        return len(self.examples)

    def __getitem__(self, idx: int) -> dict:
        return self.examples[idx]


def collate_keep_list(batch: list[dict]) -> list[dict]:
    return batch


def split_by_seed(examples: list[dict], val_fraction: float = VAL_FRACTION):
    seeds = sorted({int(ex["seed"]) for ex in examples})
    n_val = max(1, int(len(seeds) * val_fraction))
    val_seeds = set(seeds[-n_val:])
    train = [ex for ex in examples if int(ex["seed"]) not in val_seeds]
    val = [ex for ex in examples if int(ex["seed"]) in val_seeds]
    return train, val


def batch_kl_loss(
    model: PolicyNet, batch: list[dict], device: torch.device
) -> torch.Tensor:
    losses = []
    for ex in batch:
        state = ex["state"].to(device)
        actions = ex["actions"].to(device)
        target = ex["target"].to(device)
        # Broadcast state across K actions: [K, STATE_DIM]
        state_b = state.unsqueeze(0).expand(actions.size(0), -1)
        logits = model(state_b, actions)
        log_probs = F.log_softmax(logits, dim=0)
        losses.append(F.kl_div(log_probs, target, reduction="sum"))
    return torch.stack(losses).mean()


@torch.no_grad()
def eval_loss(model: PolicyNet, loader: DataLoader, device: torch.device) -> float:
    model.eval()
    total = 0.0
    n = 0
    for batch in loader:
        loss = batch_kl_loss(model, batch, device)
        total += float(loss.item()) * len(batch)
        n += len(batch)
    return total / max(n, 1)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--data",
        type=Path,
        default=DEFAULT_DATA,
        help="materialized policy .pt file",
    )
    args = parser.parse_args()

    if torch.backends.mps.is_available():
        device = torch.device("mps")
    elif torch.cuda.is_available():
        device = torch.device("cuda")
    else:
        device = torch.device("cpu")
    print(f"device={device} data={args.data}", flush=True)

    payload = torch.load(args.data, weights_only=False)
    train_ex, val_ex = split_by_seed(payload["examples"])
    print(f"train={len(train_ex)} val={len(val_ex)}", flush=True)

    train_loader = DataLoader(
        PolicyExampleDataset(train_ex),
        batch_size=32,
        shuffle=True,
        collate_fn=collate_keep_list,
    )
    val_loader = DataLoader(
        PolicyExampleDataset(val_ex),
        batch_size=64,
        shuffle=False,
        collate_fn=collate_keep_list,
    )

    model = PolicyNet().to(device)
    opt = torch.optim.Adam(model.parameters(), lr=LR, weight_decay=WEIGHT_DECAY)

    best_val = float("inf")
    for epoch in range(1, EPOCHS + 1):
        model.train()
        total = 0.0
        n = 0
        for batch in train_loader:
            opt.zero_grad()
            loss = batch_kl_loss(model, batch, device)
            loss.backward()
            opt.step()
            total += float(loss.item()) * len(batch)
            n += len(batch)
        train_loss = total / max(n, 1)
        val_loss = eval_loss(model, val_loader, device)
        print(
            f"Epoch {epoch}, Train KL: {train_loss:.4f}, Val KL: {val_loss:.4f}",
            flush=True,
        )
        if val_loss < best_val - 1e-4:
            best_val = val_loss
            CKPT.parent.mkdir(parents=True, exist_ok=True)
            torch.save(model.state_dict(), CKPT)
            print(f"  saved best -> {CKPT}", flush=True)

    print(f"best_val_kl={best_val:.4f}", flush=True)


if __name__ == "__main__":
    main()
