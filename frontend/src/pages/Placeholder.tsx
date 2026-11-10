import ApiStatus from "../components/ApiStatus";

export default function Placeholder({ title, note }: { title: string; note?: string }) {
  return (
    <div className="space-y-3">
      <h1 className="text-2xl font-semibold">{title}</h1>
      {note && <p className="text-slate-400">{note}</p>}
      <ApiStatus />
    </div>
  );
}
