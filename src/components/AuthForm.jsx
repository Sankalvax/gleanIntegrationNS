import React, { useState } from 'react';
import gleanLogo from '../assets/glean.png';
import netsuiteLogo from '../assets/netsuite.png';

const AuthForm = ({ onComplete }) => {
    const [gleanToken, setGleanToken] = useState({
        gleanAccount: '',
        apiToken: ''
    });

    const [netsuiteCreds, setNetsuiteCreds] = useState({
        accountId: '',
        consumerKey: '',
        consumerSecret: '',
        token: '',
        tokenSecret: ''
    });

    const [errors, setErrors] = useState({});

    const validateForm = () => {
        const newErrors = {};
        let isValid = true;

        if (!gleanToken.gleanAccount.trim()) {
            newErrors.gleanAccount = 'Glean Account Name is required';
            isValid = false;
        }
        if (!gleanToken.apiToken.trim()) {
            newErrors.apiToken = 'Glean API Token is required';
            isValid = false;
        }

        Object.entries(netsuiteCreds).forEach(([key, value]) => {
            if (!value.trim()) {
                newErrors[key] = `${key.replace(/([A-Z])/g, ' $1')} is required`;
                isValid = false;
            }
        });

        setErrors(newErrors);
        return isValid;
    };

    const handleSubmit = async (e) => {
        e.preventDefault();

        if (!validateForm()) return;

        const payload = {
            gleanAccount: gleanToken.gleanAccount,
            gleanToken: gleanToken.apiToken,
            ...netsuiteCreds,
        };

        try {
            const response = await fetch('http://localhost:5001/api/auth', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify(payload),
            });

            const data = await response.json();
            if (response.ok) {
                alert('✅ Auth credentials saved!');
                onComplete();
            } else {
                alert(`❌ Failed: ${data.error}`);
            }
        } catch (err) {
            console.error('Submit error:', err);
            alert('❌ Submission failed. Check console for details.');
        }
    };

    return (
        <form onSubmit={handleSubmit} className="flex justify-center items-center min-h-screen bg-gray-50 px-6 py-12">
            <div className="w-full max-w-5xl bg-white rounded-2xl shadow-lg border overflow-hidden">
                <div className="grid grid-cols-1 md:grid-cols-2">
                    {/* Glean Section */}
                    <div className="p-8 flex flex-col items-start">
                        <img src={gleanLogo} alt="Glean Logo" className="max-h-12 object-contain mb-6" />
                        <h2 className="text-xl font-semibold text-gray-800 mb-4">Glean Authentication</h2>

                        <label className="text-sm font-medium text-gray-700 mb-1">Glean Account Name</label>
                        <input
                            type="text"
                            name="gleanAccount"
                            className={`w-full p-3 border ${errors.gleanAccount ? 'border-red-500' : 'border-gray-300'} rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 mb-2`}
                            placeholder="e.g. mycompany (from https://mycompany.glean.com)"
                            value={gleanToken.gleanAccount}
                            onChange={(e) => setGleanToken({ ...gleanToken, gleanAccount: e.target.value })}
                        />
                        {errors.gleanAccount && <p className="text-red-500 text-sm mb-2">{errors.gleanAccount}</p>}

                        <label className="text-sm font-medium text-gray-700 mb-1">Glean API Token</label>
                        <input
                            type="text"
                            name="apiToken"
                            className={`w-full p-3 border ${errors.apiToken ? 'border-red-500' : 'border-gray-300'} rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500`}
                            placeholder="Enter Glean API Token"
                            value={gleanToken.apiToken}
                            onChange={(e) => setGleanToken({ ...gleanToken, apiToken: e.target.value })}
                        />
                        {errors.apiToken && <p className="text-red-500 text-sm">{errors.apiToken}</p>}
                    </div>

                    {/* NetSuite Section */}
                    <div className="p-8 flex flex-col items-start">
                        <div className="w-full flex justify-end mb-6">
                            <img src={netsuiteLogo} alt="NetSuite Logo" className="max-h-12 object-contain" />
                        </div>
                        <h2 className="text-xl font-semibold text-gray-800 mb-4">NetSuite Authentication</h2>

                        {['accountId', 'consumerKey', 'consumerSecret', 'token', 'tokenSecret'].map((field) => (
                            <div key={field} className="mb-4 w-full">
                                <label className="text-sm font-medium text-gray-700 mb-1 block">
                                    {field === 'accountId' ? 'Account ID' : field.replace(/([A-Z])/g, ' $1')}
                                </label>
                                <input
                                    type="text"
                                    className={`w-full p-3 border ${errors[field] ? 'border-red-500' : 'border-gray-300'} rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500`}
                                    value={netsuiteCreds[field]}
                                    onChange={(e) => setNetsuiteCreds({ ...netsuiteCreds, [field]: e.target.value })}
                                />
                                {errors[field] && <p className="text-red-500 text-sm">{errors[field]}</p>}
                            </div>
                        ))}
                    </div>
                </div>

                {/* Submit Button */}
                <div className="px-8 py-6 border-t flex justify-end">
                    <button
                        type="submit"
                        className="px-6 py-3 bg-blue-600 text-white font-semibold rounded-md hover:bg-blue-700 transition"
                    >
                        Save & Continue
                    </button>
                </div>
            </div>
        </form>
    );
};

export default AuthForm;