import { Nav } from "./components/nav";
import { Footer } from "./components/footer";
import { ThemeProvider } from "./components/theme";
import { Hero } from "./sections/hero";
import { TrustedBy } from "./sections/trusted-by";
import { Overview } from "./sections/overview";
import { Features } from "./sections/features";
import { Architecture } from "./sections/architecture";
import { CodeSample } from "./sections/code-sample";
import { Performance } from "./sections/performance";
import { UseCases } from "./sections/use-cases";
import { Adoption } from "./sections/adoption";
import { Faq } from "./sections/faq";
import { GetStarted } from "./sections/get-started";

export default function App() {
  return (
    <ThemeProvider>
      <div className="relative min-h-screen">
        <Nav />
        <main>
          <Hero />
          <TrustedBy />
          <Overview />
          <Features />
          <Architecture />
          <CodeSample />
          <Performance />
          <UseCases />
          <Adoption />
          <Faq />
          <GetStarted />
        </main>
        <Footer />
      </div>
    </ThemeProvider>
  );
}
