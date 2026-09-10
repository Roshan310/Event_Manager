import { CheckIn } from "@/components/check-in";
export default async function Page({
  params,
}: {
  params: Promise<{ id: string }>;
}) {
  const { id } = await params;
  return <CheckIn id={id} />;
}
