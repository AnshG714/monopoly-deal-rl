import torch
from torch.utils.data import DataLoader
from pathlib import Path

from .dataset import EncodedDataset, load_encoded, split_by_seed
from .model import ValueNet

EPOCHS = 40
BATCH_SIZE = 256
LR = 1e-4
WEIGHT_DECAY = 1e-3
PATIENCE = 5


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
    if torch.cuda.is_available():
        device = torch.device("cuda")
    elif torch.backends.mps.is_available():
        device = torch.device("mps")
    else:
        device = torch.device("cpu")
    print(f"Using device: {device}")

    data = load_encoded(
        Path(__file__).parent.parent / "data" / "encoded" / "data_10000_2500.pt"
    )
    train, val = split_by_seed(data)
    train_loader = DataLoader(
        EncodedDataset(train), batch_size=BATCH_SIZE, shuffle=True
    )
    val_loader = DataLoader(
        EncodedDataset(val), batch_size=BATCH_SIZE, shuffle=False
    )

    model = ValueNet().to(device)
    criterion = torch.nn.BCEWithLogitsLoss()
    optimizer = torch.optim.Adam(
        model.parameters(), lr=LR, weight_decay=WEIGHT_DECAY
    )

    best_val_loss = float("inf")
    stall = 0
    ckpt_path = Path(__file__).parent.parent / "outputs" / "best_value_net.pth"
    ckpt_path.parent.mkdir(parents=True, exist_ok=True)

    for epoch in range(EPOCHS):
        train_loss = train_epoch(model, train_loader, optimizer, criterion, device)
        val_loss = validate_epoch(model, val_loader, criterion, device)
        print(
            f"Epoch {epoch+1}, Train Loss: {train_loss:.4f}, Val Loss: {val_loss:.4f}"
        )
        if val_loss < best_val_loss - 1e-4:
            best_val_loss = val_loss
            stall = 0
            torch.save(model.state_dict(), ckpt_path)
            print(f"  saved best -> {ckpt_path} (val={best_val_loss:.4f})")
        else:
            stall += 1
            if stall >= PATIENCE:
                print(f"Early stop at epoch {epoch+1} (best val={best_val_loss:.4f})")
                break


if __name__ == "__main__":
    main()
