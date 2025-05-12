// src/pages/AuthPage.jsx
import React from 'react';
import { useNavigate } from 'react-router-dom'; // 1. Import useNavigate
import AuthForm from '../components/AuthForm';
import gruveLogo from '../assets/gruve.png';

const AuthPage = () => {
  const navigate = useNavigate(); // 2. Initialize the navigate function

  const handleComplete = () => {
    // alert('Next step triggered'); // We'll replace this
    console.log('Authentication complete, navigating to index users page...');
    navigate('/index-users'); // 3. Navigate to the new page
  };

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Top Bar with Gruve Logo + Heading */}
      <div className="bg-white py-4 px-6 shadow-sm flex items-center justify-between">
        <img src={gruveLogo} alt="Gruve Logo" className="h-10" />
        <h1 className="text-xl font-bold text-center flex-grow -ml-10"> {/* Consider adjusting margin if Gruve logo size changes text centering */}
          Step 1: Enter Authentication Details
        </h1>
        <div className="w-10" /> {/* Placeholder for spacing on the right */}
      </div>

      {/* Auth Form */}
      <AuthForm onComplete={handleComplete} />
    </div>
  );
};

export default AuthPage;