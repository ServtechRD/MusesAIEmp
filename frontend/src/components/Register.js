import React, { useState } from 'react';
import api from '../services/api';

function Register() {
  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');
  const [email, setEmail] = useState(''); // 如果需要邮箱
  const [error, setError] = useState('');
  const [success, setSuccess] = useState('');

  const handleRegister = async () => {
    try {
      const response = await api.post('/register', { username, password });
      setSuccess('註冊成功, 請登入');
    } catch (error) {
      setError('註冊失敗, 使用者代碼可能已存在');
    }
  };

  return (
    <div>
      <h2>注册</h2>
      <input
        type="text"
        placeholder="使用者代號"
        onChange={(e) => setUsername(e.target.value)}
      />
      <input
        type="password"
        placeholder="使用者密碼"
        onChange={(e) => setPassword(e.target.value)}
      />
      {/* 如果需要邮箱
      <input
        type="email"
        placeholder="邮箱"
        onChange={(e) => setEmail(e.target.value)}
      />
      */}
      <button onClick={handleRegister}>注册</button>
      {error && <p>{error}</p>}
      {success && <p>{success}</p>}
    </div>
  );
}

export default Register;
