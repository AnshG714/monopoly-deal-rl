import torch
from torch.utils.data import DataLoader
from pathlib import Path

from .dataset import load_examples, split_by_seed, DecisionRowDataset
from .model import ValueNet

EPOCHS = 100


def train_epoch(
    model: torch.nn.Module,
    train_loader: DataLoader,
    optimizer: torch.optim.Optimizer,
    criterion: torch.nn.Module,
    device: torch.device,
) -> float:
    model.train()
    total_loss = 0.0
    n_samples = 0
    for x, y in train_loader:
        x, y = x.to(device), y.to(device)
        optimizer.zero_grad()
        batch_size = x.size(0)
        logits = model(x)
        loss = criterion(logits, y)
        loss.backward()
        optimizer.step()
        total_loss += loss.item() * batch_size
        n_samples += batch_size
    return total_loss / n_samples


def validate_epoch(
    model: torch.nn.Module,
    val_loader: DataLoader,
    criterion: torch.nn.Module,
    device: torch.device,
) -> float:
    model.eval()
    total_loss = 0.0
    n_samples = 0
    with torch.no_grad():
        for x, y in val_loader:
            x, y = x.to(device), y.to(device)
            batch_size = x.size(0)
            logits = model(x)
            loss = criterion(logits, y)
            total_loss += loss.item() * batch_size
            n_samples += batch_size
    return total_loss / n_samples


def main():
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    print(f"Using device: {device}")

    examples = load_examples(
        Path(__file__).parent.parent / "data" / "self_play" / "data_2500_0.csv"
    )
    train, val = split_by_seed(examples)
    train_loader = DataLoader(DecisionRowDataset(train), batch_size=128, shuffle=True)
    val_loader = DataLoader(DecisionRowDataset(val), batch_size=128, shuffle=False)

    model = ValueNet().to(device)
    criteron = torch.nn.BCEWithLogitsLoss()
    optimizer = torch.optim.Adam(model.parameters(), lr=1e-3)

    best_val_loss = float("inf")
    for epoch in range(EPOCHS):
        train_loss = train_epoch(model, train_loader, optimizer, criteron, device)
        val_loss = validate_epoch(model, val_loader, criteron, device)
        print(
            f"Epoch {epoch+1}, Train Loss: {train_loss:.4f}, Val Loss: {val_loss:.4f}"
        )
        if val_loss < best_val_loss:
            best_val_loss = val_loss
            torch.save(model.state_dict(), "best_model.pth")
        print(
            f"Epoch {epoch+1}, Train Loss: {train_loss:.4f}, Val Loss: {val_loss:.4f}"
        )


if __name__ == "__main__":
    main()
