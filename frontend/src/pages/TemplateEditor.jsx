import { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { ArrowLeft, Plus, GripVertical, Pencil, Trash2, FileText, Calendar, DollarSign, Users, FileCheck } from 'lucide-react';
import Button from '../components/Button.jsx';
import Card from '../components/Card.jsx';
import Modal from '../components/Modal.jsx';
import { templatesApi } from '../api/index.js';
import { FIELD_TYPES, NORMALIZATION_RULES } from '../constants/index.js';

const TYPE_ICONS = {
  text: FileText,
  date: Calendar,
  currency: DollarSign,
  party: Users,
  clause: FileCheck,
};

const INITIAL_FIELD = {
  field_name: '',
  field_label: '',
  field_type: 'text',
  description: '',
  normalization_rule: '',
  is_required: false,
};

function TemplateEditor() {
  const { id } = useParams();
  const navigate = useNavigate();
  const [template, setTemplate] = useState(null);
  const [loading, setLoading] = useState(true);
  const [showFieldModal, setShowFieldModal] = useState(false);
  const [editingField, setEditingField] = useState(null);
  const [fieldForm, setFieldForm] = useState(INITIAL_FIELD);

  const fetchTemplate = async () => {
    try {
      setLoading(true);
      const res = await templatesApi.getById(id);
      setTemplate(res.data);
    } catch (err) {
      console.error('Failed to fetch template:', err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => { if (id) fetchTemplate(); }, [id]);

  const openFieldModal = (field = null) => {
    setEditingField(field);
    setFieldForm(field ? {
      field_name: field.field_name,
      field_label: field.field_label,
      field_type: field.field_type,
      description: field.description || '',
      normalization_rule: field.normalization_rule || '',
      is_required: field.is_required,
    } : INITIAL_FIELD);
    setShowFieldModal(true);
  };

  const handleSaveField = async (e) => {
    e.preventDefault();
    try {
      if (editingField) {
        await templatesApi.updateField(id, editingField.id, fieldForm);
      } else {
        await templatesApi.addField(id, fieldForm);
      }
      fetchTemplate();
      setShowFieldModal(false);
    } catch (err) {
      alert(`Save failed: ${err.message}`);
    }
  };

  const handleDeleteField = async (fieldId) => {
    if (!confirm('Are you sure you want to delete this field?')) return;
    try {
      await templatesApi.deleteField(id, fieldId);
      fetchTemplate();
    } catch (err) {
      alert(`Delete failed: ${err.message}`);
    }
  };

  const handleAutoGenerateName = () => {
    if (fieldForm.field_label && !editingField) {
      const name = fieldForm.field_label.toLowerCase().replace(/[^a-z0-9\s]/g, '').replace(/\s+/g, '_');
      setFieldForm(prev => ({ ...prev, field_name: name }));
    }
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="animate-spin w-8 h-8 border-2 border-primary-500 border-t-transparent rounded-full" />
      </div>
    );
  }

  if (!template) {
    return <Card className="text-center py-12 text-slate-400">Template not found</Card>;
  }

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-4">
          <button onClick={() => navigate('/templates')} className="p-2 text-slate-400 hover:text-white hover:bg-slate-700 rounded-lg transition-colors">
            <ArrowLeft className="w-5 h-5" />
          </button>
          <div>
            <h1 className="text-3xl font-bold text-white">{template.name}</h1>
            <p className="text-slate-400">{template.description || 'No description'}</p>
          </div>
        </div>
        <Button icon={Plus} onClick={() => openFieldModal()}>Add Field</Button>
      </div>

      <Card>
        <h2 className="text-lg font-semibold text-white mb-4">Fields ({template.fields?.length || 0})</h2>
        {template.fields?.length > 0 ? (
          <div className="space-y-2">
            {template.fields.map(field => {
              const Icon = TYPE_ICONS[field.field_type] || FileText;
              return (
                <div key={field.id} className="flex items-center gap-4 p-4 bg-slate-800/50 rounded-xl group">
                  <GripVertical className="w-5 h-5 text-slate-600 cursor-grab" />
                  <div className="w-10 h-10 rounded-lg bg-slate-700/50 flex items-center justify-center">
                    <Icon className="w-5 h-5 text-slate-400" />
                  </div>
                  <div className="flex-1">
                    <div className="flex items-center gap-2">
                      <span className="font-medium text-white">{field.field_label}</span>
                      {field.is_required && <span className="px-2 py-0.5 text-xs rounded-full bg-red-500/20 text-red-400">Required</span>}
                    </div>
                    <p className="text-sm text-slate-500">
                      {field.field_name} • {field.field_type}
                      {field.normalization_rule && ` • ${field.normalization_rule}`}
                    </p>
                    {field.description && <p className="text-sm text-slate-500 mt-1">{field.description}</p>}
                  </div>
                  <div className="flex gap-2 opacity-0 group-hover:opacity-100 transition-opacity">
                    <button onClick={() => openFieldModal(field)} className="p-2 text-slate-400 hover:text-white hover:bg-slate-700 rounded-lg transition-colors">
                      <Pencil className="w-4 h-4" />
                    </button>
                    <button onClick={() => handleDeleteField(field.id)} className="p-2 text-slate-400 hover:text-red-400 hover:bg-red-500/10 rounded-lg transition-colors">
                      <Trash2 className="w-4 h-4" />
                    </button>
                  </div>
                </div>
              );
            })}
          </div>
        ) : (
          <div className="text-center py-8 text-slate-400">No fields defined. Add your first field to get started.</div>
        )}
      </Card>

      <Modal isOpen={showFieldModal} onClose={() => setShowFieldModal(false)} title={editingField ? 'Edit Field' : 'Add Field'} size="md">
        <form onSubmit={handleSaveField} className="space-y-4">
          <div>
            <label className="block text-sm font-medium text-slate-300 mb-2">Field Label</label>
            <input
              type="text"
              value={fieldForm.field_label}
              onChange={(e) => setFieldForm({ ...fieldForm, field_label: e.target.value })}
              onBlur={handleAutoGenerateName}
              className="w-full px-4 py-3 bg-slate-800 border border-slate-700 rounded-xl text-white placeholder-slate-500 focus:outline-none focus:ring-2 focus:ring-primary-500/50"
              placeholder="e.g., Effective Date"
              required
            />
          </div>
          <div>
            <label className="block text-sm font-medium text-slate-300 mb-2">Field Name (Internal)</label>
            <input
              type="text"
              value={fieldForm.field_name}
              onChange={(e) => setFieldForm({ ...fieldForm, field_name: e.target.value.toLowerCase().replace(/\s+/g, '_') })}
              className="w-full px-4 py-3 bg-slate-800 border border-slate-700 rounded-xl text-white placeholder-slate-500 focus:outline-none focus:ring-2 focus:ring-primary-500/50"
              placeholder="e.g., effective_date"
              required
            />
          </div>
          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="block text-sm font-medium text-slate-300 mb-2">Field Type</label>
              <select
                value={fieldForm.field_type}
                onChange={(e) => setFieldForm({ ...fieldForm, field_type: e.target.value })}
                className="w-full px-4 py-3 bg-slate-800 border border-slate-700 rounded-xl text-white focus:outline-none focus:ring-2 focus:ring-primary-500/50"
              >
                {FIELD_TYPES.map(t => <option key={t.value} value={t.value}>{t.label}</option>)}
              </select>
            </div>
            <div>
              <label className="block text-sm font-medium text-slate-300 mb-2">Normalization</label>
              <select
                value={fieldForm.normalization_rule}
                onChange={(e) => setFieldForm({ ...fieldForm, normalization_rule: e.target.value })}
                className="w-full px-4 py-3 bg-slate-800 border border-slate-700 rounded-xl text-white focus:outline-none focus:ring-2 focus:ring-primary-500/50"
              >
                {NORMALIZATION_RULES.map(r => <option key={r.value} value={r.value}>{r.label}</option>)}
              </select>
            </div>
          </div>
          <div>
            <label className="block text-sm font-medium text-slate-300 mb-2">Description</label>
            <textarea
              value={fieldForm.description}
              onChange={(e) => setFieldForm({ ...fieldForm, description: e.target.value })}
              className="w-full px-4 py-3 bg-slate-800 border border-slate-700 rounded-xl text-white placeholder-slate-500 focus:outline-none focus:ring-2 focus:ring-primary-500/50"
              placeholder="Brief description or extraction hint"
              rows={2}
            />
          </div>
          <label className="flex items-center gap-3 cursor-pointer">
            <input
              type="checkbox"
              checked={fieldForm.is_required}
              onChange={(e) => setFieldForm({ ...fieldForm, is_required: e.target.checked })}
              className="w-5 h-5 rounded border-slate-600 bg-slate-800 text-primary-500 focus:ring-primary-500/50"
            />
            <span className="text-slate-300">Required field</span>
          </label>
          <div className="flex justify-end gap-3 pt-4">
            <Button variant="ghost" type="button" onClick={() => setShowFieldModal(false)}>Cancel</Button>
            <Button type="submit">{editingField ? 'Update Field' : 'Add Field'}</Button>
          </div>
        </form>
      </Modal>
    </div>
  );
}

export default TemplateEditor;
