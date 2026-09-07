import { Suspense } from "react";
import { Discovery } from "@/components/discovery";
import { Loading } from "@/components/feedback";
export default async function Events({
  searchParams,
}: {
  searchParams: Promise<Record<string, string | string[] | undefined>>;
}) {
  const params = await searchParams;
  return (
    <Suspense fallback={<Loading />}>
      <Discovery key={JSON.stringify(params)} />
    </Suspense>
  );
}
