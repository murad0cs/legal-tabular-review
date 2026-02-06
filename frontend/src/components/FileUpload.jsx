import { useState, useCallback } from 'react';
import { Upload, File, X, CheckCircle, AlertCircle } from 'lucide-react';
import clsx from 'clsx';
import Button from './Button.jsx';
import { formatFileSize } from '../utils/format.js';

function FileUpload({ onUpload, accept = '.pdf,.docx', multiple = true }) {
  const [files, setFiles] = useState([]);
  const [dragActive, setDragActive] = useState(false);
  const [uploading, setUploading] = useState(false);
  const [results, setResults] = useState(null);

  const handleDrag = useCallback((e) => {
    e.preventDefault();
    e.stopPropagation();
    setDragActive(e.type === 'dragenter' || e.type === 'dragover');
  }, []);

  const handleDrop = useCallback((e) => {
    e.preventDefault();
    e.stopPropagation();
    setDragActive(false);
    setFiles(prev => [...prev, ...Array.from(e.dataTransfer.files)]);
  }, []);

  const handleFileInput = (e) => setFiles(prev => [...prev, ...Array.from(e.target.files)]);
  const removeFile = (index) => setFiles(prev => prev.filter((_, i) => i !== index));

  const handleUpload = async () => {
    if (files.length === 0) return;
    setUploading(true);
    setResults(null);
    try {
      const result = await onUpload(files);
      setResults(result);
      if (result.uploaded?.length > 0) setFiles([]);
    } catch (error) {
      setResults({ errors: [{ error: error.message }] });
    } finally {
      setUploading(false);
    }
  };

  return (
    <div className="space-y-4">
      <div
        className={clsx(
          'relative border-2 border-dashed rounded-xl p-8 text-center transition-colors',
          dragActive ? 'border-primary-500 bg-primary-500/10' : 'border-slate-600 hover:border-slate-500'
        )}
        onDragEnter={handleDrag}
        onDragLeave={handleDrag}
        onDragOver={handleDrag}
        onDrop={handleDrop}
      >
        <input type="file" accept={accept} multiple={multiple} onChange={handleFileInput} className="absolute inset-0 w-full h-full opacity-0 cursor-pointer" />
        <Upload className="w-12 h-12 mx-auto text-slate-400 mb-4" />
        <p className="text-slate-300 font-medium mb-2">Drag and drop files here, or click to browse</p>
        <p className="text-sm text-slate-500">Supports PDF and DOCX files (max 50MB each)</p>
      </div>

      {files.length > 0 && (
        <div className="space-y-2">
          <h4 className="text-sm font-medium text-slate-300">Selected Files ({files.length})</h4>
          <ul className="space-y-2">
            {files.map((file, index) => (
              <li key={index} className="flex items-center justify-between p-3 bg-slate-800/50 rounded-lg">
                <div className="flex items-center gap-3">
                  <File className="w-5 h-5 text-slate-400" />
                  <div>
                    <p className="text-sm text-slate-200">{file.name}</p>
                    <p className="text-xs text-slate-500">{formatFileSize(file.size)}</p>
                  </div>
                </div>
                <button onClick={() => removeFile(index)} className="p-1 text-slate-400 hover:text-red-400 transition-colors">
                  <X className="w-4 h-4" />
                </button>
              </li>
            ))}
          </ul>
          <Button onClick={handleUpload} loading={uploading} className="w-full">
            Upload {files.length} {files.length === 1 ? 'File' : 'Files'}
          </Button>
        </div>
      )}

      {results && (
        <div className="space-y-2">
          {results.uploaded?.map((doc, i) => (
            <div key={i} className="flex items-center gap-2 p-3 bg-emerald-500/10 rounded-lg text-emerald-400">
              <CheckCircle className="w-5 h-5" />
              <span className="text-sm">{doc.original_filename} uploaded successfully</span>
            </div>
          ))}
          {results.errors?.map((err, i) => (
            <div key={i} className="flex items-center gap-2 p-3 bg-red-500/10 rounded-lg text-red-400">
              <AlertCircle className="w-5 h-5" />
              <span className="text-sm">{err.filename || 'Error'}: {err.error}</span>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}

export default FileUpload;
