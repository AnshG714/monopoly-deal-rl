import { useEffect, useMemo, useState } from "react";

import { getDeck } from "../api/client";
import type { Card as CardType } from "../api/types";
import { Card } from "./Card";

interface DeckGroup {
  label: string;
  cards: CardType[];
}

function groupLabel(card: CardType): string {
  if (card.property_kind === "single") return "Properties";
  if (card.property_kind === "multi" || card.property_kind === "wild") {
    return "Property Wilds";
  }
  if (card.type === "rent") return "Rent Cards";
  if (card.type === "money") return "Money";
  if (card.action_type) return "Actions";
  return "Other";
}

function groupCards(cards: CardType[]): DeckGroup[] {
  const order = [
    "Properties",
    "Property Wilds",
    "Actions",
    "Rent Cards",
    "Money",
    "Other",
  ];
  const groups = new Map<string, CardType[]>();

  for (const card of cards) {
    const label = groupLabel(card);
    groups.set(label, [...(groups.get(label) ?? []), card]);
  }

  return order
    .map((label) => ({ label, cards: groups.get(label) ?? [] }))
    .filter((group) => group.cards.length > 0);
}

export function DeckGallery() {
  const [cards, setCards] = useState<CardType[]>([]);
  const [total, setTotal] = useState(0);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let isMounted = true;

    async function loadDeck() {
      try {
        const deck = await getDeck();
        if (!isMounted) return;
        setCards(deck.cards);
        setTotal(deck.total);
        setError(null);
      } catch (err) {
        if (!isMounted) return;
        setError(err instanceof Error ? err.message : "Failed to load deck.");
      } finally {
        if (isMounted) setLoading(false);
      }
    }

    void loadDeck();

    return () => {
      isMounted = false;
    };
  }, []);

  const groups = useMemo(() => groupCards(cards), [cards]);

  return (
    <main className="deck-page">
      <section className="deck-hero">
        <div>
          <p className="deck-hero__eyebrow">Card renderer preview</p>
          <h2>Full deck</h2>
          <p>
            Browse the canonical Monopoly Deal deck using the same serialized
            card data the game UI receives.
          </p>
        </div>
        <span className="deck-hero__count">{total || cards.length} cards</span>
      </section>

      {loading && (
        <div className="banner banner--loading" role="status">
          Loading deck...
        </div>
      )}

      {error && (
        <div className="banner banner--error" role="alert">
          {error}
        </div>
      )}

      {!loading &&
        !error &&
        groups.map((group) => (
          <section className="deck-section" key={group.label}>
            <header className="deck-section__header">
              <h3>{group.label}</h3>
              <span>{group.cards.length}</span>
            </header>
            <div className="deck-grid">
              {group.cards.map((card, index) => (
                <Card
                  key={`${group.label}-${card.display_name ?? card.type}-${index}`}
                  card={card}
                />
              ))}
            </div>
          </section>
        ))}
    </main>
  );
}
