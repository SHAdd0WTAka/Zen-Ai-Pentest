import { useEffect, useState } from 'react';
import { Navbar } from './sections/Navbar';
import { Hero } from './sections/Hero';
import { Stats } from './sections/Stats';
import { Features } from './sections/Features';
import { Tools } from './sections/Tools';
import { Architecture } from './sections/Architecture';
import { APIDocs } from './sections/APIDocs';
import { GettingStarted } from './sections/GettingStarted';
import { Footer } from './sections/Footer';
import { ParticleBackground } from './components/ParticleBackground';

function App() {
  const [scrollY, setScrollY] = useState(0);

  useEffect(() => {
    const handleScroll = () => {
      setScrollY(window.scrollY);
    };
    window.addEventListener('scroll', handleScroll, { passive: true });
    return () => window.removeEventListener('scroll', handleScroll);
  }, []);

  return (
    <div className="min-h-screen bg-slate-950 text-white overflow-x-hidden">
      <ParticleBackground />
      <Navbar scrollY={scrollY} />
      <main>
        <Hero />
        <Stats />
        <Features />
        <Tools />
        <Architecture />
        <APIDocs />
        <GettingStarted />
      </main>
      <Footer />
    </div>
  );
}

export default App;
