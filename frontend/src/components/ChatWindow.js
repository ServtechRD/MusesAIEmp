import React, { useState, useEffect, useRef } from 'react';
import styled from 'styled-components';
import api from '../services/api';

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
`;

const BubbleContent = styled.div`
  background-color: ${(props) => (props.isUser ? '#007aff' : '#e5e5ea')};
  color: ${(props) => (props.isUser ? '#fff' : '#000')};
  padding: 12px 20px;
  border-radius: 20px;
  border-bottom-right-radius: ${(props) => (props.isUser ? '0' : '20px')};
  border-bottom-left-radius: ${(props) => (props.isUser ? '20px' : '0')};
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

function ChatWindow({ token }) {
  const [messages, setMessages] = useState([]);
  const [input, setInput] = useState('');
  const messagesEndRef = useRef(null);

  // 滚动到底部
  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  // 从服务器获取历史消息
  useEffect(() => {
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
    setMessages([...messages, { sender: 'user', text: input }]);

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
            <BubbleContent isUser={msg.sender === 'user'}>
              <p style={{ margin: 0, whiteSpace: 'pre-wrap' }}>{msg.text}</p>
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
