# Frontend and design system

## Principles

1. Numbers first. Figures are large, aligned and never decorative.
2. Colour never works alone. Gains and losses carry an arrow and a sign.
3. One quiet border. Panels have a hairline rule and no shadow.
4. Plain words. Labels use sentence case and say what the thing is.

## Tokens

Defined in src/index.css as CSS variables and mapped to Tailwind names: bg, panel, panel2, rule, ink, muted, accent, up, down. Dark is the default. Light is a cool paper theme. The choice is stored in localStorage with a safe fallback.

## Type

Newsreader (serif) for titles and large figures. IBM Plex Sans for text and table figures, with tabular numbers.

## Components (src/components)

ui: Panel, Ledger and MetricCard, PriceChange, Badge, Button, Tabs, RangeSelector, Select, DataTable, StockCard, SearchBar, Icon, and the feedback set (LoadingSpinner, Skeleton, ErrorMessage, EmptyState).
layout: AppLayout, Sidebar, Navbar, ApiStatus.

Open /design in the running app to see all of them in both themes.

## Data access

src/services/api.ts is the only place that calls the backend. src/hooks/useApi.ts handles loading, errors and stale responses.

## Prices

Yahoo quotes JSE equities in cents. Their currency is stored as ZAc and formatMoney shows them in rand. Indices are shown as points.
