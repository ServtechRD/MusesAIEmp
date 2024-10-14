import React, { useState } from "react";
import GlobalStyles from "./styles/GlobalStyles";
import Login from "./components/Login";
import Register from "./components/Register";
import ChatWindow from "./components/ChatWindow";
import ImageUpload from "./components/ImageUpload";
import CodeUpload from "./components/CodeUpload";
import LoginPage from "./components/LoginScreen";
import ChatPage from "./components/ChatPage";

function App() {
  const [token, setToken] = useState(null);
  const [engineer, setEngineer] = useState({}); // 預設為前端工程師
  return (
    <>
      <GlobalStyles />
      {!token ? (
        <div>
          <LoginPage
            setToken={setToken}
            setEngineer={setEngineer}
            engineer={engineer}
          />
        </div>
      ) : (
        <div>
          <ChatPage token={token} engineer={engineer} setToken={setToken} />

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
