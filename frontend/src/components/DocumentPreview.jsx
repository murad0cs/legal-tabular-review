import { useState, useEffect, useMemo } from 'react';
import { X, FileText, Search, ZoomIn, ZoomOut, ChevronUp, ChevronDown } from 'lucide-react';
import { documentsApi } from '../api/index.js';
import Skeleton from './Skeleton.jsx';

function DocumentPreview({ document, citationText, onClose }) {
  const [content, setContent] = useState('');
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [searchTerm, setSearchTerm] = useState('');
  const [fontSize, setFontSize] = useState(14);
  const [highlightIndex, setHighlightIndex] = useState(0);

  useEffect(() => {
    const fetchContent = async () => {
      if (!document?.id) return;
      
      try {
        setLoading(true);
        setError(null);
        const response = await documentsApi.getContent(document.id);
        setContent(response.data.content || '');
      } catch (err) {
        setError(err.message);
      } finally {
        setLoading(false);
      }
    };

    fetchContent();
  }, [document?.id]);

  // Find all occurrences of citation text
  const highlights = useMemo(() => {
    if (!citationText || !content) return [];
    
    const positions = [];
    const searchLower = citationText.toLowerCase();
    const contentLower = content.toLowerCase();
    let startIndex = 0;
    
    while (true) {
      const index = contentLower.indexOf(searchLower, startIndex);
      if (index === -1) break;
      positions.push({ start: index, end: index + citationText.length });
      startIndex = index + 1;
    }
    
    return positions;
  }, [citationText, content]);

  // Highlighted content rendering
  const renderContent = useMemo(() => {
    if (!content) return null;
    
    let parts = [];
    let lastIndex = 0;
    const termToHighlight = searchTerm || citationText;
    
    if (termToHighlight) {
      const termLower = termToHighlight.toLowerCase();
      const contentLower = content.toLowerCase();
      let searchIndex = 0;
      let partIndex = 0;
      
      while (true) {
        const index = contentLower.indexOf(termLower, searchIndex);
        if (index === -1) break;
        
        // Add text before match
        if (index > lastIndex) {
          parts.push(
            <span key={`text-${partIndex}`}>{content.slice(lastIndex, index)}</span>
          );
        }
        
        // Add highlighted match
        const isCitation = !searchTerm && citationText;
        parts.push(
          <mark
            key={`highlight-${partIndex}`}
            className={`px-0.5 rounded ${
              isCitation 
                ? 'bg-amber-500/40 text-amber-100 border-b-2 border-amber-500' 
                : 'bg-blue-500/40 text-blue-100'
            }`}
          >
            {content.slice(index, index + termToHighlight.length)}
          </mark>
        );
        
        lastIndex = index + termToHighlight.length;
        searchIndex = index + 1;
        partIndex++;
      }
    }
    
    // Add remaining text
    if (lastIndex < content.length) {
      parts.push(<span key="remaining">{content.slice(lastIndex)}</span>);
    }
    
    return parts.length > 0 ? parts : content;
  }, [content, searchTerm, citationText]);

  const scrollToHighlight = (direction) => {
    const marks = document.querySelectorAll('mark');
    if (marks.length === 0) return;
    
    let newIndex = highlightIndex;
    if (direction === 'next') {
      newIndex = (highlightIndex + 1) % marks.length;
    } else {
      newIndex = highlightIndex === 0 ? marks.length - 1 : highlightIndex - 1;
    }
    
    setHighlightIndex(newIndex);
    marks[newIndex]?.scrollIntoView({ behavior: 'smooth', block: 'center' });
  };

  if (!document) return null;

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/60 backdrop-blur-sm p-4">
      <div className="bg-slate-800 dark:bg-slate-800 light:bg-white rounded-xl shadow-2xl w-full max-w-4xl h-[85vh] flex flex-col border border-slate-700 dark:border-slate-700 light:border-slate-200">
        {/* Header */}
        <div className="flex items-center justify-between p-4 border-b border-slate-700 dark:border-slate-700 light:border-slate-200">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 bg-indigo-600/20 rounded-lg flex items-center justify-center">
              <FileText className="w-5 h-5 text-indigo-400" />
            </div>
            <div>
              <h2 className="text-lg font-semibold text-white dark:text-white light:text-slate-900">
                {document.filename}
              </h2>
              <p className="text-sm text-slate-400 dark:text-slate-400 light:text-slate-500">
                {document.page_count || 0} pages • {document.file_type?.toUpperCase()}
              </p>
            </div>
          </div>
          <button
            onClick={onClose}
            className="p-2 text-slate-400 hover:text-white hover:bg-slate-700 rounded-lg transition-colors"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        {/* Toolbar */}
        <div className="flex items-center gap-4 px-4 py-3 border-b border-slate-700 dark:border-slate-700 light:border-slate-200">
          <div className="flex-1 relative">
            <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-slate-400" />
            <input
              type="text"
              placeholder="Search in document..."
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              className="w-full pl-10 pr-4 py-2 bg-slate-700/50 dark:bg-slate-700/50 light:bg-slate-100 border border-slate-600 dark:border-slate-600 light:border-slate-300 rounded-lg text-white dark:text-white light:text-slate-900 placeholder-slate-400 text-sm focus:outline-none focus:ring-2 focus:ring-indigo-500"
            />
          </div>
          
          {(searchTerm || citationText) && (
            <div className="flex items-center gap-2">
              <button
                onClick={() => scrollToHighlight('prev')}
                className="p-2 text-slate-400 hover:text-white hover:bg-slate-700 rounded-lg transition-colors"
                title="Previous match"
              >
                <ChevronUp className="w-4 h-4" />
              </button>
              <button
                onClick={() => scrollToHighlight('next')}
                className="p-2 text-slate-400 hover:text-white hover:bg-slate-700 rounded-lg transition-colors"
                title="Next match"
              >
                <ChevronDown className="w-4 h-4" />
              </button>
            </div>
          )}
          
          <div className="flex items-center gap-2 border-l border-slate-600 pl-4">
            <button
              onClick={() => setFontSize(Math.max(10, fontSize - 2))}
              className="p-2 text-slate-400 hover:text-white hover:bg-slate-700 rounded-lg transition-colors"
              title="Decrease font size"
            >
              <ZoomOut className="w-4 h-4" />
            </button>
            <span className="text-sm text-slate-400 w-8 text-center">{fontSize}</span>
            <button
              onClick={() => setFontSize(Math.min(24, fontSize + 2))}
              className="p-2 text-slate-400 hover:text-white hover:bg-slate-700 rounded-lg transition-colors"
              title="Increase font size"
            >
              <ZoomIn className="w-4 h-4" />
            </button>
          </div>
        </div>

        {/* Citation highlight notice */}
        {citationText && (
          <div className="px-4 py-2 bg-amber-500/10 border-b border-amber-500/20">
            <p className="text-sm text-amber-400">
              <span className="font-medium">Citation highlighted:</span> "{citationText.slice(0, 100)}{citationText.length > 100 ? '...' : ''}"
            </p>
          </div>
        )}

        {/* Content */}
        <div className="flex-1 overflow-auto p-6">
          {loading ? (
            <div className="space-y-3">
              <Skeleton className="h-4 w-full" />
              <Skeleton className="h-4 w-full" />
              <Skeleton className="h-4 w-3/4" />
              <Skeleton className="h-4 w-full" />
              <Skeleton className="h-4 w-5/6" />
            </div>
          ) : error ? (
            <div className="text-center py-12">
              <p className="text-red-400">{error}</p>
            </div>
          ) : (
            <pre
              className="whitespace-pre-wrap font-mono text-slate-300 dark:text-slate-300 light:text-slate-700 leading-relaxed"
              style={{ fontSize: `${fontSize}px` }}
            >
              {renderContent}
            </pre>
          )}
        </div>
      </div>
    </div>
  );
}

export default DocumentPreview;

