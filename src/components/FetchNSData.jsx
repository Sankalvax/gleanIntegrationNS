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
        console.log('Fetch Data button clicked!');
        setIsLoading(true);
        setApiMessage('');
        setApiError('');

        try {
            const response = await fetch('http://localhost:5001/api/fetch_ns_bulk_data', { // Ensure Flask is on port 5001
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json', // Good practice, even if no body is sent for this specific call
                },
                // body: JSON.stringify({ someData: 'neededForIndexing' }) // Uncomment if you need to send data
            });

            const result = await response.json();

            console.log("API Response:", result);

            if (response.ok) {
                console.log("API Success:", result);
                setApiMessage('Fetching NetSuite Data process completed successfully!');

                navigate('/bulk-doc-index'); // 3. Navigate to the new page
         
                // alert(`✅ Users indexing process status: ${result.message}`);
            } else {
                console.error("API Error:", result);
                setApiError(result.error || `Failed to fetch Netsuite Data: ${response.statusText}`);
                // alert(`❌ Failed to start user indexing: ${result.error || 'Unknown error'}`);
            }
        } catch (error) {
            console.error('Error calling index_users API:', error);
            setApiError('❌ Network error or an issue calling the API.');
            // alert('❌ Error calling index_users API. Check console.');
        } finally {
            setIsLoading(false);
        }
    };



    const objects = [
        "Customer",
        "Vendor",
        "Item",
        "Invoice",
        "Bill",
        "Sales Order",
        "Purchase Order",
        "Estimate",
        "Opportunity",
    ];

    return (
        <div className="flex flex-col justify-center items-center min-h-screen bg-gray-50 px-6 py-12">
            <div className="w-full max-w-3xl bg-white rounded-2xl shadow-lg border overflow-hidden p-8">
                <div className="flex justify-start items-center mb-6">
                    <img src={gruveLogo} alt="Gruve Logo" className="max-h-10 object-contain" />
                    <h1 className="text-2xl font-semibold text-gray-800 ml-4">Step 3: Fetch Data for Indexing</h1>
                </div>

                <div className="mb-6 text-left">
                    <h3 className="text-lg font-semibold text-gray-700 mb-2">Objects to fetch from Netsuite:</h3>
                    <ul className="list-disc list-inside text-gray-600 space-y-1">
                        {objects.map((object, index) => (
                            <li key={index}>{object}</li>
                        ))}
                    </ul>
                </div>

                <div className="text-center mt-8">
                    <button
                        onClick={handleIndexUsersClick}
                        disabled={isLoading}
                        className="px-8 py-4 bg-blue-600 text-white font-semibold rounded-md hover:bg-blue-700 transition text-lg shadow-md focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-opacity-50 disabled:opacity-50 disabled:cursor-not-allowed"
                    >
                        {isLoading ? 'Fetching...' : 'Fetch Data'}
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
