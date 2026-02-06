import { useState, useEffect, useCallback, useRef } from 'react';
import { Search, X, Filter, FileText, Folder, Tag, ChevronDown } from 'lucide-react';
import { searchApi } from '../api/index.js';
import ConfidenceBadge from './ConfidenceBadge.jsx';
import StatusBadge from './StatusBadge.jsx';
import Modal from './Modal.jsx';
import Button from './Button.jsx';
import { useNavigate } from 'react-router-dom';
import toast from 'react-hot-toast';
import clsx from 'clsx';

function GlobalSearch({ isOpen, onClose }) {
  const navigate = useNavigate();
  const [query, setQuery] = useState('');
  const [results, setResults] = useState([]);
  const [loading, setLoading] = useState(false);
  const [showFilters, setShowFilters] = useState(false);
  const [fieldTypes, setFieldTypes] = useState([]);
  const [filters, setFilters] = useState({
    field_type: '',
    status: '',
    min_confidence: '',
    max_confidence: '',
  });
  const [pagination, setPagination] = useState({ total: 0, has_more: false });
  const searchInputRef = useRef(null);
  const debounceTimer = useRef(null);

  // Focus input when modal opens
  useEffect(() => {
    if (isOpen && searchInputRef.current) {
      setTimeout(() => searchInputRef.current?.focus(), 100);
    }
  }, [isOpen]);

  // Fetch field types for filter dropdown
  useEffect(() => {
    if (isOpen && fieldTypes.length === 0) {
      searchApi.getFieldTypes()
        .then(res => setFieldTypes(res.data.field_types || []))
        .catch(() => {});
    }
  }, [isOpen, fieldTypes.length]);

  // Debounced search
  const performSearch = useCallback(async () => {
    if (!query.trim()) {
      setResults([]);
      setPagination({ total: 0, has_more: false });
      return;
    }

    setLoading(true);
    try {
      const options = {};
      if (filters.field_type) options.field_type = filters.field_type;
      if (filters.status) options.status = filters.status;
      if (filters.min_confidence) options.min_confidence = parseFloat(filters.min_confidence);
      if (filters.max_confidence) options.max_confidence = parseFloat(filters.max_confidence);

      const res = await searchApi.search(query, options);
      setResults(res.data.results || []);
      setPagination({
        total: res.data.total || 0,
        has_more: res.data.has_more || false
      });
    } catch (err) {
      toast.error(`Search failed: ${err.message}`);
    } finally {
      setLoading(false);
    }
  }, [query, filters]);

  // Debounce search input
  useEffect(() => {
    if (debounceTimer.current) {
      clearTimeout(debounceTimer.current);
    }
    debounceTimer.current = setTimeout(() => {
      performSearch();
    }, 300);

    return () => {
      if (debounceTimer.current) {
        clearTimeout(debounceTimer.current);
      }
    };
  }, [query, performSearch]);

  const handleResultClick = (result) => {
    onClose();
    // Navigate to the project's review table
    if (result.project?.id) {
      navigate(`/projects/${result.project.id}/review`);
    }
  };

  const clearFilters = () => {
    setFilters({
      field_type: '',
      status: '',
      min_confidence: '',
      max_confidence: '',
    });
  };

  const hasActiveFilters = Object.values(filters).some(v => v !== '');

  return (
    <Modal isOpen={isOpen} onClose={onClose} title="Global Search" size="xl">
      <div className="flex flex-col h-[70vh]">
        {/* Search Input */}
        <div className="relative mb-4">
          <Search className="absolute left-4 top-1/2 -translate-y-1/2 w-5 h-5 text-slate-400" />
          <input
            ref={searchInputRef}
            type="text"
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            placeholder="Search extracted values, documents, fields..."
            className="w-full pl-12 pr-12 py-3 bg-slate-800 border border-slate-700 rounded-xl text-white placeholder-slate-500 focus:outline-none focus:ring-2 focus:ring-primary-500/50 text-lg"
          />
          {query && (
            <button
              onClick={() => setQuery('')}
              className="absolute right-4 top-1/2 -translate-y-1/2 text-slate-400 hover:text-white"
            >
              <X className="w-5 h-5" />
            </button>
          )}
        </div>

        {/* Filters Toggle */}
        <div className="flex items-center justify-between mb-4">
          <button
            onClick={() => setShowFilters(!showFilters)}
            className={clsx(
              "flex items-center gap-2 px-3 py-2 rounded-lg transition-colors",
              showFilters || hasActiveFilters
                ? "bg-primary-500/20 text-primary-400"
                : "bg-slate-800 text-slate-400 hover:text-white"
            )}
          >
            <Filter className="w-4 h-4" />
            Filters
            {hasActiveFilters && (
              <span className="px-2 py-0.5 bg-primary-500 text-white text-xs rounded-full">
                Active
              </span>
            )}
            <ChevronDown className={clsx("w-4 h-4 transition-transform", showFilters && "rotate-180")} />
          </button>

          {pagination.total > 0 && (
            <span className="text-sm text-slate-400">
              {pagination.total} result{pagination.total !== 1 ? 's' : ''} found
            </span>
          )}
        </div>

        {/* Filter Panel */}
        {showFilters && (
          <div className="grid grid-cols-4 gap-4 mb-4 p-4 bg-slate-800/50 rounded-xl">
            <div>
              <label className="block text-sm text-slate-400 mb-1">Field Type</label>
              <select
                value={filters.field_type}
                onChange={(e) => setFilters(f => ({ ...f, field_type: e.target.value }))}
                className="w-full px-3 py-2 bg-slate-800 border border-slate-700 rounded-lg text-white text-sm focus:outline-none focus:ring-2 focus:ring-primary-500/50"
              >
                <option value="">All Types</option>
                {fieldTypes.map(type => (
                  <option key={type} value={type}>{type}</option>
                ))}
              </select>
            </div>

            <div>
              <label className="block text-sm text-slate-400 mb-1">Status</label>
              <select
                value={filters.status}
                onChange={(e) => setFilters(f => ({ ...f, status: e.target.value }))}
                className="w-full px-3 py-2 bg-slate-800 border border-slate-700 rounded-lg text-white text-sm focus:outline-none focus:ring-2 focus:ring-primary-500/50"
              >
                <option value="">All Statuses</option>
                <option value="pending">Pending</option>
                <option value="approved">Approved</option>
                <option value="rejected">Rejected</option>
                <option value="edited">Edited</option>
              </select>
            </div>

            <div>
              <label className="block text-sm text-slate-400 mb-1">Min Confidence</label>
              <input
                type="number"
                min="0"
                max="1"
                step="0.1"
                value={filters.min_confidence}
                onChange={(e) => setFilters(f => ({ ...f, min_confidence: e.target.value }))}
                placeholder="0.0"
                className="w-full px-3 py-2 bg-slate-800 border border-slate-700 rounded-lg text-white text-sm focus:outline-none focus:ring-2 focus:ring-primary-500/50"
              />
            </div>

            <div>
              <label className="block text-sm text-slate-400 mb-1">Max Confidence</label>
              <input
                type="number"
                min="0"
                max="1"
                step="0.1"
                value={filters.max_confidence}
                onChange={(e) => setFilters(f => ({ ...f, max_confidence: e.target.value }))}
                placeholder="1.0"
                className="w-full px-3 py-2 bg-slate-800 border border-slate-700 rounded-lg text-white text-sm focus:outline-none focus:ring-2 focus:ring-primary-500/50"
              />
            </div>

            {hasActiveFilters && (
              <div className="col-span-4 flex justify-end">
                <Button variant="ghost" size="sm" onClick={clearFilters}>
                  Clear Filters
                </Button>
              </div>
            )}
          </div>
        )}

        {/* Results */}
        <div className="flex-1 overflow-y-auto">
          {loading ? (
            <div className="flex items-center justify-center h-32">
              <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary-500"></div>
            </div>
          ) : results.length === 0 ? (
            <div className="text-center py-12 text-slate-400">
              {query ? 'No results found' : 'Start typing to search...'}
            </div>
          ) : (
            <div className="space-y-2">
              {results.map((result) => (
                <button
                  key={result.id}
                  onClick={() => handleResultClick(result)}
                  className="w-full p-4 bg-slate-800/50 hover:bg-slate-800 rounded-xl text-left transition-colors group"
                >
                  <div className="flex items-start justify-between gap-4">
                    <div className="flex-1 min-w-0">
                      {/* Value */}
                      <div className="font-medium text-white truncate">
                        {result.normalized_value || result.raw_value || '(empty)'}
                      </div>
                      
                      {/* Field info */}
                      <div className="flex items-center gap-2 mt-1 text-sm text-slate-400">
                        <Tag className="w-3 h-3" />
                        <span>{result.field?.label || result.field?.name}</span>
                        <span className="text-slate-600">•</span>
                        <span className="text-slate-500">{result.field?.type}</span>
                      </div>

                      {/* Document & Project */}
                      <div className="flex items-center gap-4 mt-2 text-xs text-slate-500">
                        <span className="flex items-center gap-1">
                          <FileText className="w-3 h-3" />
                          {result.document?.filename}
                        </span>
                        {result.project?.name && (
                          <span className="flex items-center gap-1">
                            <Folder className="w-3 h-3" />
                            {result.project.name}
                          </span>
                        )}
                      </div>

                      {/* Citation */}
                      {result.citation_text && (
                        <div className="mt-2 text-xs text-slate-500 italic truncate">
                          "{result.citation_text}"
                        </div>
                      )}
                    </div>

                    {/* Badges */}
                    <div className="flex flex-col items-end gap-2">
                      <ConfidenceBadge value={result.confidence} />
                      <StatusBadge status={result.status} />
                    </div>
                  </div>
                </button>
              ))}
            </div>
          )}
        </div>

        {/* Load More */}
        {pagination.has_more && (
          <div className="pt-4 text-center">
            <span className="text-sm text-slate-400">
              Showing {results.length} of {pagination.total} results
            </span>
          </div>
        )}
      </div>
    </Modal>
  );
}

export default GlobalSearch;

