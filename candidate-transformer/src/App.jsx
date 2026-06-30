import { useState } from 'react';
import SelectionPage from './components/SelectionPage';
import ResultsPage from './components/ResultsPage';

export default function App() {
  const [page, setPage] = useState('selection'); // 'selection' | 'results'
  const [selectedSources, setSelectedSources] = useState([]);

  const handleStart = (sources) => {
    setSelectedSources(sources);
    setPage('results');
  };

  const handleBack = () => {
    setPage('selection');
  };

  return (
    <>
      {page === 'selection' && (
        <SelectionPage onStart={handleStart} />
      )}
      {page === 'results' && (
        <ResultsPage sources={selectedSources} onBack={handleBack} />
      )}
    </>
  );
}
