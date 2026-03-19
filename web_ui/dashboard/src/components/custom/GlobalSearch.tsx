// ============================================
// Zen-AI-Pentest Platform - Global Search
// ============================================

import { useState, useEffect, useCallback } from 'react';
import { useNavigate } from 'react-router-dom';
import { Search, FileText, Scan, ShieldAlert, Bot, Loader2 } from 'lucide-react';
import {
  CommandDialog,
  CommandEmpty,
  CommandGroup,
  CommandInput,
  CommandItem,
  CommandList,
  CommandSeparator,
} from '@/components/ui/command';
import { searchApi } from '@/services/api';

interface GlobalSearchProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
}

interface SearchResult {
  type: string;
  item: {
    id: string;
    name?: string;
    title?: string;
    target?: string;
    severity?: string;
  };
}

export function GlobalSearch({ open, onOpenChange }: GlobalSearchProps) {
  const navigate = useNavigate();
  const [query, setQuery] = useState('');
  const [results, setResults] = useState<SearchResult[]>([]);
  const [loading, setLoading] = useState(false);
  const [suggestions, setSuggestions] = useState<string[]>([]);

  const performSearch = useCallback(async (searchQuery: string) => {
    if (!searchQuery.trim()) {
      setResults([]);
      return;
    }

    setLoading(true);
    try {
      const data = await searchApi.global(searchQuery, {}, { page: 1, limit: 10 });
      setResults(data.results);
    } catch (error) {
      console.error('Search error:', error);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    const timer = setTimeout(() => {
      performSearch(query);
    }, 300);

    return () => clearTimeout(timer);
  }, [query, performSearch]);

  useEffect(() => {
    const fetchSuggestions = async () => {
      if (query.length > 2) {
        try {
          const data = await searchApi.suggestions(query);
          setSuggestions(data);
        } catch (error) {
          console.error('Suggestions error:', error);
        }
      }
    };

    fetchSuggestions();
  }, [query]);

  const handleSelect = (result: SearchResult) => {
    onOpenChange(false);

    const routes: Record<string, string> = {
      scan: '/scans',
      vulnerability: '/vulnerabilities',
      report: '/reports',
      agent: '/agents',
      plugin: '/plugins',
    };

    const route = routes[result.type];
    if (route) {
      navigate(`${route}/${result.item.id}`);
    }
  };

  const getIcon = (type: string) => {
    switch (type) {
      case 'scan':
        return <Scan className="w-4 h-4" />;
      case 'vulnerability':
        return <ShieldAlert className="w-4 h-4" />;
      case 'report':
        return <FileText className="w-4 h-4" />;
      case 'agent':
        return <Bot className="w-4 h-4" />;
      default:
        return <Search className="w-4 h-4" />;
    }
  };

  const groupedResults = results.reduce((acc, result) => {
    if (!acc[result.type]) {
      acc[result.type] = [];
    }
    acc[result.type].push(result);
    return acc;
  }, {} as Record<string, SearchResult[]>);

  return (
    <CommandDialog open={open} onOpenChange={onOpenChange}>
      <CommandInput
        placeholder="Search scans, vulnerabilities, reports..."
        value={query}
        onValueChange={setQuery}
      />
      <CommandList>
        <CommandEmpty>
          {loading ? (
            <div className="flex items-center justify-center py-6">
              <Loader2 className="w-5 h-5 animate-spin mr-2" />
              Searching...
            </div>
          ) : (
            'No results found.'
          )}
        </CommandEmpty>

        {suggestions.length > 0 && query.length > 0 && (
          <CommandGroup heading="Suggestions">
            {suggestions.map((suggestion, index) => (
              <CommandItem
                key={`suggestion-${index}`}
                onSelect={() => setQuery(suggestion)}
              >
                <Search className="w-4 h-4 mr-2" />
                {suggestion}
              </CommandItem>
            ))}
          </CommandGroup>
        )}

        <CommandSeparator />

        {Object.entries(groupedResults).map(([type, items]) => (
          <CommandGroup key={type} heading={type.charAt(0).toUpperCase() + type.slice(1) + 's'}>
            {items.map((result) => (
              <CommandItem
                key={`${result.type}-${result.item.id}`}
                onSelect={() => handleSelect(result)}
              >
                {getIcon(result.type)}
                <span className="ml-2">
                  {result.item.name || result.item.title || result.item.target || result.item.id}
                </span>
                {result.item.severity && (
                  <span className={`ml-auto text-xs px-2 py-0.5 rounded-full ${
                    result.item.severity === 'critical' ? 'bg-red-500/20 text-red-500' :
                    result.item.severity === 'high' ? 'bg-orange-500/20 text-orange-500' :
                    result.item.severity === 'medium' ? 'bg-yellow-500/20 text-yellow-500' :
                    'bg-blue-500/20 text-blue-500'
                  }`}>
                    {result.item.severity}
                  </span>
                )}
              </CommandItem>
            ))}
          </CommandGroup>
        ))}

        <CommandSeparator />

        <CommandGroup heading="Quick Actions">
          <CommandItem onSelect={() => { onOpenChange(false); navigate('/scans/new'); }}>
            <Scan className="w-4 h-4 mr-2" />
            Start New Scan
          </CommandItem>
          <CommandItem onSelect={() => { onOpenChange(false); navigate('/reports'); }}>
            <FileText className="w-4 h-4 mr-2" />
            Generate Report
          </CommandItem>
          <CommandItem onSelect={() => { onOpenChange(false); navigate('/agents'); }}>
            <Bot className="w-4 h-4 mr-2" />
            Manage Agents
          </CommandItem>
        </CommandGroup>
      </CommandList>
    </CommandDialog>
  );
}
