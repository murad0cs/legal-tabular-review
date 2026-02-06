import { useState, useEffect } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { Layers, Plus, Pencil, Trash2 } from 'lucide-react';
import Button from '../components/Button.jsx';
import Card from '../components/Card.jsx';
import Modal from '../components/Modal.jsx';
import { templatesApi } from '../api/index.js';
import { DOCUMENT_TYPES } from '../constants/index.js';
import { formatDate } from '../utils/format.js';

function Templates() {
  const navigate = useNavigate();
  const [templates, setTemplates] = useState([]);
  const [loading, setLoading] = useState(true);
  const [showCreateModal, setShowCreateModal] = useState(false);
  const [formData, setFormData] = useState({ name: '', description: '', document_type: 'nda' });

  const fetchTemplates = async () => {
    try {
      setLoading(true);
      const res = await templatesApi.getAll();
      setTemplates(res.data.templates || []);
    } catch (err) {
      console.error('Failed to fetch templates:', err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => { fetchTemplates(); }, []);

  const handleCreate = async (e) => {
    e.preventDefault();
    try {
      const res = await templatesApi.create(formData);
      navigate(`/templates/${res.data.id}`);
    } catch (err) {
      alert(`Create failed: ${err.message}`);
    }
  };

  const handleDelete = async (id) => {
    if (!confirm('Are you sure you want to delete this template?')) return;
    try {
      await templatesApi.delete(id);
      setTemplates(templates.filter(t => t.id !== id));
    } catch (err) {
      alert(`Delete failed: ${err.message}`);
    }
  };

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold text-white mb-2">Templates</h1>
          <p className="text-slate-400">Define field extraction schemas for different document types.</p>
        </div>
        <Button icon={Plus} onClick={() => setShowCreateModal(true)}>Create Template</Button>
      </div>

      {loading ? (
        <div className="text-center py-12">
          <div className="animate-spin w-8 h-8 border-2 border-primary-500 border-t-transparent rounded-full mx-auto" />
        </div>
      ) : templates.length > 0 ? (
        <div className="grid grid-cols-3 gap-6">
          {templates.map(template => (
            <Card key={template.id} className="relative group">
              <div className="absolute top-4 right-4 flex gap-2 opacity-0 group-hover:opacity-100 transition-opacity">
                <Link to={`/templates/${template.id}`} className="p-2 text-slate-400 hover:text-white hover:bg-slate-700 rounded-lg transition-colors">
                  <Pencil className="w-4 h-4" />
                </Link>
                <button onClick={() => handleDelete(template.id)} className="p-2 text-slate-400 hover:text-red-400 hover:bg-red-500/10 rounded-lg transition-colors">
                  <Trash2 className="w-4 h-4" />
                </button>
              </div>
              <h3 className="text-xl font-semibold text-white mb-2">{template.name}</h3>
              <p className="text-slate-400 text-sm mb-4 line-clamp-2">{template.description || 'No description'}</p>
              <div className="flex items-center justify-between text-sm">
                <span className="text-slate-500">{template.fields?.length || 0} fields</span>
                <span className="text-slate-500">{formatDate(template.created_at)}</span>
              </div>
              <Link to={`/templates/${template.id}`} className="mt-4 block text-center py-2 text-primary-400 hover:text-primary-300 text-sm">
                Edit Fields
              </Link>
            </Card>
          ))}
        </div>
      ) : (
        <Card className="text-center py-12">
          <Layers className="w-16 h-16 text-slate-600 mx-auto mb-4" />
          <h3 className="text-xl font-medium text-white mb-2">No templates yet</h3>
          <p className="text-slate-400 mb-6">Create your first template to define extraction fields.</p>
          <Button icon={Plus} onClick={() => setShowCreateModal(true)}>Create Template</Button>
        </Card>
      )}

      <Modal isOpen={showCreateModal} onClose={() => setShowCreateModal(false)} title="Create Template" size="md">
        <form onSubmit={handleCreate} className="space-y-4">
          <div>
            <label className="block text-sm font-medium text-slate-300 mb-2">Template Name</label>
            <input
              type="text"
              value={formData.name}
              onChange={(e) => setFormData({ ...formData, name: e.target.value })}
              className="w-full px-4 py-3 bg-slate-800 border border-slate-700 rounded-xl text-white placeholder-slate-500 focus:outline-none focus:ring-2 focus:ring-primary-500/50"
              placeholder="Enter template name"
              required
            />
          </div>
          <div>
            <label className="block text-sm font-medium text-slate-300 mb-2">Document Type</label>
            <select
              value={formData.document_type}
              onChange={(e) => setFormData({ ...formData, document_type: e.target.value })}
              className="w-full px-4 py-3 bg-slate-800 border border-slate-700 rounded-xl text-white focus:outline-none focus:ring-2 focus:ring-primary-500/50"
            >
              {DOCUMENT_TYPES.map(type => (
                <option key={type.value} value={type.value}>{type.label}</option>
              ))}
            </select>
          </div>
          <div>
            <label className="block text-sm font-medium text-slate-300 mb-2">Description</label>
            <textarea
              value={formData.description}
              onChange={(e) => setFormData({ ...formData, description: e.target.value })}
              className="w-full px-4 py-3 bg-slate-800 border border-slate-700 rounded-xl text-white placeholder-slate-500 focus:outline-none focus:ring-2 focus:ring-primary-500/50"
              placeholder="Brief description of this template"
              rows={3}
            />
          </div>
          <div className="flex justify-end gap-3">
            <Button variant="ghost" type="button" onClick={() => setShowCreateModal(false)}>Cancel</Button>
            <Button type="submit">Create Template</Button>
          </div>
        </form>
      </Modal>
    </div>
  );
}

export default Templates;
