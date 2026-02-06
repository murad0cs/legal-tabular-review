import { useState, useEffect } from 'react';
import { X, History, Check, X as XIcon, Edit2, MessageSquare, FileText, Settings, Zap, ChevronDown, ChevronUp } from 'lucide-react';
import { auditApi } from '../api/index.js';
import Skeleton from './Skeleton.jsx';

const ACTION_ICONS = {
  extracted: Zap,
  auto_approved: Check,
  status_change: Edit2,
  value_edited: Edit2,
  comment_added: MessageSquare,
  comment_updated: MessageSquare,
  comment_deleted: MessageSquare,
  approved: Check,
  rejected: XIcon,
};

const ACTION_COLORS = {
  extracted: 'text-blue-400 bg-blue-500/20',
  auto_approved: 'text-green-400 bg-green-500/20',
  status_change: 'text-amber-400 bg-amber-500/20',
  value_edited: 'text-purple-400 bg-purple-500/20',
  comment_added: 'text-indigo-400 bg-indigo-500/20',
  comment_updated: 'text-indigo-400 bg-indigo-500/20',
  comment_deleted: 'text-red-400 bg-red-500/20',
  approved: 'text-green-400 bg-green-500/20',
  rejected: 'text-red-400 bg-red-500/20',
};

function AuditLog({ projectId, onClose }) {
  const [logs, setLogs] = useState([]);
  const [loading, setLoading] = useState(true);
  const [total, setTotal] = useState(0);
  const [expandedLogs, setExpandedLogs] = useState({});

  useEffect(() => {
    fetchLogs();
  }, [projectId]);

  const fetchLogs = async () => {
    try {
      setLoading(true);
      const response = await auditApi.getForProject(projectId);
      setLogs(response.data.logs || []);
      setTotal(response.data.total || 0);
    } catch (err) {
      console.error('Failed to load audit logs:', err);
    } finally {
      setLoading(false);
    }
  };

  const toggleExpand = (logId) => {
    setExpandedLogs(prev => ({ ...prev, [logId]: !prev[logId] }));
  };

  const formatDate = (dateString) => {
    const date = new Date(dateString);
    return date.toLocaleString('en-US', {
      month: 'short',
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit',
    });
  };

  const getActionDescription = (log) => {
    switch (log.action) {
      case 'extracted':
        return 'Value extracted';
      case 'auto_approved':
        return 'Auto-approved (high confidence)';
      case 'status_change':
        return log.description || `Status changed: ${log.old_value?.status} → ${log.new_value?.status}`;
      case 'value_edited':
        return 'Value edited';
      case 'comment_added':
        return 'Comment added';
      case 'comment_updated':
        return 'Comment updated';
      case 'comment_deleted':
        return 'Comment deleted';
      default:
        return log.action.replace(/_/g, ' ');
    }
  };

  const Icon = (action) => ACTION_ICONS[action] || History;

  return (
    <div className="fixed inset-y-0 right-0 z-50 w-[450px] bg-slate-800 dark:bg-slate-800 light:bg-white shadow-2xl border-l border-slate-700 dark:border-slate-700 light:border-slate-200 flex flex-col">
      {/* Header */}
      <div className="flex items-center justify-between p-4 border-b border-slate-700 dark:border-slate-700 light:border-slate-200">
        <div className="flex items-center gap-3">
          <History className="w-5 h-5 text-indigo-400" />
          <h2 className="text-lg font-semibold text-white dark:text-white light:text-slate-900">
            Activity Log
          </h2>
          <span className="px-2 py-0.5 bg-slate-700 dark:bg-slate-700 light:bg-slate-200 text-slate-300 dark:text-slate-300 light:text-slate-600 text-xs rounded-full">
            {total}
          </span>
        </div>
        <button
          onClick={onClose}
          className="p-2 text-slate-400 hover:text-white hover:bg-slate-700 rounded-lg transition-colors"
        >
          <X className="w-5 h-5" />
        </button>
      </div>

      {/* Logs list */}
      <div className="flex-1 overflow-auto">
        {loading ? (
          <div className="p-4 space-y-4">
            <Skeleton className="h-16 w-full" />
            <Skeleton className="h-16 w-full" />
            <Skeleton className="h-16 w-full" />
          </div>
        ) : logs.length === 0 ? (
          <div className="text-center py-12 text-slate-400">
            <History className="w-12 h-12 mx-auto mb-3 opacity-50" />
            <p>No activity yet</p>
          </div>
        ) : (
          <div className="relative">
            {/* Timeline line */}
            <div className="absolute left-8 top-0 bottom-0 w-0.5 bg-slate-700" />
            
            {logs.map((log, index) => {
              const ActionIcon = Icon(log.action);
              const colorClass = ACTION_COLORS[log.action] || 'text-slate-400 bg-slate-500/20';
              const isExpanded = expandedLogs[log.id];
              
              return (
                <div
                  key={log.id}
                  className="relative px-4 py-3 hover:bg-slate-700/30 transition-colors"
                >
                  {/* Timeline dot */}
                  <div className={`absolute left-6 w-5 h-5 rounded-full flex items-center justify-center ${colorClass}`}>
                    <ActionIcon className="w-3 h-3" />
                  </div>
                  
                  <div className="ml-10">
                    <div className="flex items-start justify-between">
                      <div>
                        <p className="text-sm font-medium text-white dark:text-white light:text-slate-900">
                          {getActionDescription(log)}
                        </p>
                        <p className="text-xs text-slate-400 mt-0.5">
                          by {log.user} • {formatDate(log.created_at)}
                        </p>
                      </div>
                      
                      {(log.old_value || log.new_value) && (
                        <button
                          onClick={() => toggleExpand(log.id)}
                          className="p-1 text-slate-400 hover:text-white"
                        >
                          {isExpanded ? (
                            <ChevronUp className="w-4 h-4" />
                          ) : (
                            <ChevronDown className="w-4 h-4" />
                          )}
                        </button>
                      )}
                    </div>
                    
                    {/* Expanded details */}
                    {isExpanded && (log.old_value || log.new_value) && (
                      <div className="mt-3 p-3 bg-slate-700/50 rounded-lg text-xs font-mono space-y-2">
                        {log.old_value && (
                          <div>
                            <span className="text-red-400">- Old: </span>
                            <span className="text-slate-300">
                              {typeof log.old_value === 'object' 
                                ? JSON.stringify(log.old_value, null, 2)
                                : log.old_value}
                            </span>
                          </div>
                        )}
                        {log.new_value && (
                          <div>
                            <span className="text-green-400">+ New: </span>
                            <span className="text-slate-300">
                              {typeof log.new_value === 'object'
                                ? JSON.stringify(log.new_value, null, 2)
                                : log.new_value}
                            </span>
                          </div>
                        )}
                      </div>
                    )}
                  </div>
                </div>
              );
            })}
          </div>
        )}
      </div>
    </div>
  );
}

export default AuditLog;


