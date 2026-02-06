import { useState, useMemo } from 'react';
import { ArrowLeftRight, ChevronDown, ChevronUp, AlertTriangle, Check, X } from 'lucide-react';
import Modal from './Modal.jsx';
import Button from './Button.jsx';
import clsx from 'clsx';

function DiffView({ isOpen, onClose, values, documents, fields }) {
  const [expandedFields, setExpandedFields] = useState({});
  const [showOnlyDifferences, setShowOnlyDifferences] = useState(false);

  const valuesByField = useMemo(() => {
    const grouped = {};
    
    fields?.forEach(field => {
      grouped[field.id] = {
        field,
        values: documents?.map(doc => {
          const val = values?.find(
            v => v.document_id === doc.id && v.template_field_id === field.id
          );
          return {
            document: doc,
            value: val?.normalized_value || val?.raw_value || null,
            confidence: val?.confidence || 0,
            status: val?.status || 'missing'
          };
        }) || []
      };
    });
    
    return grouped;
  }, [values, documents, fields]);

  const fieldsWithDiffs = useMemo(() => {
    return Object.entries(valuesByField).map(([fieldId, data]) => {
      const uniqueValues = [...new Set(data.values.map(v => v.value).filter(Boolean))];
      const hasDifference = uniqueValues.length > 1;
      const allSame = uniqueValues.length === 1;
      const allMissing = uniqueValues.length === 0;
      
      return {
        fieldId,
        ...data,
        hasDifference,
        allSame,
        allMissing,
        uniqueCount: uniqueValues.length
      };
    });
  }, [valuesByField]);

  const displayFields = showOnlyDifferences 
    ? fieldsWithDiffs.filter(f => f.hasDifference)
    : fieldsWithDiffs;

  const stats = useMemo(() => {
    const total = fieldsWithDiffs.length;
    const withDiffs = fieldsWithDiffs.filter(f => f.hasDifference).length;
    const allSame = fieldsWithDiffs.filter(f => f.allSame).length;
    const allMissing = fieldsWithDiffs.filter(f => f.allMissing).length;
    
    return { total, withDiffs, allSame, allMissing };
  }, [fieldsWithDiffs]);

  const toggleField = (fieldId) => {
    setExpandedFields(prev => ({
      ...prev,
      [fieldId]: !prev[fieldId]
    }));
  };

  const computeDiff = (val1, val2) => {
    if (!val1 || !val2) return null;
    
    const words1 = val1.toLowerCase().split(/\s+/);
    const words2 = val2.toLowerCase().split(/\s+/);
    
    const common = words1.filter(w => words2.includes(w));
    const onlyIn1 = words1.filter(w => !words2.includes(w));
    const onlyIn2 = words2.filter(w => !words1.includes(w));
    
    return { common, onlyIn1, onlyIn2 };
  };

  return (
    <Modal isOpen={isOpen} onClose={onClose} title="Document Comparison" size="2xl">
      <div className="flex flex-col h-[80vh]">
        <div className="flex items-center justify-between mb-4 p-4 bg-slate-800 rounded-xl">
          <div className="flex items-center gap-6">
            <div className="text-center">
              <div className="text-2xl font-bold text-white">{stats.total}</div>
              <div className="text-xs text-slate-400">Total Fields</div>
            </div>
            <div className="text-center">
              <div className="text-2xl font-bold text-amber-400">{stats.withDiffs}</div>
              <div className="text-xs text-slate-400">With Differences</div>
            </div>
            <div className="text-center">
              <div className="text-2xl font-bold text-green-400">{stats.allSame}</div>
              <div className="text-xs text-slate-400">Identical</div>
            </div>
            <div className="text-center">
              <div className="text-2xl font-bold text-slate-500">{stats.allMissing}</div>
              <div className="text-xs text-slate-400">Missing</div>
            </div>
          </div>
          
          <label className="flex items-center gap-2 cursor-pointer">
            <input
              type="checkbox"
              checked={showOnlyDifferences}
              onChange={(e) => setShowOnlyDifferences(e.target.checked)}
              className="w-4 h-4 rounded border-slate-600 bg-slate-700 text-primary-500 focus:ring-primary-500"
            />
            <span className="text-sm text-slate-300">Show only differences</span>
          </label>
        </div>

        <div className="grid grid-cols-[200px_1fr] gap-4 mb-2 px-2">
          <div className="text-sm font-medium text-slate-400">Field</div>
          <div className="grid gap-2" style={{ gridTemplateColumns: `repeat(${documents?.length || 1}, 1fr)` }}>
            {documents?.map(doc => (
              <div key={doc.id} className="text-sm font-medium text-slate-300 truncate">
                {doc.original_filename}
              </div>
            ))}
          </div>
        </div>

        <div className="flex-1 overflow-y-auto space-y-2 pr-2">
          {displayFields.length === 0 ? (
            <div className="text-center py-8 text-slate-400">
              {showOnlyDifferences ? 'No differences found!' : 'No fields to compare.'}
            </div>
          ) : (
            displayFields.map(({ fieldId, field, values: fieldValues, hasDifference, allSame, allMissing }) => (
              <div
                key={fieldId}
                className={clsx(
                  'border rounded-xl overflow-hidden transition-colors',
                  hasDifference ? 'border-amber-500/50 bg-amber-500/5' :
                  allSame ? 'border-green-500/30 bg-green-500/5' :
                  'border-slate-700 bg-slate-800/50'
                )}
              >
                <button
                  onClick={() => toggleField(fieldId)}
                  className="w-full flex items-center justify-between p-3 hover:bg-slate-700/30 transition-colors"
                >
                  <div className="flex items-center gap-3">
                    {hasDifference ? (
                      <AlertTriangle className="w-4 h-4 text-amber-400" />
                    ) : allSame ? (
                      <Check className="w-4 h-4 text-green-400" />
                    ) : (
                      <X className="w-4 h-4 text-slate-500" />
                    )}
                    <span className="font-medium text-white">{field.field_label}</span>
                    <span className="text-xs text-slate-500">({field.field_type})</span>
                  </div>
                  <div className="flex items-center gap-2">
                    {hasDifference && (
                      <span className="text-xs px-2 py-0.5 bg-amber-500/20 text-amber-400 rounded">
                        {fieldValues.filter(v => v.value).length} variants
                      </span>
                    )}
                    {expandedFields[fieldId] ? (
                      <ChevronUp className="w-4 h-4 text-slate-400" />
                    ) : (
                      <ChevronDown className="w-4 h-4 text-slate-400" />
                    )}
                  </div>
                </button>

                <div className="grid grid-cols-[200px_1fr] gap-4 px-3 pb-3">
                  <div />
                  <div className="grid gap-2" style={{ gridTemplateColumns: `repeat(${documents?.length || 1}, 1fr)` }}>
                    {fieldValues.map((item, idx) => (
                      <div
                        key={idx}
                        className={clsx(
                          'p-2 rounded-lg text-sm',
                          item.value ? 'bg-slate-700/50' : 'bg-slate-800/30',
                          hasDifference && item.value && 'border border-amber-500/30'
                        )}
                      >
                        {item.value ? (
                          <>
                            <div className="text-white line-clamp-2">{item.value}</div>
                            <div className="flex items-center gap-2 mt-1">
                              <span className={clsx(
                                'text-xs px-1.5 py-0.5 rounded',
                                item.confidence >= 0.8 ? 'bg-green-500/20 text-green-400' :
                                item.confidence >= 0.5 ? 'bg-yellow-500/20 text-yellow-400' :
                                'bg-red-500/20 text-red-400'
                              )}>
                                {Math.round(item.confidence * 100)}%
                              </span>
                            </div>
                          </>
                        ) : (
                          <span className="text-slate-500 italic">Not found</span>
                        )}
                      </div>
                    ))}
                  </div>
                </div>

                {expandedFields[fieldId] && hasDifference && (
                  <div className="border-t border-slate-700 p-3 bg-slate-800/30">
                    <h4 className="text-xs font-medium text-slate-400 mb-2">DIFFERENCE ANALYSIS</h4>
                    <div className="space-y-2">
                      {fieldValues.filter(v => v.value).map((item, idx) => (
                        <div key={idx} className="flex items-start gap-2 text-sm">
                          <span className="text-slate-500 min-w-[80px] truncate">
                            {item.document.original_filename}:
                          </span>
                          <span className="text-white flex-1">{item.value}</span>
                        </div>
                      ))}
                    </div>
                    
                    {fieldValues.filter(v => v.value).length === 2 && (
                      <div className="mt-3 p-2 bg-slate-900/50 rounded-lg">
                        <h5 className="text-xs text-slate-500 mb-1">Word Differences:</h5>
                        {(() => {
                          const vals = fieldValues.filter(v => v.value);
                          const diff = computeDiff(vals[0]?.value, vals[1]?.value);
                          if (!diff) return null;
                          
                          return (
                            <div className="flex flex-wrap gap-1 text-xs">
                              {diff.onlyIn1.map((w, i) => (
                                <span key={`1-${i}`} className="px-1.5 py-0.5 bg-red-500/20 text-red-400 rounded">
                                  -{w}
                                </span>
                              ))}
                              {diff.onlyIn2.map((w, i) => (
                                <span key={`2-${i}`} className="px-1.5 py-0.5 bg-green-500/20 text-green-400 rounded">
                                  +{w}
                                </span>
                              ))}
                            </div>
                          );
                        })()}
                      </div>
                    )}
                  </div>
                )}
              </div>
            ))
          )}
        </div>

        <div className="flex justify-end gap-3 mt-4 pt-4 border-t border-slate-700">
          <Button variant="secondary" onClick={onClose}>
            Close
          </Button>
        </div>
      </div>
    </Modal>
  );
}

export default DiffView;

