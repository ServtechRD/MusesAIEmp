import React, { useState } from 'react';
import styled from 'styled-components';
import api from '../services/api';


const LoginContainer = styled.div`
  display: 'flex';
  justifyContent: 'center';
  alignItems: 'center';
  height: '100vh' 
`;

const LogoItem = styled.img`
  width: '100px';
  height: '100px';
  marginBottom: '20px';
`;

const UserInput = styled.input`
  padding: '10px';
  marginBottom: '10px';
  width: '200px';
`;

const PasswordInput = styled.input`
  padding: '10px';
  marginBottom: '10px';
  width: '200px';
`;

const LoginButton = styled.button`
   padding: '10px';
   width: '100px';
   backgroundColor: '#3498db';
   color: '#fff', border: 'none'; 
`;



function Login({ setToken }) {
  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState('');

  const handleLogin = async () => {
    try {
      const response = await api.post('/login', { username, password });
      setToken(response.data.access_token);
    } catch (error) {
      setError('代號或密碼錯誤');
    }
  };

  return (
    <LoginContainer>
      <LogoItem src="/static/assets/images/logo.png" alt="logo"/>
      <h2>登錄</h2>
      <UserInput
        type="text"
        placeholder="使用者代號"
        onChange={(e) => setUsername(e.target.value)}
      />
      <PasswordInput
        type="password"
        placeholder="使用者密碼"
        onChange={(e) => setPassword(e.target.value)}
      />
      <LoginButton onClick={handleLogin}>登入</LoginButton>
      {error && <p>{error}</p>}
    </LoginContainer>
  );
}

export default Login;
