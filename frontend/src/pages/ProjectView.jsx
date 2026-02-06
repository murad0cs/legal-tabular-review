import { useState, useEffect } from 'react';
import { useParams, useNavigate, Link } from 'react-router-dom';
import { ArrowLeft, Plus, Play, Table2, FileText, Trash2, Download } from 'lucide-react';
import Button from '../components/Button.jsx';
import Card from '../components/Card.jsx';
import Modal from '../components/Modal.jsx';
import StatusBadge from '../components/StatusBadge.jsx';
import { projectsApi, documentsApi } from '../api/index.js';
import { formatDate, downloadBlob } from '../utils/format.js';

function ProjectView() {
  const { id } = useParams();
  const navigate = useNavigate();
  const [project, setProject] = useState(null);
  const [loading, setLoading] = useState(true);
  const [extracting, setExtracting] = useState(false);
  const [showAddDocuments, setShowAddDocuments] = useState(false);
  const [availableDocs, setAvailableDocs] = useState([]);
  const [selectedDocs, setSelectedDocs] = useState([]);

  const fetchProject = async () => {
    try {
      setLoading(true);
      const res = await projectsApi.getById(id);
      setProject(res.data);
    } catch (err) {
      console.error('Failed to fetch project:', err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => { if (id) fetchProject(); }, [id]);

  const fetchAvailableDocs = async () => {
    try {
      const res = await documentsApi.getAll();
      const projectDocIds = new Set(project?.documents?.map(d => d.id) || []);
      setAvailableDocs((res.data.documents || []).filter(d => !projectDocIds.has(d.id)));
    } catch (err) {
      console.error('Failed to fetch documents:', err);
    }
  };

  const handleAddDocuments = async () => {
    if (selectedDocs.length === 0) return;
    try {
      await projectsApi.addDocuments(id, selectedDocs);
      fetchProject();
      setShowAddDocuments(false);
      setSelectedDocs([]);
    } catch (err) {
      alert(`Failed to add documents: ${err.message}`);
    }
  };

  const handleRemoveDocument = async (docId) => {
    if (!confirm('Remove this document from the project?')) return;
    try {
      await projectsApi.removeDocument(id, docId);
      fetchProject();
    } catch (err) {
      alert(`Failed to remove document: ${err.message}`);
    }
  };

  const handleExtract = async () => {
    if (!project.documents?.length) {
      alert('Add documents before extracting');
      return;
    }
    setExtracting(true);
    try {
      await projectsApi.extract(id);
      navigate(`/projects/${id}/review`);
    } catch (err) {
      alert(`Extraction failed: ${err.message}`);
    } finally {
      setExtracting(false);
    }
  };

  const handleExport = async (format) => {
    try {
      const res = format === 'csv' ? await projectsApi.exportCsv(id) : await projectsApi.exportExcel(id);
      const ext = format === 'csv' ? 'csv' : 'xlsx';
      downloadBlob(res.data, `${project.name.replace(/\s+/g, '_')}.${ext}`);
    } catch (err) {
      alert(`Export failed: ${err.message}`);
    }
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="animate-spin w-8 h-8 border-2 border-primary-500 border-t-transparent rounded-full" />
      </div>
    );
  }

  if (!project) {
    return <Card className="text-center py-12 text-slate-400">Project not found</Card>;
  }

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-4">
          <button onClick={() => navigate('/projects')} className="p-2 text-slate-400 hover:text-white hover:bg-slate-700 rounded-lg transition-colors">
            <ArrowLeft className="w-5 h-5" />
          </button>
          <div>
            <div className="flex items-center gap-3">
              <h1 className="text-3xl font-bold text-white">{project.name}</h1>
              <StatusBadge status={project.status} />
            </div>
            <p className="text-slate-400">{project.template?.name}</p>
          </div>
        </div>
        <div className="flex gap-3">
          {(project.status === 'needs_review' || project.status === 'completed') && (
            <>
              <Button variant="secondary" icon={Table2} onClick={() => navigate(`/projects/${id}/review`)}>Review Table</Button>
              <Button variant="ghost" icon={Download} onClick={() => handleExport('excel')}>Export</Button>
            </>
          )}
          <Button icon={Play} onClick={handleExtract} loading={extracting} disabled={!project.documents?.length}>
            Extract Fields
          </Button>
        </div>
      </div>

      <div className="grid grid-cols-3 gap-6">
        <Card>
          <div className="text-sm text-slate-400 mb-1">Documents</div>
          <div className="text-3xl font-bold text-white">{project.document_count}</div>
        </Card>
        <Card>
          <div className="text-sm text-slate-400 mb-1">Fields</div>
          <div className="text-3xl font-bold text-white">{project.template?.fields?.length || 0}</div>
        </Card>
        <Card>
          <div className="text-sm text-slate-400 mb-1">Created</div>
          <div className="text-xl font-semibold text-white">{formatDate(project.created_at)}</div>
        </Card>
      </div>

      <Card>
        <div className="flex items-center justify-between mb-4">
          <h2 className="text-xl font-semibold text-white">Documents</h2>
          <Button variant="secondary" size="sm" icon={Plus} onClick={() => { fetchAvailableDocs(); setShowAddDocuments(true); }}>
            Add Documents
          </Button>
        </div>

        {project.documents?.length > 0 ? (
          <div className="space-y-2">
            {project.documents.map(doc => (
              <div key={doc.id} className="flex items-center justify-between p-4 bg-slate-800/50 rounded-xl group">
                <div className="flex items-center gap-3">
                  <FileText className="w-5 h-5 text-slate-400" />
                  <div>
                    <p className="font-medium text-white">{doc.original_filename}</p>
                    <p className="text-sm text-slate-500">{doc.page_count} pages • {doc.file_type.toUpperCase()}</p>
                  </div>
                </div>
                <div className="flex items-center gap-2">
                  <StatusBadge status={doc.status} />
                  <button onClick={() => handleRemoveDocument(doc.id)} className="p-2 text-slate-400 hover:text-red-400 hover:bg-red-500/10 rounded-lg opacity-0 group-hover:opacity-100 transition-all">
                    <Trash2 className="w-4 h-4" />
                  </button>
                </div>
              </div>
            ))}
          </div>
        ) : (
          <div className="text-center py-8 text-slate-400">No documents added. Click "Add Documents" to get started.</div>
        )}
      </Card>

      <Modal isOpen={showAddDocuments} onClose={() => setShowAddDocuments(false)} title="Add Documents" size="md">
        {availableDocs.length > 0 ? (
          <div className="space-y-4">
            <div className="space-y-2 max-h-80 overflow-auto">
              {availableDocs.map(doc => (
                <label key={doc.id} className="flex items-center gap-3 p-3 bg-slate-800/50 rounded-lg cursor-pointer hover:bg-slate-800">
                  <input
                    type="checkbox"
                    checked={selectedDocs.includes(doc.id)}
                    onChange={(e) => {
                      if (e.target.checked) {
                        setSelectedDocs([...selectedDocs, doc.id]);
                      } else {
                        setSelectedDocs(selectedDocs.filter(id => id !== doc.id));
                      }
                    }}
                    className="w-5 h-5 rounded border-slate-600 bg-slate-800 text-primary-500 focus:ring-primary-500/50"
                  />
                  <FileText className="w-5 h-5 text-slate-400" />
                  <div className="flex-1">
                    <p className="text-white">{doc.original_filename}</p>
                    <p className="text-sm text-slate-500">{doc.page_count} pages</p>
                  </div>
                </label>
              ))}
            </div>
            <div className="flex justify-end gap-3">
              <Button variant="ghost" onClick={() => setShowAddDocuments(false)}>Cancel</Button>
              <Button onClick={handleAddDocuments} disabled={selectedDocs.length === 0}>
                Add {selectedDocs.length} Document{selectedDocs.length !== 1 ? 's' : ''}
              </Button>
            </div>
          </div>
        ) : (
          <div className="text-center py-8">
            <FileText className="w-12 h-12 text-slate-600 mx-auto mb-3" />
            <p className="text-slate-400 mb-4">No documents available to add.</p>
            <Link to="/documents" className="text-primary-400 hover:text-primary-300">Upload documents first</Link>
          </div>
        )}
      </Modal>
    </div>
  );
}

export default ProjectView;
