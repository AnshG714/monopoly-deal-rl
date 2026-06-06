import { StrictMode } from "react";
import { createRoot } from "react-dom/client";
import "./index.css";
import App from "./App.tsx";
import { DeckPage } from "./pages/DeckPage.tsx";

const isDeckRoute = window.location.pathname === "/deck";

createRoot(document.getElementById("root")!).render(
  <StrictMode>{isDeckRoute ? <DeckPage /> : <App />}</StrictMode>,
);
