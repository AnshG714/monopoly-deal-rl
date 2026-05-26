

# Rollout Strategy

This document guides a simple heuristic rollout strategy that will be used to guide a coding assistant to write a rollout policy in `rollout.py`.

Note that this policy is based on the assumption of a full information game, which is unrealistic for Monopoly Deal, but is a good starting ground to work towards training an RL agent that can play the game via MCTS and its variants.

## On your turn

Note: these priorities should be followed based on what `legal_moves()`  returns. 

### Priority 1: Completing sets

The game needs 3 sets to win, so we should prioritize completing sets. Prefer these operations in order.

- If you possess a deal breaker which cannot be 'Just-Say-No'd (henceforth aliased as JSN), play the deal breaker to steal the set.
  - This can occur in various situations - if you have a deal breaker and the opponent doesn't, you can play the deal breaker safely.
  - If you have a deal breaker and a JSN, and the opponent only has one JSN, then you can play it safely (since you can JSN the JSN)
- Play a Sly Deal if doing so completes a set
- Play a Forced Deal if doing so completes a set, AND it doesn't break one of your own sets.
- Play a property or a wild card from your hand if it helps you complete a set.
- Move a wild card from another incomplete pile if it helps you complete a set.

### Priority 2: Charging money

It is important to have some money in the bank to avoid paying in properties if the opponent charges you! You can either put down your own money or charge players rent, but it's typically better to charge players so we can deplete their board strength.

Your options for charging rent are rent cards, "Double the rent" (with a rent card), "It's my birthday" and a "Debt Collector". Simply play the czrd that can charget the opponent the highest amount of money.

### Priority 3: Putting down properties

You need to make progress towards putting down properties to get to 3 sets! Put down properties in this order:

- If you have a rent card for a color, put down as many colors of that rent as you can
- Put down cards from the lowest possible value
- If there is a tie, prefer cards that are 'single color' (as opposed to wildcards)

### Priority 4: Putting down money

If charging is not an option, you still need to put down money to defend your properties!

- Put down money (not action cards being discarded as money - we'll tackle that later). Start from the lowest value first.
- If you have 2 or more "Pass Go" cards, you can play those as money. Still keep 1 in hand if possible.
- If you have no money, but you have properties (which are in danger if the opponent charges you), then discard action cards as money. Go from the lowest value card. DO NOT DISCARD A JUST SAY NO OR A DEAL BREAKER!

### Priority 5: Misc actions

Some actions have already been discussed above, but there are still a few options left. Here are things to do, in order of priority:

- Play a sly deal if you have one, stealing the highest value property that's possible.
- Play a house/hotel whenever possible on your complete sets.
- Forced Deal (swap one of your board properties for one of theirs — both piles must stay incomplete)
  - Score each legal swap as **net board improvement**: progress you gain minus progress you lose. Prefer the highest-scoring swap; skip Forced Deal entirely if every swap is net-negative.
  - **What to take** (in order of preference among legal targets):
    - A card that completes one of your sets (already covered in Priority 1).
    - Else, a card that advances your most promising incomplete pile (fewest cards still needed to complete; break ties by higher face value / rent ladder).
    - Else, disruption: pull a card from an opponent pile that is one card away from complete — especially when they already have 2 complete sets.
  - **What to give** (among cards that make the swap legal):
    - Prefer giving from a **single-card pile** in a color you are not building; the empty pile is removed and you consolidate board space.
    - Else, give the lowest-value card from an incomplete pile where you still stay close to finishing (ideally still within one card of complete after the swap).
    - Avoid giving wilds or dual-color cards that are doing useful work in their current pile unless the incoming card completes a set for you.
    - Never give a card that drops one of your piles from “one away” to “two or more away” unless the swap completes a different set.
  - Tie-break among equally scored swaps: take the opponent’s highest face-value card, or the one from their most advanced incomplete pile.
- Pass go: Play this 60% of the time.

### End turn

If no legal move matches Priorities 1–5, apply `EndTurn`.

## End-of-turn discard

When `legal_moves()` returns only `DiscardCards`, **score each move in that list** and apply the best one. For each `DiscardCards`, score it by the cards it keeps (hand indices *not* in `hand_indices`): higher is better. Prefer keeping JSN, Deal Breaker, properties, and rent cards for colors on your board; among what you'd give up, lowest face value first (plain money and Double the Rent before useful action cards). Pick the highest-scoring move.

## Paying debt

When `PaymentDue` is pending, **score each move in `legal_moves()`** and apply the best one.

### JSN (prefer over paying)

- If playing JSN can cancel the debt and you win the chain (same rule as Priority 1), pick that over any `PayDebt`.
- During an active JSN chain on this debt, counter with JSN if you can win the chain; otherwise `PassJustSayNo`.

### PayDebt — rank each legal move (best first)

Compare moves in this order; **only use the next step when tied**:

1. **Does not break a complete set** — if any legal move avoids this, drop all moves that take a card from a complete pile. This beats total value: never break a set just to pay a few less million from the bank.
2. **Bank-only** — no entries in `property_card_indices`.
3. **Lowest total value paid** — sum face values of all bank cards and properties given up.
4. **Least progress lost** — among property payments, prefer cards from incomplete piles that are furthest from complete; lowest face value first.

Tie-break: prefer the move that gives up fewer property cards.

## Defending steals

When a deal interrupt is pending (`SlyDealPending`, `ForcedDealPending`, or `DealBreakerPending`), **score each move in `legal_moves()`** and apply the best one. Counter with JSN if you win the chain; always do so against a Deal Breaker. Otherwise `PassJustSayNo`.

## JSN realism tuning

To create a more realistic opponent during rollouts, the policy does not always play JSN optimally based on chain math. Instead:

- **Deal Breakers**: always counter with JSN from either side — losing a complete set is too costly to let through.
- **Rent / debt**: JSN probability scales linearly with the charge amount, from 0% at 1M to 100% at 14M+. Small debts are cheaper to just pay off; large ones are worth burning a JSN. Once a chain is started, mid-chain decisions still follow optimal JSN-count logic.
