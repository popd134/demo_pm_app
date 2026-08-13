import { Card } from "../components/ui";

/** Simple placeholder page for sections still under construction (WBS 1.4.2). */
export function PlaceholderPage({ title, note }: { title: string; note: string }) {
  return (
    <div>
      <h2 className="section-heading">{title}</h2>
      <Card>
        <p className="section-subtle">{note}</p>
      </Card>
    </div>
  );
}
