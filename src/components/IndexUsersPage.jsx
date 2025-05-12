// src/components/IndexUsersPage.jsx
import React, { useState } from 'react'; // CORRECTED: Added useState to the import
import gruveLogo from '../assets/gruve.png'; // Assuming your gruve logo is in src/assets/
import { useNavigate } from 'react-router-dom'; // 1. Import useNavigate

const IndexUsersPage = () => {

  const navigate = useNavigate(); // 2. Initialize the navigate function
  
  const [isLoading, setIsLoading] = useState(false);
  const [apiMessage, setApiMessage] = useState('');
  const [apiError, setApiError] = useState('');

  const handleIndexUsersClick = async () => {
    console.log('Index Users button clicked!');
    setIsLoading(true);
    setApiMessage('');
    setApiError('');

    try {
      const response = await fetch('http://localhost:5001/api/index_users', { // Ensure Flask is on port 5001
        method: 'POST',
        headers: {
          'Content-Type': 'application/json', // Good practice, even if no body is sent for this specific call
        },
        // body: JSON.stringify({ someData: 'neededForIndexing' }) // Uncomment if you need to send data
      });

      const result = await response.json();

      if (response.ok) {
        console.log("API Success:", result);
        setApiMessage(result.message || 'User indexing process completed successfully!');
        if (result.users_indexed !== undefined) {
            setApiMessage(prev => `${prev} Users indexed: ${result.users_indexed}.`);
        }
        navigate('/fetch-data'); // 3. Navigate to the new page

        // alert(`✅ Users indexing process status: ${result.message}`);
      } else {
        console.error("API Error:", result);
        setApiError(result.error || `Failed to start user indexing: ${response.statusText}`);
        // alert(`❌ Failed to start user indexing: ${result.error || 'Unknown error'}`);
      }
    } catch (error) {
      console.error('Error calling index_users API:', error);
      setApiError('❌ Network error or an issue calling the index_users API. Check console.');
      // alert('❌ Error calling index_users API. Check console.');
    } finally {
      setIsLoading(false);
    }
  };

  const whyIndexText = `
    In Glean, indexing users is a crucial step before using them in permissions.
    Users need to be indexed before they can be referenced in group memberships,
    document permissions, etc. This process essentially tells Glean about the
    users who might have access to a particular data source.
  `;

  const benefits = [
    "Accurate Permissions: Ensures users have the correct level of access to data.",
    "Improved Search: Indexing helps Glean identify relevant information based on user identity and roles.",
    "Integration with HRIS/Identity Systems: Glean connects to various systems to automatically manage user data, simplifying the indexing process."
  ];

  return (
    <div className="flex flex-col justify-center items-center min-h-screen bg-gray-50 px-6 py-12">
      <div className="w-full max-w-3xl bg-white rounded-2xl shadow-lg border overflow-hidden p-8">
        <div className="flex justify-start items-center mb-6">
          <img src={gruveLogo} alt="Gruve Logo" className="max-h-10 object-contain" />
          <h1 className="text-2xl font-semibold text-gray-800 ml-4">Step 2: Index Users in Glean</h1>
        </div>

        <div className="mb-6 text-left">
          <h2 className="text-xl font-semibold text-gray-700 mb-3">Why Index Users?</h2>
          <p className="text-gray-600 whitespace-pre-line mb-4">
            {whyIndexText.trim()}
          </p>
          <h3 className="text-lg font-semibold text-gray-700 mb-2">Key Benefits:</h3>
          <ul className="list-disc list-inside text-gray-600 space-y-1">
            {benefits.map((benefit, index) => (
              <li key={index}>{benefit}</li>
            ))}
          </ul>
        </div>

        <div className="text-center mt-8">
          <button
            onClick={handleIndexUsersClick}
            disabled={isLoading}
            className="px-8 py-4 bg-blue-600 text-white font-semibold rounded-md hover:bg-blue-700 transition text-lg shadow-md focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-opacity-50 disabled:opacity-50 disabled:cursor-not-allowed"
          >
            {isLoading ? 'Indexing...' : 'Index Users'}
          </button>
        </div>

        {/* Display API messages or errors */}
        {apiMessage && (
          <div className="mt-6 p-4 text-center bg-green-100 text-green-700 rounded-md border border-green-300">
            {apiMessage}
          </div>
        )}
        {apiError && (
          <div className="mt-6 p-4 text-center bg-red-100 text-red-700 rounded-md border border-red-300">
            {apiError}
          </div>
        )}

      </div>
    </div>
  );
};

export default IndexUsersPage;
