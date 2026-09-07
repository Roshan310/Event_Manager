import Link from "next/link";
import { Logo } from "@/components/shell";
import { Button } from "@/components/ui/button";
export default function NotFound() {
  return (
    <div className="standalone-message">
      <Logo />
      <h1>A little off the beaten path.</h1>
      <p>This page isn’t here, but your next good experience could be.</p>
      <Button asChild>
        <Link href="/">Back to Evently</Link>
      </Button>
    </div>
  );
}
