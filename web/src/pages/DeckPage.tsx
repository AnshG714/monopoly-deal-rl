import { useEffect, useMemo, useState } from "react";

import { getDeck } from "@/api/client";
import type { Card as DeckCard } from "@/api/types";
import { Card as CardView } from "@/components/card";
import { Button } from "@/components/ui/button";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { cardIdentity, uniqueCardsByGroup } from "@/lib/deckGallery";

export function DeckPage() {
  const [cards, setCards] = useState<DeckCard[]>([]);
  const [total, setTotal] = useState(0);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let active = true;

    void getDeck()
      .then((deck) => {
        if (!active) return;
        setCards(deck.cards);
        setTotal(deck.total);
        setError(null);
      })
      .catch((err) => {
        if (!active) return;
        setError(err instanceof Error ? err.message : "Failed to load deck");
      })
      .finally(() => {
        if (active) setLoading(false);
      });

    return () => {
      active = false;
    };
  }, []);

  const groups = useMemo(() => uniqueCardsByGroup(cards), [cards]);
  const uniqueCount = useMemo(
    () => groups.reduce((sum, group) => sum + group.cards.length, 0),
    [groups],
  );

  return (
    <main className="mx-auto flex min-h-screen max-w-6xl flex-col gap-6 p-4 md:p-6">
      <header className="flex flex-wrap items-end justify-between gap-4">
        <div>
          <h1 className="text-2xl font-semibold tracking-tight">
            Deck preview
          </h1>
          <p className="text-muted-foreground text-sm">
            One example of each card type from the engine registry
            {total > 0 && ` (${uniqueCount} unique · ${total} total in deck)`}
          </p>
        </div>
        <nav className="flex gap-2">
          <Button variant="outline" asChild>
            <a href="/">Game</a>
          </Button>
          <Button asChild>
            <a href="/deck">Deck</a>
          </Button>
        </nav>
      </header>

      {loading && (
        <p className="text-muted-foreground text-sm" role="status">
          Loading deck…
        </p>
      )}

      {error && (
        <p className="text-destructive text-sm" role="alert">
          {error}
        </p>
      )}

      {!loading &&
        !error &&
        groups.map((group) => (
          <section key={group.label} className="space-y-3">
            <div className="flex items-baseline justify-between gap-2">
              <h2 className="text-lg font-medium">{group.label}</h2>
              <span className="text-muted-foreground text-sm">
                {group.cards.length} types
              </span>
            </div>
            <div className="flex flex-wrap gap-4">
              {group.cards.map((card) => (
                <Card key={cardIdentity(card)} className="w-fit py-4">
                  <CardHeader className="px-4 pb-2">
                    <CardTitle className="text-sm">
                      {card.display_name ?? card.name ?? card.type}
                    </CardTitle>
                    <CardDescription className="text-xs">
                      ${card.value}M
                    </CardDescription>
                  </CardHeader>
                  <CardContent className="px-4">
                    <CardView card={card} />
                  </CardContent>
                </Card>
              ))}
            </div>
          </section>
        ))}
    </main>
  );
}
