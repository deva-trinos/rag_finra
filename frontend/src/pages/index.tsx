import { useState, ChangeEvent, FormEvent } from 'react';

interface ComplianceFinding {
  rule_id: string;
  rule_text: string;
  document_excerpt: string;
  suggestion: string;
  correction?: string;
}

interface DocumentAnalysisResult {
  document_id: string;
  filename: string;
  status: string;
  findings: ComplianceFinding[];
}

const Home: React.FC = () => {
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [loading, setLoading] = useState<boolean>(false);
  const [documentId, setDocumentId] = useState<string | null>(null);
  const [analysisResult, setAnalysisResult] = useState<DocumentAnalysisResult | null>(null);
  const [error, setError] = useState<string | null>(null);

  const handleFileChange = (event: ChangeEvent<HTMLInputElement>) => {
    if (event.target.files && event.target.files[0]) {
      setSelectedFile(event.target.files[0]);
    }
  };

  const handleFileUpload = async (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    if (!selectedFile) {
      setError("Please select a file to upload.");
      return;
    }

    setLoading(true);
    setError(null);
    setDocumentId(null);
    setAnalysisResult(null);

    const formData = new FormData();
    formData.append("file", selectedFile);

    try {
      const uploadResponse = await fetch(`${process.env.NEXT_PUBLIC_BACKEND_URL}/upload-document`, {
        method: "POST",
        body: formData,
      });

      if (!uploadResponse.ok) {
        throw new Error(`Upload failed: ${uploadResponse.statusText}`);
      }

      const uploadData = await uploadResponse.json();
      setDocumentId(uploadData.document_id);

      // Poll for analysis results (simplified for local demo)
      let resultFetched = false;
      let attempts = 0;
      const maxAttempts = 10;
      const pollInterval = 2000; // 2 seconds

      while (!resultFetched && attempts < maxAttempts) {
        await new Promise(resolve => setTimeout(resolve, pollInterval));
        const analysisResponse = await fetch(`${process.env.NEXT_PUBLIC_BACKEND_URL}/compliance-findings/${uploadData.document_id}`);
        
        if (analysisResponse.ok) {
          const analysisData: DocumentAnalysisResult = await analysisResponse.json();
          if (analysisData.status === "completed") {
            setAnalysisResult(analysisData);
            resultFetched = true;
          } else {
            console.log("Analysis still pending...");
          }
        } else if (analysisResponse.status === 404) {
          console.log("Document analysis not yet available. Retrying...");
        } else {
          throw new Error(`Analysis retrieval failed: ${analysisResponse.statusText}`);
        }
        attempts++;
      }

      if (!resultFetched) {
        setError("Analysis timed out or not completed.");
      }

    } catch (err: any) {
      setError(err.message || "An unknown error occurred during file upload or analysis.");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-gray-100 flex flex-col items-center justify-center p-4">
      <h1 className="text-4xl font-bold text-gray-800 mb-8">AI Compliance Platform</h1>
      
      <div className="bg-white p-8 rounded-lg shadow-md w-full max-w-lg">
        <h2 className="text-2xl font-semibold text-gray-700 mb-6">Upload Document</h2>
        <form onSubmit={handleFileUpload} className="space-y-4">
          <div>
            <label htmlFor="document-upload" className="block text-sm font-medium text-gray-700">Choose Document (PDF or DOCX)</label>
            <input
              type="file"
              id="document-upload"
              accept=".pdf,.docx"
              onChange={handleFileChange}
              className="mt-1 block w-full text-sm text-gray-500
                file:mr-4 file:py-2 file:px-4
                file:rounded-full file:border-0
                file:text-sm file:font-semibold
                file:bg-blue-50 file:text-blue-700
                hover:file:bg-blue-100"
            />
          </div>
          <button
            type="submit"
            className="w-full px-4 py-2 bg-blue-600 text-white font-semibold rounded-md shadow-sm hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-2"
            disabled={loading}
          >
            {loading ? "Uploading and Analyzing..." : "Upload and Analyze"}
          </button>
        </form>
        
        {loading && <p className="mt-4 text-center text-blue-600">Processing document, please wait...</p>}
        {error && <p className="mt-4 text-center text-red-600">Error: {error}</p>}
        {documentId && !loading && !error && (
          <p className="mt-4 text-center text-green-600">Document uploaded. Document ID: {documentId}</p>
        )}
      </div>

      {analysisResult && (
        <div className="bg-white p-8 rounded-lg shadow-md w-full max-w-3xl mt-8">
          <h2 className="text-2xl font-semibold text-gray-700 mb-6">Analysis Results for {analysisResult.filename}</h2>
          {analysisResult.findings.length > 0 ? (
            <div className="space-y-6">
              {analysisResult.findings.map((finding, index) => (
                <div key={index} className="border-b border-gray-200 pb-4 last:border-b-0">
                  <h3 className="text-xl font-medium text-gray-800">Rule: {finding.rule_id}</h3>
                  <p className="text-gray-600 mt-2"><strong>Rule Text:</strong> {finding.rule_text}</p>
                  <p className="text-gray-600 mt-2"><strong>Document Excerpt:</strong> <span className="italic">"{finding.document_excerpt}"</span></p>
                  <p className="text-yellow-700 mt-2"><strong>Suggestion:</strong> {finding.suggestion}</p>
                  {finding.correction && (
                    <p className="text-green-700 mt-2"><strong>Proposed Correction:</strong> {finding.correction}</p>
                  )}
                </div>
              ))}
            </div>
          ) : (
            <p className="text-gray-600">No compliance findings for this document.</p>
          )}
        </div>
      )}
    </div>
  );
};

export default Home;
