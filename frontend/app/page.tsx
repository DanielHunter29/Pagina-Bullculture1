import { Hero } from "@/components/sections/Hero";
import { CategoryHighlights } from "@/components/sections/CategoryHighlights";
import { ScienceSection } from "@/components/sections/ScienceSection";

export default function Home() {
  return (
    <>
      <Hero />
      <CategoryHighlights />
      <ScienceSection />
    </>
  );
}
