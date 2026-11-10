import { EmptyState } from "../components/ui/Feedback";

export default function ComingSoon({ title, children }: { title: string; children: string }) {
  return (
    <div className="space-y-6">
      <h1 className="font-serif text-3xl font-medium">{title}</h1>
      <EmptyState title={`${title} is not built yet`}>{children}</EmptyState>
    </div>
  );
}
