import { Link } from "react-router-dom";
import Badge from "./Badge";
import PriceChange from "./PriceChange";
import { formatPrice } from "../../utils/format";

interface Props {
  symbol: string;
  name: string;
  exchange: string;
  currency: string;
  price: number;
  changePct: number | null;
  assetType?: string;
}

export default function StockCard({ symbol, name, exchange, currency, price, changePct, assetType }: Props) {
  return (
    <Link
      to={`/stocks/${encodeURIComponent(symbol)}?exchange=${encodeURIComponent(exchange)}`}
      className="block rounded-md border border-rule bg-panel p-4 transition-colors hover:bg-panel2"
    >
      <div className="flex items-start justify-between gap-2">
        <div className="min-w-0">
          <div className="font-serif text-xl leading-tight">{symbol}</div>
          <div className="truncate text-sm text-muted">{name}</div>
        </div>
        <Badge>{exchange}</Badge>
      </div>
      <div className="mt-4 flex items-baseline justify-between">
        <span className="num text-lg font-medium">{formatPrice(price, currency, assetType)}</span>
        <PriceChange value={changePct} />
      </div>
    </Link>
  );
}
