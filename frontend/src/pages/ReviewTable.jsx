import { useState, useEffect, useMemo, useCallback, useRef } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import {
  ArrowLeft, Check, X, Pencil, Download, Info, Save, Filter,
  ChevronDown, ChevronUp, BarChart3, Keyboard, CheckSquare, Square,
  MessageSquare, History, GitCompare, Settings, Eye
} from 'lucide-react';
import toast from 'react-hot-toast';
import Button from '../components/Button.jsx';
import Card from '../components/Card.jsx';
import Modal from '../components/Modal.jsx';
import ConfidenceBadge from '../components/ConfidenceBadge.jsx';
import StatusBadge from '../components/StatusBadge.jsx';
import Analytics from '../components/Analytics.jsx';
import { SkeletonReviewTable } from '../components/Skeleton.jsx';
import DocumentPreview from '../components/DocumentPreview.jsx';
import CommentsPanel from '../components/CommentsPanel.jsx';
import AuditLog from '../components/AuditLog.jsx';
import ValueComparison from '../components/ValueComparison.jsx';
import ProjectSettings from '../components/ProjectSettings.jsx';
import { projectsApi } from '../api/index.js';
import { downloadBlob, truncate } from '../utils/format.js';

const FILTER_OPTIONS = {
  status: [
    { value: 'all', label: 'All Statuses' },
    { value: 'pending', label: 'Pending' },
    { value: 'approved', label: 'Approved' },
    { value: 'rejected', label: 'Rejected' },
    { value: 'edited', label: 'Edited' },
  ],
  confidence: [
    { value: 'all', label: 'All Confidence' },
    { value: 'high', label: 'High (≥80%)' },
    { value: 'medium', label: 'Medium (50-79%)' },
    { value: 'low', label: 'Low (<50%)' },
  ],
};

/**
 * Enhanced side-by-side comparison table for reviewing extracted values.
 * Features: bulk actions, filtering, sorting, keyboard shortcuts, analytics
 */
