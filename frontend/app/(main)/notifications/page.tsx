import { Notifications } from "@/components/workflows";
import { RequireAuth } from "@/components/feedback";
export default function Page() {
  return (
    <RequireAuth>
      <Notifications />
    </RequireAuth>
  );
}
