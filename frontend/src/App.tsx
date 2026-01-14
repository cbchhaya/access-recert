/**
 * ARAS Frontend Application
 * Author: Chiradeep Chhaya
 */

import React from 'react';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { BrowserRouter, Routes, Route, Link, useLocation, useSearchParams } from 'react-router-dom';
import { Home, FileText, Settings, Shield, MessageSquare } from 'lucide-react';
import ReactMarkdown from 'react-markdown';
import Dashboard from './pages/Dashboard';
import CampaignList from './pages/CampaignList';
import CampaignDetail from './pages/CampaignDetail';
import ReviewItemDetail from './pages/ReviewItemDetail';

const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      refetchOnWindowFocus: false,
      retry: 1,
    },
  },
});

function App() {
  return (
    <QueryClientProvider client={queryClient}>
      <BrowserRouter>
        <div className="min-h-screen bg-gray-50">
          <Navigation />
          <main className="pl-64">
            <Routes>
              <Route path="/" element={<Dashboard />} />
              <Route path="/campaigns" element={<CampaignList />} />
              <Route path="/campaigns/:id" element={<CampaignDetail />} />
              <Route path="/review/:id" element={<ReviewItemDetail />} />
              <Route path="/settings/weights" element={<WeightsPage />} />
              <Route path="/chat" element={<ChatPage />} />
            </Routes>
          </main>
        </div>
      </BrowserRouter>
    </QueryClientProvider>
  );
}

function Navigation() {
  const location = useLocation();

  const links = [
    { path: '/', icon: Home, label: 'Dashboard' },
    { path: '/campaigns', icon: FileText, label: 'Campaigns' },
    { path: '/settings/weights', icon: Settings, label: 'Settings' },
    { path: '/chat', icon: MessageSquare, label: 'Chat Assistant' },
  ];

  return (
    <nav className="fixed left-0 top-0 bottom-0 w-64 bg-white border-r border-gray-200 p-4">
      {/* Logo */}
      <div className="flex items-center gap-3 px-4 py-4 mb-8">
        <Shield className="h-8 w-8 text-blue-600" />
        <div>
          <h1 className="font-bold text-gray-900">ARAS</h1>
          <p className="text-xs text-gray-500">Access Recertification</p>
        </div>
      </div>

      {/* Links */}
      <div className="space-y-1">
        {links.map(({ path, icon: Icon, label }) => {
          const isActive = location.pathname === path ||
            (path !== '/' && location.pathname.startsWith(path));

          return (
            <Link
              key={path}
              to={path}
              className={`flex items-center gap-3 px-4 py-3 rounded-lg transition-colors ${
                isActive
                  ? 'bg-blue-50 text-blue-700'
                  : 'text-gray-600 hover:bg-gray-50'
              }`}
            >
              <Icon className="h-5 w-5" />
              <span className="font-medium">{label}</span>
            </Link>
          );
        })}
      </div>

      {/* Footer */}
      <div className="absolute bottom-4 left-4 right-4 text-center text-xs text-gray-400">
        <p>ARAS v0.1.0</p>
        <p className="mt-1">Chiradeep Chhaya</p>
      </div>
    </nav>
  );
}

// Placeholder for Weights settings page
function WeightsPage() {
  return (
    <div className="p-6 max-w-3xl mx-auto">
      <h1 className="text-2xl font-bold text-gray-900 mb-6">Proximity Weights</h1>
      <div className="bg-white rounded-lg border border-gray-200 p-6">
        <p className="text-gray-500 mb-6">
          Configure the weights used to calculate peer proximity. Weights must sum to 1.0.
        </p>

        <div className="space-y-6">
          <WeightSlider label="Structural" description="Based on org hierarchy" defaultValue={0.25} />
          <WeightSlider label="Functional" description="Based on job role similarity" defaultValue={0.35} />
          <WeightSlider label="Behavioral" description="Based on activity patterns" defaultValue={0.30} />
          <WeightSlider label="Temporal" description="Based on tenure alignment" defaultValue={0.10} />
        </div>

        <div className="mt-6 flex justify-end">
          <button className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700">
            Save Changes
          </button>
        </div>
      </div>
    </div>
  );
}

function WeightSlider({
  label,
  description,
  defaultValue
}: {
  label: string;
  description: string;
  defaultValue: number;
}) {
  return (
    <div>
      <div className="flex items-center justify-between mb-2">
        <div>
          <label className="font-medium text-gray-900">{label}</label>
          <p className="text-sm text-gray-500">{description}</p>
        </div>
        <span className="text-lg font-semibold text-blue-600">
          {(defaultValue * 100).toFixed(0)}%
        </span>
      </div>
      <input
        type="range"
        min="0"
        max="100"
        defaultValue={defaultValue * 100}
        className="w-full h-2 bg-gray-200 rounded-lg appearance-none cursor-pointer"
      />
    </div>
  );
}

