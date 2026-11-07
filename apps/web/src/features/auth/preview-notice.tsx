import { InlineMessage } from "@/components/ui/states";

export function PreviewNotice() {
  return (
    <InlineMessage tone="info" title="Phase 1 preview" className="text-xs">
      These fields are fully interactive for design review. Accounts, sessions and email
      delivery are connected in Phase 2, so nothing is submitted.
    </InlineMessage>
  );
}
