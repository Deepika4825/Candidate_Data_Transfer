import { useState, useRef } from 'react';

const CheckCircleIcon = () => (
  <svg className="w-5 h-5 text-emerald-500 flex-shrink-0" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
    <path strokeLinecap="round" strokeLinejoin="round" d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
  </svg>
);

const UploadIcon = () => (
  <svg className="w-8 h-8 text-blue-400 mb-2" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1.5}>
    <path strokeLinecap="round" strokeLinejoin="round" d="M3 16.5v2.25A2.25 2.25 0 005.25 21h13.5A2.25 2.25 0 0021 18.75V16.5m-13.5-9L12 3m0 0l4.5 4.5M12 3v13.5" />
  </svg>
);

export default function FileUploadZone({ accept, file, onFileChange }) {
  const [dragging, setDragging] = useState(false);
  const inputRef = useRef(null);

  const handleFile = (f) => { if (f) onFileChange(f); };

  const onDrop = (e) => {
    e.preventDefault();
    setDragging(false);
    handleFile(e.dataTransfer.files[0]);
  };

  const onDragOver = (e) => { e.preventDefault(); setDragging(true); };
  const onDragLeave = () => setDragging(false);
  const onInputChange = (e) => handleFile(e.target.files[0]);

  return (
    <div
      onDrop={onDrop}
      onDragOver={onDragOver}
      onDragLeave={onDragLeave}
      onClick={() => !file && inputRef.current.click()}
      className={`
        relative flex flex-col items-center justify-center gap-1
        rounded-xl border-2 border-dashed px-4 py-6 cursor-pointer
        transition-all duration-200
        ${dragging
          ? 'border-blue-500 bg-blue-50'
          : file
            ? 'border-emerald-300 bg-emerald-50 cursor-default'
            : 'border-gray-300 bg-white hover:border-blue-400 hover:bg-blue-50'
        }
      `}
    >
      {file ? (
        <div className="flex items-center gap-2 w-full justify-center">
          <CheckCircleIcon />
          <span className="text-sm text-emerald-700 font-medium truncate max-w-xs">{file.name}</span>
          <button
            onClick={(e) => { e.stopPropagation(); onFileChange(null); }}
            className="ml-2 text-gray-400 hover:text-red-500 transition-colors text-xs"
            title="Remove file"
          >
            ✕
          </button>
        </div>
      ) : (
        <>
          <UploadIcon />
          <p className="text-sm text-gray-500 text-center">
            Drag & drop here, or{' '}
            <span className="text-blue-600 font-semibold hover:text-blue-700">browse</span>
          </p>
          <p className="text-xs text-gray-400">{accept}</p>
        </>
      )}
      <input
        ref={inputRef}
        type="file"
        accept={accept}
        onChange={onInputChange}
        className="hidden"
      />
    </div>
  );
}
