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
  const [engineerType, setEngineerType] = useState("1"); // 預設為前端工程師
  return (
    <>
      <GlobalStyles />
      {!token ? (
        <div>
          <LoginPage setToken={setToken} setEngineerType={setEngineerType} />
        </div>
      ) : (
        <div>
          <ChatPage token={token} engineerType={engineerType} />

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
