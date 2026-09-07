import { EventDetail } from "@/components/event-detail";
export default async function Page({
  params,
}: {
  params: Promise<{ id: string }>;
}) {
  return <EventDetail id={(await params).id} />;
}
