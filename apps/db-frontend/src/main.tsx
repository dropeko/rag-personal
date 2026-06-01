import { createRoot } from "react-dom/client";
import App from "./App.js";
import "./index.css";
import { configureApi } from "@data-platforms/db-frontend-lib/api";

configureApi(import.meta.env.VITE_API_BASE);

const root = document.getElementById("root");
if (!root) throw new Error("Root element not found");
createRoot(root).render(<App />);