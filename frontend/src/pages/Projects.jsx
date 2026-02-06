import { useState, useEffect } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { FolderKanban, Plus, Trash2, Eye } from 'lucide-react';
import Button from '../components/Button.jsx';
import Card from '../components/Card.jsx';
import Modal from '../components/Modal.jsx';
import StatusBadge from '../components/StatusBadge.jsx';
import { projectsApi, templatesApi } from '../api/index.js';
import { formatDate } from '../utils/format.js';

function Projects() {
  const navigate = useNavigate();
  const [projects, setProjects] = useState([]);
  const [templates, setTemplates] = useState([]);
  const [loading, setLoading] = useState(true);
  const [showCreateModal, setShowCreateModal] = useState(false);
  const [formData, setFormData] = useState({ name: '', description: '', template_id: '' });

  const fetchData = async () => {
    try {
      setLoading(true);
      const [projectsRes, templatesRes] = await Promise.all([
        projectsApi.getAll(),
        templatesApi.getAll()
      ]);
      setProjects(projectsRes.data.projects || []);
      const tpls = templatesRes.data.templates || [];
      setTemplates(tpls);
      if (tpls.length > 0 && !formData.template_id) {
        setFormData(prev => ({ ...prev, template_id: tpls[0].id.toString() }));
      }
    } catch (err) {
      console.error('Failed to fetch data:', err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => { fetchData(); }, []);

  const handleCreate = async (e) => {
    e.preventDefault();
    try {
      const res = await projectsApi.create({
        name: formData.name,
        description: formData.description,
        template_id: parseInt(formData.template_id),
      });
      navigate(`/projects/${res.data.id}`);
    } catch (err) {
      alert(`Create failed: ${err.message}`);
    }
  };

  const handleDelete = async (id) => {
    if (!confirm('Are you sure you want to delete this project?')) return;
    try {
      await projectsApi.delete(id);
      setProjects(projects.filter(p => p.id !== id));
    } catch (err) {
      alert(`Delete failed: ${err.message}`);
    }
  };

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold text-white mb-2">Projects</h1>
          <p className="text-slate-400">Create and manage document extraction projects.</p>
        </div>
        <Button icon={Plus} onClick={() => setShowCreateModal(true)}>New Project</Button>
      </div>

      {loading ? (
        <div className="text-center py-12">
          <div className="animate-spin w-8 h-8 border-2 border-primary-500 border-t-transparent rounded-full mx-auto" />
        </div>
      ) : projects.length > 0 ? (
        <div className="glass rounded-2xl overflow-hidden">
          <table className="w-full">
            <thead>
              <tr className="border-b border-slate-700/50">
                <th className="text-left px-6 py-4 text-sm font-medium text-slate-400">Project</th>
                <th className="text-left px-6 py-4 text-sm font-medium text-slate-400">Documents</th>
                <th className="text-left px-6 py-4 text-sm font-medium text-slate-400">Created</th>
                <th className="text-left px-6 py-4 text-sm font-medium text-slate-400">Status</th>
                <th className="text-right px-6 py-4 text-sm font-medium text-slate-400">Actions</th>
              </tr>
            </thead>
            <tbody>
              {projects.map(project => (
                <tr key={project.id} className="border-b border-slate-700/30 hover:bg-slate-800/30">
                  <td className="px-6 py-4">
                    <Link to={`/projects/${project.id}`} className="font-medium text-white hover:text-primary-400">{project.name}</Link>
                    {project.description && <p className="text-sm text-slate-500 line-clamp-1">{project.description}</p>}
                  </td>
                  <td className="px-6 py-4 text-slate-300">{project.document_count}</td>
                  <td className="px-6 py-4 text-slate-400 text-sm">{formatDate(project.created_at)}</td>
                  <td className="px-6 py-4"><StatusBadge status={project.status} /></td>
                  <td className="px-6 py-4 text-right">
                    <div className="flex items-center justify-end gap-2">
                      <Link to={`/projects/${project.id}`} className="p-2 text-slate-400 hover:text-white hover:bg-slate-700 rounded-lg transition-colors">
                        <Eye className="w-4 h-4" />
                      </Link>
                      <button onClick={() => handleDelete(project.id)} className="p-2 text-slate-400 hover:text-red-400 hover:bg-red-500/10 rounded-lg transition-colors">
                        <Trash2 className="w-4 h-4" />
                      </button>
                    </div>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      ) : (
        <Card className="text-center py-12">
          <FolderKanban className="w-16 h-16 text-slate-600 mx-auto mb-4" />
          <h3 className="text-xl font-medium text-white mb-2">No projects yet</h3>
          <p className="text-slate-400 mb-6">Create your first project to start extracting data.</p>
          <Button icon={Plus} onClick={() => setShowCreateModal(true)}>New Project</Button>
        </Card>
      )}

      <Modal isOpen={showCreateModal} onClose={() => setShowCreateModal(false)} title="Create Project" size="md">
        <form onSubmit={handleCreate} className="space-y-4">
          <div>
            <label className="block text-sm font-medium text-slate-300 mb-2">Project Name</label>
            <input
              type="text"
              value={formData.name}
              onChange={(e) => setFormData({ ...formData, name: e.target.value })}
              className="w-full px-4 py-3 bg-slate-800 border border-slate-700 rounded-xl text-white placeholder-slate-500 focus:outline-none focus:ring-2 focus:ring-primary-500/50"
              placeholder="Enter project name"
              required
            />
          </div>
          <div>
            <label className="block text-sm font-medium text-slate-300 mb-2">Template</label>
            <select
              value={formData.template_id}
              onChange={(e) => setFormData({ ...formData, template_id: e.target.value })}
              className="w-full px-4 py-3 bg-slate-800 border border-slate-700 rounded-xl text-white focus:outline-none focus:ring-2 focus:ring-primary-500/50"
              required
            >
              {templates.map(t => <option key={t.id} value={t.id}>{t.name}</option>)}
            </select>
          </div>
          <div>
            <label className="block text-sm font-medium text-slate-300 mb-2">Description</label>
            <textarea
              value={formData.description}
              onChange={(e) => setFormData({ ...formData, description: e.target.value })}
              className="w-full px-4 py-3 bg-slate-800 border border-slate-700 rounded-xl text-white placeholder-slate-500 focus:outline-none focus:ring-2 focus:ring-primary-500/50"
              placeholder="Optional project description"
              rows={3}
            />
          </div>
          <div className="flex justify-end gap-3 pt-4">
            <Button variant="ghost" type="button" onClick={() => setShowCreateModal(false)}>Cancel</Button>
            <Button type="submit">Create Project</Button>
          </div>
        </form>
      </Modal>
    </div>
  );
}

export default Projects;