function ReviewTable() {
  const { id } = useParams();
  const navigate = useNavigate();
  const tableRef = useRef(null);

  // Data state
  const [project, setProject] = useState(null);
  const [values, setValues] = useState([]);
  const [loading, setLoading] = useState(true);

  // UI state
  const [editingValue, setEditingValue] = useState(null);
  const [editInput, setEditInput] = useState('');
  const [citationModal, setCitationModal] = useState(null);
  const [showAnalytics, setShowAnalytics] = useState(false);
  const [showShortcuts, setShowShortcuts] = useState(false);
  
  // New feature states
  const [documentPreview, setDocumentPreview] = useState(null); // { document, citationText }
  const [commentsValueId, setCommentsValueId] = useState(null);
  const [showAuditLog, setShowAuditLog] = useState(false);
  const [showComparison, setShowComparison] = useState(false);
  const [showSettings, setShowSettings] = useState(false);

  // Selection state for bulk actions
  const [selectedIds, setSelectedIds] = useState(new Set());
  const [focusedCell, setFocusedCell] = useState({ row: 0, col: 0 });

  // Filter & sort state
  const [filters, setFilters] = useState({ status: 'all', confidence: 'all' });
  const [sortConfig, setSortConfig] = useState({ key: null, direction: 'asc' });
  const [showFilters, setShowFilters] = useState(false);

  // Fetch data
  const fetchData = useCallback(async () => {
    try {
      setLoading(true);
      const [projectRes, valuesRes] = await Promise.all([
        projectsApi.getById(id),
        projectsApi.getValues(id)
      ]);
      setProject(projectRes.data);
      setValues(valuesRes.data.values || []);
    } catch (err) {
      toast.error(`Failed to load project: ${err.message}`);
    } finally {
      setLoading(false);
    }
  }, [id]);

  useEffect(() => {
    if (id) fetchData();
  }, [id, fetchData]);

  // Build table data with filtering and sorting
  const tableData = useMemo(() => {
    if (!project?.template?.fields || !project?.documents) {
      return { fields: [], documents: [], matrix: {}, filteredValues: [] };
    }

    // Apply filters
    let filteredValues = values.filter(v => {
      if (filters.status !== 'all' && v.status !== filters.status) return false;
      if (filters.confidence !== 'all') {
        const conf = v.confidence || 0;
        if (filters.confidence === 'high' && conf < 0.8) return false;
        if (filters.confidence === 'medium' && (conf < 0.5 || conf >= 0.8)) return false;
        if (filters.confidence === 'low' && conf >= 0.5) return false;
      }
      return true;
    });

    // Build matrix
    const matrix = {};
    filteredValues.forEach(v => {
      const key = `${v.template_field_id}-${v.document_id}`;
      matrix[key] = v;
    });

    // Get unique field IDs that have values after filtering
    const fieldIdsWithValues = new Set(filteredValues.map(v => v.template_field_id));
    let fields = project.template.fields;

    // If filtering by status or confidence, only show rows with matching values
    if (filters.status !== 'all' || filters.confidence !== 'all') {
      fields = fields.filter(f => fieldIdsWithValues.has(f.id));
    }

    // Apply sorting
    if (sortConfig.key) {
      fields = [...fields].sort((a, b) => {
        if (sortConfig.key === 'label') {
          const aVal = a.field_label.toLowerCase();
          const bVal = b.field_label.toLowerCase();
          return sortConfig.direction === 'asc'
            ? aVal.localeCompare(bVal)
            : bVal.localeCompare(aVal);
        }
        if (sortConfig.key === 'confidence') {
          const aConf = getAverageConfidence(a.id, matrix, project.documents);
          const bConf = getAverageConfidence(b.id, matrix, project.documents);
          return sortConfig.direction === 'asc' ? aConf - bConf : bConf - aConf;
        }
        return 0;
      });
    }

    return { fields, documents: project.documents, matrix, filteredValues };
  }, [project, values, filters, sortConfig]);

  // Helper to get average confidence for a field
  const getAverageConfidence = (fieldId, matrix, documents) => {
    let sum = 0, count = 0;
    documents.forEach(doc => {
      const v = matrix[`${fieldId}-${doc.id}`];
      if (v) {
        sum += v.confidence || 0;
        count++;
      }
    });
    return count > 0 ? sum / count : 0;
  };

  // Actions
  const handleApprove = async (valueId) => {
    try {
      const res = await projectsApi.approveValue(valueId);
      setValues(prev => prev.map(v => v.id === valueId ? res.data : v));
      toast.success('Value approved');
    } catch (err) {
      toast.error(`Failed to approve: ${err.message}`);
    }
  };

  const handleReject = async (valueId) => {
    try {
      const res = await projectsApi.rejectValue(valueId);
      setValues(prev => prev.map(v => v.id === valueId ? res.data : v));
      toast.success('Value rejected');
    } catch (err) {
      toast.error(`Failed to reject: ${err.message}`);
    }
  };

  const handleEdit = (value) => {
    setEditingValue(value);
    setEditInput(value.raw_value || '');
  };

  const handleSaveEdit = async () => {
    if (!editingValue) return;
    try {
      const res = await projectsApi.updateValue(editingValue.id, { raw_value: editInput });
      setValues(prev => prev.map(v => v.id === editingValue.id ? res.data : v));
      setEditingValue(null);
      toast.success('Value updated');
    } catch (err) {
      toast.error(`Failed to save: ${err.message}`);
    }
  };

  // Bulk actions
  const handleBulkApprove = async () => {
    if (selectedIds.size === 0) return;
    try {
      await projectsApi.bulkApprove(Array.from(selectedIds));
      setValues(prev => prev.map(v =>
        selectedIds.has(v.id) ? { ...v, status: 'approved' } : v
      ));
      toast.success(`Approved ${selectedIds.size} values`);
      setSelectedIds(new Set());
    } catch (err) {
      toast.error(`Bulk approve failed: ${err.message}`);
    }
  };

  const handleBulkReject = async () => {
    if (selectedIds.size === 0) return;
    try {
      await projectsApi.bulkReject(Array.from(selectedIds));
      setValues(prev => prev.map(v =>
        selectedIds.has(v.id) ? { ...v, status: 'rejected' } : v
      ));
      toast.success(`Rejected ${selectedIds.size} values`);
      setSelectedIds(new Set());
    } catch (err) {
      toast.error(`Bulk reject failed: ${err.message}`);
    }
  };

  const toggleSelect = (valueId) => {
    setSelectedIds(prev => {
      const next = new Set(prev);
      if (next.has(valueId)) {
        next.delete(valueId);
      } else {
        next.add(valueId);
      }
      return next;
    });
  };

  const selectAll = () => {
    const allIds = tableData.filteredValues.map(v => v.id);
    setSelectedIds(new Set(allIds));
  };

  const selectNone = () => {
    setSelectedIds(new Set());
  };

  const selectByStatus = (status) => {
    const ids = values.filter(v => v.status === status).map(v => v.id);
    setSelectedIds(new Set(ids));
  };

  // Export handlers
  const handleExport = async (format) => {
    try {
      const res = format === 'csv' ? await projectsApi.exportCsv(id) : await projectsApi.exportExcel(id);
      downloadBlob(res.data, `${project?.name?.replace(/\s+/g, '_') || 'export'}.${format === 'csv' ? 'csv' : 'xlsx'}`);
      toast.success(`Exported as ${format.toUpperCase()}`);
    } catch (err) {
      toast.error(`Export failed: ${err.message}`);
    }
  };

  // Sorting handler
  const handleSort = (key) => {
    setSortConfig(prev => ({
      key,
      direction: prev.key === key && prev.direction === 'asc' ? 'desc' : 'asc'
    }));
  };

  // Keyboard shortcuts
  useEffect(() => {
    const handleKeyDown = (e) => {
      // Don't trigger if typing in an input
      if (e.target.tagName === 'INPUT' || e.target.tagName === 'TEXTAREA') return;

      const { fields, documents, matrix } = tableData;
      if (!fields.length || !documents.length) return;

      const currentField = fields[focusedCell.row];
      const currentDoc = documents[focusedCell.col];
      const currentValue = currentField && currentDoc
        ? matrix[`${currentField.id}-${currentDoc.id}`]
        : null;

      switch (e.key) {
        case 'ArrowUp':
          e.preventDefault();
          setFocusedCell(prev => ({ ...prev, row: Math.max(0, prev.row - 1) }));
          break;
        case 'ArrowDown':
          e.preventDefault();
          setFocusedCell(prev => ({ ...prev, row: Math.min(fields.length - 1, prev.row + 1) }));
          break;
        case 'ArrowLeft':
          e.preventDefault();
          setFocusedCell(prev => ({ ...prev, col: Math.max(0, prev.col - 1) }));
          break;
        case 'ArrowRight':
          e.preventDefault();
          setFocusedCell(prev => ({ ...prev, col: Math.min(documents.length - 1, prev.col + 1) }));
          break;
        case 'a':
        case 'A':
          if (currentValue && !e.ctrlKey && !e.metaKey) {
            e.preventDefault();
            handleApprove(currentValue.id);
          }
          break;
        case 'r':
        case 'R':
          if (currentValue) {
            e.preventDefault();
            handleReject(currentValue.id);
          }
          break;
        case 'e':
        case 'E':
          if (currentValue) {
            e.preventDefault();
            handleEdit(currentValue);
          }
          break;
        case ' ':
          if (currentValue) {
            e.preventDefault();
            toggleSelect(currentValue.id);
          }
          break;
        case 'Escape':
          setSelectedIds(new Set());
          break;
        case '?':
          e.preventDefault();
          setShowShortcuts(true);
          break;
      }
    };

    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, [tableData, focusedCell]);

  // Stats for the stats bar
  const stats = useMemo(() => {
    return values.reduce((acc, v) => {
      acc[v.status] = (acc[v.status] || 0) + 1;
      acc.total++;
      return acc;
    }, { total: 0, pending: 0, approved: 0, rejected: 0, edited: 0 });
  }, [values]);

  // Loading state
  if (loading) {
    return <SkeletonReviewTable />;
  }

  if (!project) {
    return <Card className="text-center py-12 text-slate-400">Project not found</Card>;
  }

  const SortIcon = ({ field }) => {
    if (sortConfig.key !== field) return <ChevronDown className="w-4 h-4 text-slate-600" />;
    return sortConfig.direction === 'asc'
      ? <ChevronUp className="w-4 h-4 text-primary-400" />
      : <ChevronDown className="w-4 h-4 text-primary-400" />;
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-4">
          <button
            onClick={() => navigate(`/projects/${id}`)}
            className="p-2 text-slate-400 hover:text-white hover:bg-slate-700 rounded-lg transition-colors"
          >
            <ArrowLeft className="w-5 h-5" />
          </button>
          <div>
            <h1 className="text-3xl font-bold text-white">Review: {project.name}</h1>
            <p className="text-slate-400">Compare and approve extracted values across documents</p>
          </div>
        </div>
        <div className="flex gap-2">
          <Button
            variant="ghost"
            size="sm"
            icon={Settings}
            onClick={() => setShowSettings(true)}
            title="Project Settings"
          />
          <Button
            variant="ghost"
            size="sm"
            icon={History}
            onClick={() => setShowAuditLog(true)}
            title="Activity Log"
          />
          <Button
            variant="ghost"
            size="sm"
            icon={GitCompare}
            onClick={() => setShowComparison(true)}
            title="Compare Values"
          />
          <Button
            variant="ghost"
            size="sm"
            icon={Keyboard}
            onClick={() => setShowShortcuts(true)}
            title="Keyboard shortcuts (?)"
          />
          <Button
            variant={showAnalytics ? 'secondary' : 'ghost'}
            size="sm"
            icon={BarChart3}
            onClick={() => setShowAnalytics(!showAnalytics)}
          >
            Analytics
          </Button>
          <Button variant="ghost" size="sm" icon={Download} onClick={() => handleExport('csv')}>CSV</Button>
          <Button variant="secondary" size="sm" icon={Download} onClick={() => handleExport('excel')}>Excel</Button>
        </div>
      </div>

      {/* Analytics Panel */}
      {showAnalytics && (
        <div className="animate-fade-in">
          <Analytics
            values={values}
            fields={project.template?.fields || []}
            documents={project.documents || []}
          />
        </div>
      )}

      {/* Stats bar */}
      <div className="flex items-center justify-between">
        <div className="flex gap-4">
          <div className="px-4 py-2 bg-slate-800/50 rounded-lg text-sm">
            <span className="text-slate-400">Total:</span>{' '}
            <span className="text-white font-medium">{stats.total}</span>
          </div>
          <div className="px-4 py-2 bg-emerald-500/10 rounded-lg text-sm">
            <span className="text-emerald-400">Approved:</span>{' '}
            <span className="text-white font-medium">{stats.approved || 0}</span>
          </div>
          <div className="px-4 py-2 bg-amber-500/10 rounded-lg text-sm">
            <span className="text-amber-400">Pending:</span>{' '}
            <span className="text-white font-medium">{stats.pending || 0}</span>
          </div>
          <div className="px-4 py-2 bg-red-500/10 rounded-lg text-sm">
            <span className="text-red-400">Rejected:</span>{' '}
            <span className="text-white font-medium">{stats.rejected || 0}</span>
          </div>
        </div>

        {/* Filter toggle */}
        <Button
          variant={showFilters ? 'secondary' : 'ghost'}
          icon={Filter}
          onClick={() => setShowFilters(!showFilters)}
        >
          Filters
          {(filters.status !== 'all' || filters.confidence !== 'all') && (
            <span className="ml-2 px-1.5 py-0.5 text-xs bg-primary-500/30 rounded-full">
              Active
            </span>
          )}
        </Button>
      </div>

      {/* Filter panel */}
      {showFilters && (
        <div className="glass rounded-xl p-4 flex items-center gap-6 animate-fade-in">
          <div className="flex items-center gap-3">
            <label className="text-sm text-slate-400">Status:</label>
            <select
              value={filters.status}
              onChange={(e) => setFilters(prev => ({ ...prev, status: e.target.value }))}
              className="px-3 py-2 bg-slate-800 border border-slate-700 rounded-lg text-white text-sm focus:outline-none focus:ring-2 focus:ring-primary-500/50"
            >
              {FILTER_OPTIONS.status.map(opt => (
                <option key={opt.value} value={opt.value}>{opt.label}</option>
              ))}
            </select>
          </div>
          <div className="flex items-center gap-3">
            <label className="text-sm text-slate-400">Confidence:</label>
            <select
              value={filters.confidence}
              onChange={(e) => setFilters(prev => ({ ...prev, confidence: e.target.value }))}
              className="px-3 py-2 bg-slate-800 border border-slate-700 rounded-lg text-white text-sm focus:outline-none focus:ring-2 focus:ring-primary-500/50"
            >
              {FILTER_OPTIONS.confidence.map(opt => (
                <option key={opt.value} value={opt.value}>{opt.label}</option>
              ))}
            </select>
          </div>
          <button
            onClick={() => setFilters({ status: 'all', confidence: 'all' })}
            className="text-sm text-slate-400 hover:text-white"
          >
            Clear filters
          </button>
        </div>
      )}

      {/* Bulk action bar */}
      {selectedIds.size > 0 && (
        <div className="glass rounded-xl p-4 flex items-center justify-between animate-fade-in border border-primary-500/30">
          <div className="flex items-center gap-4">
            <span className="text-white font-medium">
              {selectedIds.size} selected
            </span>
            <button
              onClick={selectNone}
              className="text-sm text-slate-400 hover:text-white"
            >
              Clear selection
            </button>
          </div>
          <div className="flex gap-3">
            <Button variant="ghost" size="sm" icon={Check} onClick={handleBulkApprove}>
              Approve All
            </Button>
            <Button variant="ghost" size="sm" icon={X} onClick={handleBulkReject}>
              Reject All
            </Button>
          </div>
        </div>
      )}

      {/* Selection helpers */}
      <div className="flex items-center gap-4 text-sm">
        <span className="text-slate-500">Quick select:</span>
        <button onClick={selectAll} className="text-slate-400 hover:text-primary-400">
          All
        </button>
        <button onClick={selectNone} className="text-slate-400 hover:text-primary-400">
          None
        </button>
        <button onClick={() => selectByStatus('pending')} className="text-amber-400 hover:text-amber-300">
          Pending
        </button>
        <button onClick={() => selectByStatus('approved')} className="text-emerald-400 hover:text-emerald-300">
          Approved
        </button>
        <button onClick={() => selectByStatus('rejected')} className="text-red-400 hover:text-red-300">
          Rejected
        </button>
      </div>

      {/* Main comparison table */}
      <div className="glass rounded-2xl overflow-auto" ref={tableRef}>
        <table className="w-full border-collapse">
          <thead className="sticky top-0 bg-slate-900/95 backdrop-blur z-10">
            <tr>
              <th className="w-10 px-4 py-3 border-b border-slate-700">
                <button
                  onClick={() => selectedIds.size > 0 ? selectNone() : selectAll()}
                  className="text-slate-400 hover:text-white"
                >
                  {selectedIds.size > 0 ? (
                    <CheckSquare className="w-5 h-5" />
                  ) : (
                    <Square className="w-5 h-5" />
                  )}
                </button>
              </th>
              <th
                className="text-left px-4 py-3 text-sm font-medium text-slate-400 border-b border-slate-700 min-w-[200px] sticky left-0 bg-slate-900/95 cursor-pointer hover:text-white"
                onClick={() => handleSort('label')}
              >
                <div className="flex items-center gap-2">
                  Field
                  <SortIcon field="label" />
                </div>
              </th>
              {tableData.documents.map(doc => (
                <th
                  key={doc.id}
                  className="text-left px-4 py-3 text-sm font-medium text-slate-400 border-b border-slate-700 min-w-[300px]"
                >
                  {truncate(doc.original_filename, 25)}
                </th>
              ))}
            </tr>
          </thead>
          <tbody>
            {tableData.fields.length === 0 ? (
              <tr>
                <td
                  colSpan={tableData.documents.length + 2}
                  className="text-center py-12 text-slate-400"
                >
                  No values match the current filters.
                </td>
              </tr>
            ) : (
              tableData.fields.map((field, rowIdx) => (
                <tr
                  key={field.id}
                  className={`hover:bg-slate-800/30 ${focusedCell.row === rowIdx ? 'bg-slate-800/20' : ''}`}
                >
                  <td className="px-4 py-3 border-b border-slate-700/30">
                    {/* Row checkbox - select all values in this row */}
                  </td>
                  <td className="px-4 py-3 border-b border-slate-700/30 sticky left-0 bg-surface/95">
                    <div className="font-medium text-white">{field.field_label}</div>
                    <div className="text-xs text-slate-500">{field.field_type}</div>
                  </td>
                  {tableData.documents.map((doc, colIdx) => {
                    const value = tableData.matrix[`${field.id}-${doc.id}`];
                    const isFocused = focusedCell.row === rowIdx && focusedCell.col === colIdx;
                    const isSelected = value && selectedIds.has(value.id);

                    return (
                      <td
                        key={doc.id}
                        className={`px-4 py-3 border-b border-slate-700/30 ${isFocused ? 'ring-2 ring-primary-500/50 ring-inset' : ''} ${isSelected ? 'bg-primary-500/10' : ''}`}
                        onClick={() => setFocusedCell({ row: rowIdx, col: colIdx })}
                      >
                        {value ? (
                          <div className="space-y-2">
                            <div className="flex items-start gap-2">
                              <button
                                onClick={(e) => { e.stopPropagation(); toggleSelect(value.id); }}
                                className="mt-1 text-slate-400 hover:text-primary-400 flex-shrink-0"
                              >
                                {isSelected ? (
                                  <CheckSquare className="w-4 h-4 text-primary-400" />
                                ) : (
                                  <Square className="w-4 h-4" />
                                )}
                              </button>
                              <span className="text-white">{value.normalized_value || value.raw_value || '-'}</span>
                            </div>
                            <div className="flex items-center gap-2">
                              <ConfidenceBadge value={value.confidence} />
                              <StatusBadge status={value.status} />
                            </div>
                            {value.citation && (
                              <button
                                onClick={() => setCitationModal(value)}
                                className="flex items-center gap-1 text-xs text-slate-500 hover:text-primary-400"
                              >
                                <Info className="w-3 h-3" />
                                {truncate(value.citation, 20)}
                              </button>
                            )}
                            <div className="flex gap-1">
                              <button
                                onClick={() => handleApprove(value.id)}
                                className="p-1.5 text-emerald-400 hover:bg-emerald-500/20 rounded transition-colors"
                                title="Approve (A)"
                              >
                                <Check className="w-4 h-4" />
                              </button>
                              <button
                                onClick={() => handleReject(value.id)}
                                className="p-1.5 text-red-400 hover:bg-red-500/20 rounded transition-colors"
                                title="Reject (R)"
                              >
                                <X className="w-4 h-4" />
                              </button>
                              <button
                                onClick={() => handleEdit(value)}
                                className="p-1.5 text-slate-400 hover:bg-slate-700 rounded transition-colors"
                                title="Edit (E)"
                              >
                                <Pencil className="w-4 h-4" />
                              </button>
                              <button
                                onClick={() => setCommentsValueId(value.id)}
                                className="p-1.5 text-indigo-400 hover:bg-indigo-500/20 rounded transition-colors"
                                title="Comments"
                              >
                                <MessageSquare className="w-4 h-4" />
                              </button>
                              <button
                                onClick={() => setDocumentPreview({ 
                                  document: doc, 
                                  citationText: value.citation_text 
                                })}
                                className="p-1.5 text-slate-400 hover:bg-slate-700 rounded transition-colors"
                                title="View Document"
                              >
                                <Eye className="w-4 h-4" />
                              </button>
                            </div>
                          </div>
                        ) : (
                          <span className="text-slate-500">-</span>
                        )}
                      </td>
                    );
                  })}
                </tr>
              ))
            )}
          </tbody>
        </table>
      </div>

      {/* Edit modal */}
      <Modal
        isOpen={!!editingValue}
        onClose={() => setEditingValue(null)}
        title={`Edit: ${editingValue?.field_label || ''}`}
        size="md"
      >
        <div className="space-y-4">
          <div>
            <label className="block text-sm font-medium text-slate-300 mb-2">Value</label>
            <textarea
              value={editInput}
              onChange={(e) => setEditInput(e.target.value)}
              className="w-full px-4 py-3 bg-slate-800 border border-slate-700 rounded-xl text-white placeholder-slate-500 focus:outline-none focus:ring-2 focus:ring-primary-500/50"
              rows={4}
              autoFocus
            />
          </div>
          {editingValue?.citation && (
            <div>
              <label className="block text-sm font-medium text-slate-300 mb-2">Citation</label>
              <p className="text-sm text-slate-400 bg-slate-800/50 p-3 rounded-lg">{editingValue.citation}</p>
            </div>
          )}
          <div className="flex justify-end gap-3">
            <Button variant="ghost" onClick={() => setEditingValue(null)}>Cancel</Button>
            <Button icon={Save} onClick={handleSaveEdit}>Save Changes</Button>
          </div>
        </div>
      </Modal>

      {/* Citation details modal */}
      <Modal
        isOpen={!!citationModal}
        onClose={() => setCitationModal(null)}
        title="Citation Details"
        size="md"
      >
        {citationModal && (
          <div className="space-y-4">
            <div>
              <label className="block text-sm font-medium text-slate-300 mb-2">Location</label>
              <p className="text-white">{citationModal.citation}</p>
            </div>
            {citationModal.citation_text && (
              <div>
                <label className="block text-sm font-medium text-slate-300 mb-2">Quoted Text</label>
                <blockquote className="text-slate-300 bg-slate-800/50 p-4 rounded-lg border-l-4 border-primary-500 italic">
                  "{citationModal.citation_text}"
                </blockquote>
              </div>
            )}
            <div>
              <label className="block text-sm font-medium text-slate-300 mb-2">Confidence</label>
              <ConfidenceBadge value={citationModal.confidence} showBar />
            </div>
          </div>
        )}
      </Modal>

      {/* Keyboard shortcuts modal */}
      <Modal
        isOpen={showShortcuts}
        onClose={() => setShowShortcuts(false)}
        title="Keyboard Shortcuts"
        size="md"
      >
        <div className="space-y-4">
          <div className="grid grid-cols-2 gap-4">
            <ShortcutItem keys={['↑', '↓', '←', '→']} description="Navigate cells" />
            <ShortcutItem keys={['A']} description="Approve selected value" />
            <ShortcutItem keys={['R']} description="Reject selected value" />
            <ShortcutItem keys={['E']} description="Edit selected value" />
            <ShortcutItem keys={['Space']} description="Toggle selection" />
            <ShortcutItem keys={['Esc']} description="Clear selection" />
            <ShortcutItem keys={['?']} description="Show this help" />
          </div>
        </div>
      </Modal>

      {/* Document Preview */}
      {documentPreview && (
        <DocumentPreview
          document={documentPreview.document}
          citationText={documentPreview.citationText}
          onClose={() => setDocumentPreview(null)}
        />
      )}

      {/* Comments Panel */}
      {commentsValueId && (
        <CommentsPanel
          valueId={commentsValueId}
          onClose={() => setCommentsValueId(null)}
        />
      )}

      {/* Audit Log */}
      {showAuditLog && (
        <AuditLog
          projectId={id}
          onClose={() => setShowAuditLog(false)}
        />
      )}

      {/* Value Comparison */}
      {showComparison && (
        <ValueComparison
          fields={tableData.fields}
          documents={tableData.documents}
          matrix={tableData.matrix}
          onClose={() => setShowComparison(false)}
        />
      )}

      {/* Project Settings */}
      {showSettings && (
        <ProjectSettings
          projectId={id}
          onClose={() => setShowSettings(false)}
          onSave={fetchData}
        />
      )}
    </div>
  );
}

function ShortcutItem({ keys, description }) {
  return (
    <div className="flex items-center gap-3">
      <div className="flex gap-1">
        {keys.map((key, i) => (
          <kbd
            key={i}
            className="px-2 py-1 bg-slate-700 border border-slate-600 rounded text-sm text-white font-mono"
          >
            {key}
          </kbd>
        ))}
      </div>
      <span className="text-slate-400">{description}</span>
    </div>
  );
}

export default ReviewTable;
