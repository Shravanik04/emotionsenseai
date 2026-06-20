import { useState } from 'react';

interface UploadZoneProps {
  onFileUpload: (file: File) => void;
}

export const UploadZone = ({ onFileUpload }: UploadZoneProps) => {
  const [dragging, setDragging] = useState(false);

  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault();
    setDragging(false);
    const file = e.dataTransfer.files[0];
    if (file && (file.type === 'text/csv' || file.name.endsWith('.csv'))) {
      onFileUpload(file);
    } else {
      alert('Please upload a CSV file.');
    }
  };

  return (
    <div 
      onDragOver={(e) => { e.preventDefault(); setDragging(true); }}
      onDragLeave={() => setDragging(false)}
      onDrop={handleDrop}
      className={`border-2 border-dashed rounded-xl p-10 text-center cursor-pointer transition-colors
      ${dragging ? 'border-blue-500 bg-blue-50' : 'border-gray-300 hover:border-gray-400'}`}
      onClick={() => document.getElementById('file-input')?.click()}
    >
      <input 
        id="file-input" 
        type="file" 
        accept=".csv" 
        className="hidden" 
        onChange={(e) => e.target.files && onFileUpload(e.target.files[0])} 
      />
      <div className="text-gray-500">
        <p className="text-lg font-medium">Drag & drop CSV file here, or click to select</p>
        <p className="text-sm mt-2">Must contain a text column (e.g., review, text, comment)</p>
      </div>
    </div>
  );
};
