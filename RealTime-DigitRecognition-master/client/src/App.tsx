import React from 'react';
import Scanner from './components/Scanner';
import { Fingerprint } from 'lucide-react';

function App() {
  return (
    <div className="min-h-screen">
      {/* Header */}
      <header className="glass sticky top-0 z-50 px-8 py-4 border-b border-white/10 flex justify-between items-center rounded-none border-t-0 border-x-0">
        <div className="flex items-center gap-3">
          <div className="p-2 bg-primary/20 rounded-lg">
            <Fingerprint className="text-primary w-6 h-6" />
          </div>
          <h1 className="text-2xl font-bold tracking-tight font-outfit">
            AI <span className="text-primary">MARK</span> SCANNER
          </h1>
        </div>
        <div className="hidden md:flex gap-6 text-sm font-medium text-text-dim">
          <span className="hover:text-primary cursor-pointer transition-colors">Scanner</span>
          <span className="hover:text-primary cursor-pointer transition-colors">Analytics</span>
          <span className="hover:text-primary cursor-pointer transition-colors">History</span>
        </div>
      </header>

      {/* Main Content */}
      <main className="container mx-auto py-12 px-4">
        <div className="text-center mb-12">
          <h2 className="text-4xl font-bold mb-4 font-outfit">Webcam <span className="text-secondary">Digit Recognition</span></h2>
          <p className="text-text-dim max-w-xl mx-auto">
            Place your marksheet within the scanning zone. Our CNN model will automatically identify and total your scores in real-time.
          </p>
        </div>

        <Scanner />
      </main>

      {/* Footer */}
      <footer className="mt-20 py-8 border-t border-white/5 text-center text-text-dim text-sm">
        <p>© 2026 AI Mark Scanner System • Powered by CNN</p>
      </footer>
    </div>
  );
}

export default App;
