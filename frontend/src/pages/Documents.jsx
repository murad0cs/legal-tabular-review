import { useState, useEffect } from 'react';
import { FileText, Upload, Search, Trash2, Eye } from 'lucide-react';
import Button from '../components/Button.jsx';
import Card from '../components/Card.jsx';
import Modal from '../components/Modal.jsx';
import FileUpload from '../components/FileUpload.jsx';
import StatusBadge from '../components/StatusBadge.jsx';
import { documentsApi } from '../api/index.js';
import { formatDate, truncate } from '../utils/format.js';

function Documents() {
  const [documents, setDocuments] = useState([]);
  const [loading, setLoading] = useState(true);
  const [searchQuery, setSearchQuery] = useState('');
  const [showUploadModal, setShowUploadModal] = useState(false);
  const [selectedDocument, setSelectedDocument] = useState(null);
  const [documentContent, setDocumentContent] = useState('');

  const fetchDocuments = async () => {
    try {
      setLoading(true);
      const res = await documentsApi.getAll();
      setDocuments(res.data.documents || []);
    } catch (err) {
      console.error('Failed to fetch documents:', err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => { fetchDocuments(); }, []);

  const handleUpload = async (files) => {
    const res = await documentsApi.upload(files);
    if (res.data.uploaded?.length > 0) fetchDocuments();
    return res.data;
  };

  const handleDelete = async (id) => {
    if (!confirm('Are you sure you want to delete this document?')) return;
    try {
      await documentsApi.delete(id);
      setDocuments(docs => docs.filter(d => d.id !== id));
    } catch (err) {
      alert(`Delete failed: ${err.message}`);
    }
  };

  const handleView = async (doc) => {
    setSelectedDocument(doc);
    try {
      const res = await documentsApi.getContent(doc.id);
      setDocumentContent(res.data.content || 'No content extracted');
    } catch (err) {
      setDocumentContent(`Error loading content: ${err.message}`);
    }
  };

  const filteredDocuments = documents.filter(d =>
    d.original_filename.toLowerCase().includes(searchQuery.toLowerCase())
  );

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold text-white mb-2">Documents</h1>
          <p className="text-slate-400">Manage your uploaded documents for extraction.</p>
        </div>
        <Button icon={Upload} onClick={() => setShowUploadModal(true)}>Upload Documents</Button>
      </div>

      <div className="relative">
        <Search className="absolute left-4 top-1/2 -translate-y-1/2 w-5 h-5 text-slate-400" />
        <input
          type="text"
          placeholder="Search documents..."
          value={searchQuery}
          onChange={(e) => setSearchQuery(e.target.value)}
          className="w-full pl-12 pr-4 py-3 bg-slate-800/50 border border-slate-700 rounded-xl text-white placeholder-slate-500 focus:outline-none focus:ring-2 focus:ring-primary-500/50"
        />
      </div>

      {loading ? (
        <div className="text-center py-12">
          <div className="animate-spin w-8 h-8 border-2 border-primary-500 border-t-transparent rounded-full mx-auto" />
        </div>
      ) : filteredDocuments.length > 0 ? (
        <div className="glass rounded-2xl overflow-hidden">
          <table className="w-full">
            <thead>
              <tr className="border-b border-slate-700/50">
                <th className="text-left px-6 py-4 text-sm font-medium text-slate-400">Name</th>
                <th className="text-left px-6 py-4 text-sm font-medium text-slate-400">Type</th>
                <th className="text-left px-6 py-4 text-sm font-medium text-slate-400">Pages</th>
                <th className="text-left px-6 py-4 text-sm font-medium text-slate-400">Uploaded</th>
                <th className="text-left px-6 py-4 text-sm font-medium text-slate-400">Status</th>
                <th className="text-right px-6 py-4 text-sm font-medium text-slate-400">Actions</th>
              </tr>
            </thead>
            <tbody>
              {filteredDocuments.map(doc => (
                <tr key={doc.id} className="border-b border-slate-700/30 hover:bg-slate-800/30">
                  <td className="px-6 py-4">
                    <div className="flex items-center gap-3">
                      <FileText className="w-5 h-5 text-slate-400" />
                      <span className="text-white font-medium">{truncate(doc.original_filename, 40)}</span>
                    </div>
                  </td>
                  <td className="px-6 py-4 text-slate-300 uppercase text-sm">{doc.file_type}</td>
                  <td className="px-6 py-4 text-slate-300">{doc.page_count}</td>
                  <td className="px-6 py-4 text-slate-400 text-sm">{formatDate(doc.upload_date)}</td>
                  <td className="px-6 py-4"><StatusBadge status={doc.status} /></td>
                  <td className="px-6 py-4 text-right">
                    <div className="flex items-center justify-end gap-2">
                      <button onClick={() => handleView(doc)} className="p-2 text-slate-400 hover:text-white hover:bg-slate-700 rounded-lg transition-colors">
                        <Eye className="w-4 h-4" />
                      </button>
                      <button onClick={() => handleDelete(doc.id)} className="p-2 text-slate-400 hover:text-red-400 hover:bg-red-500/10 rounded-lg transition-colors">
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
          <FileText className="w-16 h-16 text-slate-600 mx-auto mb-4" />
          <h3 className="text-xl font-medium text-white mb-2">No documents yet</h3>
          <p className="text-slate-400 mb-6">Upload your first document to get started.</p>
          <Button icon={Upload} onClick={() => setShowUploadModal(true)}>Upload Documents</Button>
        </Card>
      )}

      <Modal isOpen={showUploadModal} onClose={() => setShowUploadModal(false)} title="Upload Documents" size="md">
        <FileUpload onUpload={handleUpload} />
      </Modal>

      <Modal isOpen={!!selectedDocument} onClose={() => { setSelectedDocument(null); setDocumentContent(''); }} title={selectedDocument?.original_filename || 'Document'} size="lg">
        <pre className="whitespace-pre-wrap text-sm text-slate-300 bg-slate-900 rounded-xl p-4 max-h-96 overflow-auto">{documentContent}</pre>
      </Modal>
    </div>
  );
}

export default Documents;
