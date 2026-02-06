import { useState, useEffect } from 'react';
import { X, Send, Trash2, MessageSquare, Clock, Edit2, Check } from 'lucide-react';
import { commentsApi } from '../api/index.js';
import Skeleton from './Skeleton.jsx';
import toast from 'react-hot-toast';

function CommentsPanel({ valueId, onClose }) {
  const [comments, setComments] = useState([]);
  const [loading, setLoading] = useState(true);
  const [newComment, setNewComment] = useState('');
  const [submitting, setSubmitting] = useState(false);
  const [editingId, setEditingId] = useState(null);
  const [editContent, setEditContent] = useState('');

  useEffect(() => {
    fetchComments();
  }, [valueId]);

  const fetchComments = async () => {
    try {
      setLoading(true);
      const response = await commentsApi.getForValue(valueId);
      setComments(response.data.comments || []);
    } catch (err) {
      toast.error('Failed to load comments');
    } finally {
      setLoading(false);
    }
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!newComment.trim()) return;

    try {
      setSubmitting(true);
      await commentsApi.create(valueId, newComment.trim());
      setNewComment('');
      await fetchComments();
      toast.success('Comment added');
    } catch (err) {
      toast.error('Failed to add comment');
    } finally {
      setSubmitting(false);
    }
  };

  const handleEdit = (comment) => {
    setEditingId(comment.id);
    setEditContent(comment.content);
  };

  const handleSaveEdit = async (commentId) => {
    if (!editContent.trim()) return;

    try {
      await commentsApi.update(commentId, editContent.trim());
      setEditingId(null);
      setEditContent('');
      await fetchComments();
      toast.success('Comment updated');
    } catch (err) {
      toast.error('Failed to update comment');
    }
  };

  const handleDelete = async (commentId) => {
    if (!confirm('Delete this comment?')) return;

    try {
      await commentsApi.delete(commentId);
      await fetchComments();
      toast.success('Comment deleted');
    } catch (err) {
      toast.error('Failed to delete comment');
    }
  };

  const formatDate = (dateString) => {
    const date = new Date(dateString);
    const now = new Date();
    const diff = now - date;
    
    if (diff < 60000) return 'just now';
    if (diff < 3600000) return `${Math.floor(diff / 60000)}m ago`;
    if (diff < 86400000) return `${Math.floor(diff / 3600000)}h ago`;
    return date.toLocaleDateString();
  };

  return (
    <div className="fixed inset-y-0 right-0 z-50 w-96 bg-slate-800 dark:bg-slate-800 light:bg-white shadow-2xl border-l border-slate-700 dark:border-slate-700 light:border-slate-200 flex flex-col">
      {/* Header */}
      <div className="flex items-center justify-between p-4 border-b border-slate-700 dark:border-slate-700 light:border-slate-200">
        <div className="flex items-center gap-3">
          <MessageSquare className="w-5 h-5 text-indigo-400" />
          <h2 className="text-lg font-semibold text-white dark:text-white light:text-slate-900">
            Comments
          </h2>
          <span className="px-2 py-0.5 bg-slate-700 dark:bg-slate-700 light:bg-slate-200 text-slate-300 dark:text-slate-300 light:text-slate-600 text-xs rounded-full">
            {comments.length}
          </span>
        </div>
        <button
          onClick={onClose}
          className="p-2 text-slate-400 hover:text-white hover:bg-slate-700 rounded-lg transition-colors"
        >
          <X className="w-5 h-5" />
        </button>
      </div>

      {/* Comments list */}
      <div className="flex-1 overflow-auto p-4 space-y-4">
        {loading ? (
          <>
            <Skeleton className="h-20 w-full" />
            <Skeleton className="h-20 w-full" />
          </>
        ) : comments.length === 0 ? (
          <div className="text-center py-12 text-slate-400">
            <MessageSquare className="w-12 h-12 mx-auto mb-3 opacity-50" />
            <p>No comments yet</p>
            <p className="text-sm mt-1">Be the first to add a note</p>
          </div>
        ) : (
          comments.map((comment) => (
            <div
              key={comment.id}
              className="bg-slate-700/50 dark:bg-slate-700/50 light:bg-slate-100 rounded-lg p-4"
            >
              <div className="flex items-start justify-between mb-2">
                <div className="flex items-center gap-2">
                  <div className="w-8 h-8 bg-indigo-600/30 rounded-full flex items-center justify-center text-indigo-300 text-sm font-medium">
                    {comment.author?.charAt(0).toUpperCase() || 'U'}
                  </div>
                  <div>
                    <p className="text-sm font-medium text-white dark:text-white light:text-slate-900">
                      {comment.author || 'User'}
                    </p>
                    <p className="text-xs text-slate-400 flex items-center gap-1">
                      <Clock className="w-3 h-3" />
                      {formatDate(comment.created_at)}
                    </p>
                  </div>
                </div>
                
                <div className="flex items-center gap-1">
                  {editingId !== comment.id && (
                    <>
                      <button
                        onClick={() => handleEdit(comment)}
                        className="p-1.5 text-slate-400 hover:text-white hover:bg-slate-600 rounded transition-colors"
                        title="Edit"
                      >
                        <Edit2 className="w-3.5 h-3.5" />
                      </button>
                      <button
                        onClick={() => handleDelete(comment.id)}
                        className="p-1.5 text-slate-400 hover:text-red-400 hover:bg-slate-600 rounded transition-colors"
                        title="Delete"
                      >
                        <Trash2 className="w-3.5 h-3.5" />
                      </button>
                    </>
                  )}
                </div>
              </div>
              
              {editingId === comment.id ? (
                <div className="space-y-2">
                  <textarea
                    value={editContent}
                    onChange={(e) => setEditContent(e.target.value)}
                    className="w-full px-3 py-2 bg-slate-600 border border-slate-500 rounded-lg text-white text-sm resize-none focus:outline-none focus:ring-2 focus:ring-indigo-500"
                    rows={3}
                  />
                  <div className="flex gap-2">
                    <button
                      onClick={() => handleSaveEdit(comment.id)}
                      className="px-3 py-1.5 bg-indigo-600 hover:bg-indigo-700 text-white text-sm rounded-lg flex items-center gap-1"
                    >
                      <Check className="w-3.5 h-3.5" />
                      Save
                    </button>
                    <button
                      onClick={() => setEditingId(null)}
                      className="px-3 py-1.5 bg-slate-600 hover:bg-slate-500 text-white text-sm rounded-lg"
                    >
                      Cancel
                    </button>
                  </div>
                </div>
              ) : (
                <p className="text-slate-300 dark:text-slate-300 light:text-slate-600 text-sm whitespace-pre-wrap">
                  {comment.content}
                </p>
              )}
            </div>
          ))
        )}
      </div>

      {/* New comment form */}
      <form onSubmit={handleSubmit} className="p-4 border-t border-slate-700 dark:border-slate-700 light:border-slate-200">
        <div className="flex gap-2">
          <textarea
            value={newComment}
            onChange={(e) => setNewComment(e.target.value)}
            placeholder="Add a note or comment..."
            className="flex-1 px-3 py-2 bg-slate-700 dark:bg-slate-700 light:bg-slate-100 border border-slate-600 dark:border-slate-600 light:border-slate-300 rounded-lg text-white dark:text-white light:text-slate-900 placeholder-slate-400 text-sm resize-none focus:outline-none focus:ring-2 focus:ring-indigo-500"
            rows={2}
          />
          <button
            type="submit"
            disabled={!newComment.trim() || submitting}
            className="px-4 bg-indigo-600 hover:bg-indigo-700 disabled:opacity-50 disabled:cursor-not-allowed text-white rounded-lg transition-colors"
          >
            <Send className="w-4 h-4" />
          </button>
        </div>
      </form>
    </div>
  );
}

export default CommentsPanel;

