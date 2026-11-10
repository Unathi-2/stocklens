const NA = "n/a";
const LOCALE = "en-GB"; // 1,234.56

export function formatNumber(value: number | null | undefined, digits = 2): string {
  if (value == null || Number.isNaN(value)) return NA;
  return value.toLocaleString(LOCALE, { minimumFractionDigits: digits, maximumFractionDigits: digits });
}

export function formatPct(value: number | null | undefined, digits = 2): string {
  if (value == null || Number.isNaN(value)) return NA;
  const sign = value > 0 ? "+" : "";
  return `${sign}${formatNumber(value, digits)}%`;
}

export function formatCompact(value: number | null | undefined): string {
  if (value == null || Number.isNaN(value)) return NA;
  return new Intl.NumberFormat(LOCALE, { notation: "compact", maximumFractionDigits: 2 }).format(value);
}

/** Yahoo quotes JSE equities in cents (ZAc). Show them in rand. */
export function formatMoney(value: number | null | undefined, currency: string): string {
  if (value == null || Number.isNaN(value)) return NA;
  switch (currency) {
    case "ZAc":
      return `R${formatNumber(value / 100)}`;
    case "ZAR":
      return `R${formatNumber(value)}`;
    case "USD":
      return `$${formatNumber(value)}`;
    default:
      return `${currency} ${formatNumber(value)}`;
  }
}

/** Indices are quoted in points, not money. */
export function formatPrice(value: number | null | undefined, currency: string, assetType = "equity"): string {
  return assetType === "index" ? formatNumber(value) : formatMoney(value, currency);
}

export function currencyLabel(currency: string): string {
  return currency === "ZAc" ? "ZAR" : currency;
}

export function formatDate(iso: string | null | undefined): string {
  if (!iso) return NA;
  const d = new Date(`${iso}T00:00:00`);
  return d.toLocaleDateString(LOCALE, { day: "numeric", month: "short", year: "numeric" });
}
