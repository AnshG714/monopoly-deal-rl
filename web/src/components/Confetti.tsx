import type { CSSProperties } from "react";
import { useMemo } from "react";

const CONFETTI_COLORS = [
  "#ef4444",
  "#3b82f6",
  "#22c55e",
  "#eab308",
  "#ec4899",
  "#f97316",
  "#8b5cf6",
  "#06b6d4",
];

const PIECE_COUNT = 72;

interface ConfettiPiece {
  id: number;
  left: number;
  delay: number;
  duration: number;
  color: string;
  width: number;
  height: number;
  drift: number;
  spin: number;
  shape: "rect" | "strip";
}

function createPieces(): ConfettiPiece[] {
  return Array.from({ length: PIECE_COUNT }, (_, id) => ({
    id,
    left: Math.random() * 100,
    delay: Math.random() * 0.8,
    duration: 2.4 + Math.random() * 2.2,
    color: CONFETTI_COLORS[id % CONFETTI_COLORS.length]!,
    width: 6 + Math.random() * 8,
    height: 4 + Math.random() * 10,
    drift: -80 + Math.random() * 160,
    spin: 360 + Math.random() * 720,
    shape: Math.random() > 0.5 ? "rect" : "strip",
  }));
}

export function Confetti() {
  const pieces = useMemo(() => createPieces(), []);

  return (
    <div
      className="pointer-events-none fixed inset-0 z-50 overflow-hidden"
      aria-hidden
    >
      {pieces.map((piece) => (
        <span
          key={piece.id}
          className="confetti-piece absolute top-0 opacity-0"
          style={
            {
              left: `${piece.left}%`,
              width: piece.width,
              height: piece.height,
              backgroundColor: piece.color,
              borderRadius: piece.shape === "rect" ? "2px" : "9999px",
              animationDuration: `${piece.duration}s`,
              animationDelay: `${piece.delay}s`,
              "--confetti-drift": `${piece.drift}px`,
              "--confetti-spin": `${piece.spin}deg`,
            } as CSSProperties
          }
        />
      ))}
    </div>
  );
}
