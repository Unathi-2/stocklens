import { useEffect, useState } from "react";
import Badge from "../ui/Badge";

export default function ApiStatus() {
  const [status, setStatus] = useState<"checking" | "online" | "offline">("checking");

  useEffect(() => {
    let cancelled = false;
    fetch("/health")
      .then((r) => r.json())
      .then((d) => !cancelled && setStatus(d.status === "ok" ? "online" : "offline"))
      .catch(() => !cancelled && setStatus("offline"));
    return () => {
      cancelled = true;
    };
  }, []);

  const tone = status === "online" ? "up" : status === "offline" ? "down" : "neutral";
  return <Badge tone={tone}>API {status}</Badge>;
}
