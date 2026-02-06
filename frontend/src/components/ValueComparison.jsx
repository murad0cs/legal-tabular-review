import { useState, useMemo } from 'react';
import { X, GitCompare, AlertTriangle, Check, Equal } from 'lucide-react';
import Card from './Card.jsx';

function ValueComparison({ fields, documents, matrix, onClose }) {
  const [selectedField, setSelectedField] = useState(null);

  // Find fields with different values across documents
  const comparisonData = useMemo(() => {
    return fields.map(field => {
      const values = documents.map(doc => {
        const value = matrix[`${field.id}-${doc.id}`];
        return {
          documentId: doc.id,
          documentName: doc.filename,
          value: value?.normalized_value || value?.raw_value,
          confidence: value?.confidence || 0,
          status: value?.status,
        };
      });

      // Check if all values are the same
      const uniqueValues = [...new Set(values.map(v => v.value).filter(Boolean))];
      const hasDifferences = uniqueValues.length > 1;
      const allEmpty = values.every(v => !v.value);

      return {
        field,
        values,
        uniqueValues,
        hasDifferences,
        allEmpty,
      };
    });
  }, [fields, documents, matrix]);

  const fieldsWithDifferences = comparisonData.filter(d => d.hasDifferences);
  const fieldsConsistent = comparisonData.filter(d => !d.hasDifferences && !d.allEmpty);
  const fieldsEmpty = comparisonData.filter(d => d.allEmpty);

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/60 backdrop-blur-sm p-4">
      <div className="bg-slate-800 dark:bg-slate-800 light:bg-white rounded-xl shadow-2xl w-full max-w-5xl h-[85vh] flex flex-col border border-slate-700 dark:border-slate-700 light:border-slate-200">
        {/* Header */}
        <div className="flex items-center justify-between p-4 border-b border-slate-700 dark:border-slate-700 light:border-slate-200">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 bg-purple-600/20 rounded-lg flex items-center justify-center">
              <GitCompare className="w-5 h-5 text-purple-400" />
            </div>
            <div>
              <h2 className="text-lg font-semibold text-white dark:text-white light:text-slate-900">
                Value Comparison
              </h2>
              <p className="text-sm text-slate-400">
                Compare extracted values across {documents.length} documents
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

        {/* Summary stats */}
        <div className="grid grid-cols-3 gap-4 p-4 border-b border-slate-700 dark:border-slate-700 light:border-slate-200">
          <div className="bg-red-500/10 border border-red-500/30 rounded-lg p-3">
            <div className="flex items-center gap-2 text-red-400">
              <AlertTriangle className="w-4 h-4" />
              <span className="text-sm font-medium">Differences Found</span>
            </div>
            <p className="text-2xl font-bold text-red-300 mt-1">{fieldsWithDifferences.length}</p>
          </div>
          <div className="bg-green-500/10 border border-green-500/30 rounded-lg p-3">
            <div className="flex items-center gap-2 text-green-400">
              <Check className="w-4 h-4" />
              <span className="text-sm font-medium">Consistent</span>
            </div>
            <p className="text-2xl font-bold text-green-300 mt-1">{fieldsConsistent.length}</p>
          </div>
          <div className="bg-slate-500/10 border border-slate-500/30 rounded-lg p-3">
            <div className="flex items-center gap-2 text-slate-400">
              <Equal className="w-4 h-4" />
              <span className="text-sm font-medium">No Data</span>
            </div>
            <p className="text-2xl font-bold text-slate-300 mt-1">{fieldsEmpty.length}</p>
          </div>
        </div>

        {/* Content */}
        <div className="flex-1 overflow-auto p-4">
          {fieldsWithDifferences.length > 0 && (
            <div className="mb-6">
              <h3 className="text-lg font-semibold text-red-400 mb-3 flex items-center gap-2">
                <AlertTriangle className="w-5 h-5" />
                Fields with Differences
              </h3>
              <div className="space-y-4">
                {fieldsWithDifferences.map(({ field, values, uniqueValues }) => (
                  <Card key={field.id} className="border-red-500/30">
                    <div className="mb-3">
                      <h4 className="font-medium text-white dark:text-white light:text-slate-900">
                        {field.field_label}
                      </h4>
                      <p className="text-xs text-slate-400">
                        {uniqueValues.length} different values found
                      </p>
                    </div>
                    <div className="grid gap-2">
                      {values.map((v, idx) => (
                        <div
                          key={idx}
                          className={`flex items-center justify-between p-3 rounded-lg ${
                            v.value
                              ? 'bg-slate-700/50 dark:bg-slate-700/50 light:bg-slate-100'
                              : 'bg-slate-700/20 dark:bg-slate-700/20 light:bg-slate-50'
                          }`}
                        >
                          <div className="flex-1">
                            <p className="text-xs text-slate-400 mb-1">{v.documentName}</p>
                            <p className={`text-sm ${
                              v.value
                                ? 'text-white dark:text-white light:text-slate-900'
                                : 'text-slate-500 italic'
                            }`}>
                              {v.value || '(empty)'}
                            </p>
                          </div>
                          {v.value && (
                            <div className="ml-3 text-right">
                              <span className={`px-2 py-0.5 text-xs rounded-full ${
                                v.confidence >= 0.8 ? 'bg-green-500/20 text-green-300' :
                                v.confidence >= 0.5 ? 'bg-amber-500/20 text-amber-300' :
                                'bg-red-500/20 text-red-300'
                              }`}>
                                {Math.round(v.confidence * 100)}%
                              </span>
                            </div>
                          )}
                        </div>
                      ))}
                    </div>
                  </Card>
                ))}
              </div>
            </div>
          )}

          {fieldsConsistent.length > 0 && (
            <div className="mb-6">
              <h3 className="text-lg font-semibold text-green-400 mb-3 flex items-center gap-2">
                <Check className="w-5 h-5" />
                Consistent Fields
              </h3>
              <div className="grid grid-cols-2 gap-3">
                {fieldsConsistent.map(({ field, values }) => {
                  const value = values.find(v => v.value);
                  return (
                    <div
                      key={field.id}
                      className="bg-slate-700/30 dark:bg-slate-700/30 light:bg-slate-100 rounded-lg p-3 border border-green-500/20"
                    >
                      <p className="text-xs text-slate-400 mb-1">{field.field_label}</p>
                      <p className="text-sm text-white dark:text-white light:text-slate-900 truncate">
                        {value?.value || '-'}
                      </p>
                    </div>
                  );
                })}
              </div>
            </div>
          )}

          {fieldsEmpty.length > 0 && (
            <div>
              <h3 className="text-lg font-semibold text-slate-400 mb-3 flex items-center gap-2">
                <Equal className="w-5 h-5" />
                Fields with No Data
              </h3>
              <div className="flex flex-wrap gap-2">
                {fieldsEmpty.map(({ field }) => (
                  <span
                    key={field.id}
                    className="px-3 py-1.5 bg-slate-700/30 dark:bg-slate-700/30 light:bg-slate-100 rounded-lg text-sm text-slate-400"
                  >
                    {field.field_label}
                  </span>
                ))}
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}

export default ValueComparison;


