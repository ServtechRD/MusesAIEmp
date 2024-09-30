import React, { useState } from 'react';
import GlobalStyles from './styles/GlobalStyles';
import Login from './components/Login';
import Register from './components/Register';
import ChatWindow from './components/ChatWindow';
import ImageUpload from './components/ImageUpload';
import CodeUpload from './components/CodeUpload';
import LoginPage from './components/LoginScreen';

function App() {
  const [token, setToken] = useState(null);

  return (
    <>
      <GlobalStyles />
      {!token ? (
        <div>
          <LoginPage setToken={setToken} />
          <Register />
        </div>
      ) : (
        <div>
          <ChatWindow token={token} />
          
          {/* 
          <ImageUpload token={token} />
          <CodeUpload token={token} />
           */}
           
        </div>
      )}
    </>
  );
}

export default App;
