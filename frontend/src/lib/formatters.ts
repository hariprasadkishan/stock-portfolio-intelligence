/**
 * Professional financial formatting utilities.
 * Handles currency (INR, USD), percentages, ratios, and dates.
 */

export function formatCurrency(
  amount: number | null | undefined,
  currency: string = "USD",
  compact: boolean = false
): string {
  if (amount === null || amount === undefined || isNaN(amount)) {
    return "N/A";
  }

  const curr = currency ? currency.toUpperCase() : "USD";
  const locale = curr === "INR" ? "en-IN" : "en-US";

  try {
    if (compact) {
      return new Intl.NumberFormat(locale, {
        style: "currency",
        currency: curr,
        notation: "compact",
        maximumFractionDigits: 2,
      }).format(amount);
    }

    return new Intl.NumberFormat(locale, {
      style: "currency",
      currency: curr,
      minimumFractionDigits: 2,
      maximumFractionDigits: 2,
    }).format(amount);
  } catch {
    const symbol = curr === "INR" ? "₹" : curr === "USD" ? "$" : `${curr} `;
    return `${symbol}${amount.toLocaleString(locale, { minimumFractionDigits: 2, maximumFractionDigits: 2 })}`;
  }
}

export function formatPercent(
  value: number | null | undefined,
  decimals: number = 2,
  includeSign: boolean = false
): string {
  if (value === null || value === undefined || isNaN(value)) {
    return "N/A";
  }

  const pct = value * 100;
  const formatted = pct.toFixed(decimals) + "%";

  if (includeSign && pct > 0) {
    return "+" + formatted;
  }
  return formatted;
}

export function formatRatio(
  value: number | null | undefined,
  decimals: number = 2
): string {
  if (value === null || value === undefined || isNaN(value)) {
    return "N/A";
  }
  return value.toFixed(decimals);
}

export function formatDate(dateString: string | null | undefined): string {
  if (!dateString) return "N/A";
  try {
    // If format is YYYY-MM-DD
    const parts = dateString.split("-");
    if (parts.length === 3) {
      const year = parseInt(parts[0], 10);
      const month = parseInt(parts[1], 10) - 1;
      const day = parseInt(parts[2], 10);
      const d = new Date(year, month, day);
      return d.toLocaleDateString("en-US", {
        month: "short",
        day: "2-digit",
        year: "numeric",
      });
    }
    const d = new Date(dateString);
    if (isNaN(d.getTime())) return dateString;
    return d.toLocaleDateString("en-US", {
      month: "short",
      day: "2-digit",
      year: "numeric",
    });
  } catch {
    return dateString;
  }
}
