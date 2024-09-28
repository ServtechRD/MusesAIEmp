import React, { useState, useEffect, useRef } from 'react';
import styled from 'styled-components';
import api from '../services/api';
import ReactMarkdown from 'react-markdown';
import jwtDecode from 'jwt-decode'; // 引入 jwt-decode 用於解析 JWT

const ChatContainer = styled.div`
  display: flex;
  flex-direction: column;
  height: 80vh;
`;

const MessagesContainer = styled.div`
  flex: 1;
  padding: 20px;
  overflow-y: auto;
`;

const MessageBubble = styled.div`
  max-width: 60%;
  margin-bottom: 20px;
  align-self: ${(props) => (props.isUser ? 'flex-end' : 'flex-start')};
  display: flex;
  flex-direction: column;
`;


const UserInfoContainer = styled.div`
  display: flex;
  flex-direction: row;
  align-items: center; /* 讓 Avatar 和文字框垂直對齊 */
  margin-bottom: 4px; /* Avatar 和訊息間的間距 */
`;



const BubbleContent = styled.div`
  background-color: ${(props) => (props.isUser ? '#007aff' : '#e5e5ea')};
  color: ${(props) => (props.isUser ? '#fff' : '#000')};
  padding: 12px 20px;
  border-radius: 20px;
  border-bottom-right-radius: ${(props) => (props.isUser ? '0' : '20px')};
  border-bottom-left-radius: ${(props) => (props.isUser ? '20px' : '0')};
  word-break: break-word; /* 防止長字串溢出 */
`;

const InputContainer = styled.div`
  padding: 10px 20px;
  display: flex;
  border-top: 1px solid #ccc;
`;

const InputField = styled.textarea`
  flex: 1;
  resize: none;
  border: none;
  border-radius: 20px;
  padding: 10px 15px;
  font-size: 16px;
  outline: none;
`;

const SendButton = styled.button`
  background-color: #007aff;
  color: #fff;
  border: none;
  border-radius: 20px;
  padding: 10px 15px;
  margin-left: 10px;
  cursor: pointer;
  font-size: 16px;
`;

const Avatar = styled.img`
  width: 40px;
  height: 40px;
  border-radius: 50%;
  margin-right: 10px;
`;

const TextContainer = styled.div`
  display: flex;
  flex-direction: column;
`;

const NameText = styled.div`
  font-weight: bold;
  margin-bottom: 2px;
`;

const SettingsText = styled.div`
  font-size: 12px;
  color: gray;
`;



function ChatWindow({ token }) {
  const [messages, setMessages] = useState([]);
  const [input, setInput] = useState('');
  const [userName, setUserName] = useState(''); // 儲存使用者名稱
  const messagesEndRef = useRef(null);

  // 滚动到底部
  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  // 从服务器获取历史消息
  useEffect(() => {

    if (token) {
      const decodedToken = jwtDecode(token);
      setUserName(decodedToken?.sub || 'User'); // 根據 token 中的 name 字段設置名稱
    }

    const fetchMessages = async () => {
      try {
        const response = await api.get('/messages', {
          headers: { Authorization: `Bearer ${token}` },
        });
        setMessages(response.data);
        scrollToBottom();
      } catch (error) {
        // 处理错误
      }
    };
    fetchMessages();
  }, [token]);

  // 当消息更新时滚动到底部
  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  const handleSend = async () => {
    if (!input.trim()) return;

    // 更新本地消息列表
    setMessages([...messages, { sender: 'user', text: input ,name: userName}]);

    try {
      const response = await api.post(
        '/message',
        { text: input },
        { headers: { Authorization: `Bearer ${token}` } }
      );

      // 更新本地消息列表
      setMessages((prevMessages) => [
        ...prevMessages,
        { sender: 'assistant', text: response.data },
      ]);
    } catch (error) {
      // 处理错误
    }

    setInput('');
  };

  return (
    <ChatContainer>
      <MessagesContainer>
        {messages.map((msg, index) => (
          <MessageBubble key={index} isUser={msg.sender === 'user'}>
            {msg.sender === 'user' && (
              <UserName isUser={msg.sender === 'user'}>
                 {msg.name}
             </UserName>
            )}
            {msg.sender === 'assistant' && (
              <UserInfoContainer>
                  <Avatar src="/static/assets/images/A001.png" alt="A001" />
                  <TextContainer>
                    <NameText>Assistant</NameText>
                    <SettingsText>Active</SettingsText>
                </TextContainer>
              </UserInfoContainer>
            )}
            <BubbleContent isUser={msg.sender === 'user'}>
              <ReactMarkdown>{msg.text}</ReactMarkdown>
            </BubbleContent>
          </MessageBubble>
        ))}
        <div ref={messagesEndRef} />
      </MessagesContainer>
      <InputContainer>
        <InputField
          rows={1}
          value={input}
          onChange={(e) => setInput(e.target.value)}
          placeholder="请输入消息"
        />
        <SendButton onClick={handleSend}>发送</SendButton>
      </InputContainer>
    </ChatContainer>
  );
}

export default ChatWindow;
