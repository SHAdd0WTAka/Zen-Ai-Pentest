// ============================================
// Twitch Tunnel Page
// ============================================

import { TwitchTunnelPanel } from '@/components/custom/TwitchTunnelPanel';

export function TwitchTunnelPage() {
  return (
    <div className="container mx-auto py-8">
      <div className="mb-8">
        <h1 className="text-3xl font-bold mb-2">Twitch Chat Tunnel</h1>
        <p className="text-muted-foreground">
          Connect your frontend and backend through Twitch chat messages.
          Perfect for bypassing firewalls and having fun! 🎮
        </p>
      </div>

      <TwitchTunnelPanel />

      <div className="mt-8 grid grid-cols-1 md:grid-cols-2 gap-6">
        <div className="bg-muted p-6 rounded-lg">
          <h3 className="font-semibold mb-2">How it works</h3>
          <ol className="list-decimal list-inside space-y-2 text-sm text-muted-foreground">
            <li>Backend encodes API responses to Base64</li>
            <li>Chunks are sent as Twitch chat messages</li>
            <li>Frontend reassembles messages from chat</li>
            <li>Both sides think they're directly connected!</li>
          </ol>
        </div>

        <div className="bg-muted p-6 rounded-lg">
          <h3 className="font-semibold mb-2">Architecture</h3>
          <div className="font-mono text-xs space-y-1">
            <div className="flex items-center gap-2">
              <span className="bg-blue-500/20 px-2 py-1 rounded">Frontend</span>
              <span>←→</span>
              <span className="bg-purple-500/20 px-2 py-1 rounded">Twitch IRC</span>
              <span>←→</span>
              <span className="bg-green-500/20 px-2 py-1 rounded">Backend</span>
            </div>
          </div>
          <p className="text-xs text-muted-foreground mt-2">
            You are the MITM node in the middle!
          </p>
        </div>
      </div>
    </div>
  );
}
