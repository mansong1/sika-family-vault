import { Suspense } from "react";
import LandingPage from "@/components/LandingPage";

export default function Home() {
  return (
    <Suspense fallback={<div className="skeleton min-h-screen" />}>
      <LandingPage />
    </Suspense>
  );
}