// Helper to linkify UUIDs in text (for review item IDs)
function LinkifyUUIDs({ text }: { text: string }) {
  // UUID pattern
  const uuidRegex = /([0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12})/gi;
  const parts = text.split(uuidRegex);

  return (
    <>
      {parts.map((part, i) => {
        if (uuidRegex.test(part)) {
          // Reset regex lastIndex after test
          uuidRegex.lastIndex = 0;
          return (
            <Link
              key={i}
              to={`/review/${part}`}
              className="text-blue-600 hover:text-blue-800 underline"
            >
              {part}
            </Link>
          );
        }
        return <span key={i}>{part}</span>;
      })}
    </>
  );
}

// Chat page with API integration
function ChatPage() {
  const [searchParams, setSearchParams] = useSearchParams();
  const [currentItemId, setCurrentItemId] = React.useState<string | null>(null);
  const [messages, setMessages] = React.useState<Array<{role: string; content: string}>>([
    {
      role: 'assistant',
      content: `Hello! I'm your ARAS assistant. I can help you with:

- Understanding access patterns
- Reviewing specific employees or resources
- Explaining assurance scores
- Finding items that need attention
- Providing campaign statistics

Try asking me things like:
- "Show me system stats"
- "Find employees named John"
- "What low assurance items need review in campaign X?"
- "Explain the score for review item Y"`
    }
  ]);
  const [input, setInput] = React.useState('');
  const [loading, setLoading] = React.useState(false);
  const messagesEndRef = React.useRef<HTMLDivElement>(null);
  const autoSentRef = React.useRef(false);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  React.useEffect(() => {
    scrollToBottom();
  }, [messages]);

  // Handle auto-explain from URL parameter
  React.useEffect(() => {
    const explainId = searchParams.get('explain');
    if (explainId && !autoSentRef.current && !loading) {
      // Set ref immediately (synchronous) to prevent duplicate calls
      autoSentRef.current = true;
      // Store the item ID for the "View Item" link
      setCurrentItemId(explainId);
      // Clear the URL param
      setSearchParams({}, { replace: true });
      // Auto-send the explain request
      const question = `Please explain the assurance score for review item ${explainId}. Include details about why it received this score, what factors contributed to it, and whether it requires human review.`;
      sendMessageDirect(question);
    }
  }, [searchParams, loading]);

  const sendMessageDirect = async (messageText: string) => {
    setMessages(prev => [...prev, { role: 'user', content: messageText }]);
    setLoading(true);

    try {
      const response = await fetch('http://localhost:8000/api/chat', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ message: messageText }),
      });

      if (!response.ok) {
        throw new Error('Chat service unavailable');
      }

      const data = await response.json();
      setMessages(prev => [...prev, { role: 'assistant', content: data.response }]);
    } catch (error) {
      setMessages(prev => [...prev, {
        role: 'assistant',
        content: 'Sorry, I encountered an error. Make sure the ANTHROPIC_API_KEY environment variable is set on the server.'
      }]);
    } finally {
      setLoading(false);
    }
  };

  const sendMessage = async () => {
    if (!input.trim() || loading) return;
    const userMessage = input.trim();
    setInput('');
    await sendMessageDirect(userMessage);
  };

  return (
    <div className="p-6 max-w-4xl mx-auto">
      <div className="flex items-center justify-between mb-6">
        <h1 className="text-2xl font-bold text-gray-900">Chat Assistant</h1>
        {currentItemId && (
          <Link
            to={`/review/${currentItemId}`}
            className="inline-flex items-center gap-2 px-4 py-2 bg-blue-50 text-blue-700 rounded-lg hover:bg-blue-100 transition-colors"
          >
            <Shield className="h-4 w-4" />
            View Review Item
          </Link>
        )}
      </div>
      <div className="bg-white rounded-lg border border-gray-200 h-[calc(100vh-200px)] flex flex-col">
        <div className="flex-1 p-4 overflow-y-auto">
          <div className="space-y-4">
            {messages.map((msg, i) => (
              <div
                key={i}
                className={`rounded-lg p-4 max-w-[80%] ${
                  msg.role === 'user'
                    ? 'bg-blue-100 ml-auto whitespace-pre-wrap'
                    : 'bg-gray-100 prose prose-sm max-w-none'
                }`}
              >
                {msg.role === 'user' ? (
                  <LinkifyUUIDs text={msg.content} />
                ) : (
                  <ReactMarkdown>{msg.content}</ReactMarkdown>
                )}
              </div>
            ))}
            {loading && (
              <div className="bg-gray-100 rounded-lg p-4 max-w-[80%] animate-pulse">
                Thinking...
              </div>
            )}
            <div ref={messagesEndRef} />
          </div>
        </div>
        <div className="p-4 border-t border-gray-200">
          <div className="flex gap-2">
            <input
              type="text"
              value={input}
              onChange={(e) => setInput(e.target.value)}
              onKeyDown={(e) => e.key === 'Enter' && sendMessage()}
              placeholder="Ask me anything about access certifications..."
              className="flex-1 px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500"
              disabled={loading}
            />
            <button
              onClick={sendMessage}
              disabled={loading || !input.trim()}
              className="px-6 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-50"
            >
              {loading ? '...' : 'Send'}
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}

export default App;
