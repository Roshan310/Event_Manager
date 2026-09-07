import { Suspense } from "react";
import { Discovery } from "@/components/discovery";
import { Loading } from "@/components/feedback";
export default function Home() {
  return (
    <Suspense fallback={<Loading />}>
      <Discovery home />
    </Suspense>
  );
}
