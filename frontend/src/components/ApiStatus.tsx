import { useEffect, useState } from "react";

export default function ApiStatus() {
  const [status, setStatus] = useState<"checking" | "online" | "offline">("checking");

  useEffect(() => {
    fetch("/health")
      .then((r) => r.json())
      .then((d) => setStatus(d.status === "ok" ? "online" : "offline"))
      .catch(() => setStatus("offline"));
  }, []);

  const color =
    status === "online" ? "text-emerald-400" : status === "offline" ? "text-rose-400" : "text-slate-400";

  return <p className={`text-sm ${color}`}>API: {status}</p>;
}
