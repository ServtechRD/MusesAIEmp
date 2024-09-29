import React, { useState, useEffect, useRef } from 'react';
import styled from 'styled-components';
import api from '../services/api';
import ReactMarkdown from 'react-markdown';
import { jwtDecode } from "jwt-decode";

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

const UserName = styled.div`
  font-size: 14px;
  font-weight: bold;
  color: ${(props) => (props.isUser ? '#007aff' : '#000')};
  margin-bottom: 5px;
  align-self: ${(props) => (props.isUser ? 'flex-end' : 'flex-start')};
`;


const ThumbnailContainer = styled.div`
  display: flex;
  justify-content: center;
  margin-bottom: 10px;
`;

const Thumbnail = styled.img`
  max-width: 100px;
  max-height: 100px;
  margin: 5px;
  border: 1px solid #ccc;
  border-radius: 8px;
`;


function ChatWindow({ token }) {
  const [messages, setMessages] = useState([]);
  const [input, setInput] = useState('');
  const [userName, setUserName] = useState(''); // 儲存使用者名稱
  const [uploadedImages, setUploadedImages] = useState([]);
  const [imageFiles, setImageFiles] = useState([]);
  const [taskId, setTaskId] = useState(null);
  const [prevStatus, setPrevStatus] = useState('');
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

    
    if (taskId) {
      // 每隔 5 秒查詢一次任務狀態

      const intervalId = setInterval(async () => {
        const response = await api.get(`task_status/${taskId}`);
        //setStatus(response.data.status);

        if(response.data.status != prevStatus) {
          setMessages((prevMessages) => [
            ...prevMessages,
            { sender: 'assistant', text: response.data.status },
          ]);
        }

        setPrevStatus(response.data.status);
        
        // 如果任務已完成，停止查詢
        if (response.data.status === "處理完畢" || response.data.status.startsWith("錯誤")) {
          clearInterval(intervalId);
        }
      }, 1000);

      // 清除計時器
      return () => clearInterval(intervalId);
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
  }, [token,taskId]);

  // 当消息更新时滚动到底部
  useEffect(() => {
    scrollToBottom();
  }, [messages]);


  // 處理貼上事件
  const handlePaste = (event) => {
    const clipboardItems = event.clipboardData.items;
    let textContent = '';

    for (let i = 0; i < clipboardItems.length; i++) {
      const item = clipboardItems[i];

      // 判斷是否是圖片類型
      if (item.type.includes('image')) {
        const file = item.getAsFile();
        const reader = new FileReader();

        setImageFiles(file)

        reader.onload = (e) => {
          //setUploadedImage(e.target.result); // 設定圖片 URL
          setUploadedImages((prevImages) => [...prevImages, e.target.result]); // 添加圖片 URL
        };
        
        reader.readAsDataURL(file);
        event.preventDefault(); // 阻止預設行為，不插入圖片的文字描述
        return;
      } else if (item.kind === 'string') {
        // 處理文字
        item.getAsString((text) => {
          textContent += text;
          setInput((prevValue) => prevValue + textContent);
        });
      }
    }

    // 如果沒有圖片，直接插入文字
    //setInput(event.clipboardData.getData('text'));
  };

  const handleSend = async () => {
    if (!input.trim()) return;

    // 更新本地消息列表
    setMessages([...messages, { sender: 'user', text: input ,name: userName}]);

    try {

      const formData = new FormData();
      formData.append('message', input);  // 添加文字字段
      formData.append('images', imageFiles);     // 添加圖片文件

      const response = await api.post(
        '/message',
        formData,
        { headers: { Authorization: `Bearer ${token}` ,
         'Content-Type': 'multipart/form-data', } }
      );

      console.log(response.data)
      if(response.data.task_id) {
         console.log('task id :'+response.data.task_id)
         setTaskId(response.data.task_id); // 設置任務 ID
      }
     

      // 更新本地消息列表
      setMessages((prevMessages) => [
        ...prevMessages,
        { sender: 'assistant', text: response.data.message },
      ]);
    } catch (error) {
      // 处理错误
    }

    setInput('');
    setImageFiles([])
    setUploadedImages([])
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

        {uploadedImages.length > 0 && (
        <ThumbnailContainer>
          {uploadedImages.map((image, index) => (
            <Thumbnail key={index} src={image} alt={`Pasted content ${index}`} />
          ))}
        </ThumbnailContainer>
       )}
        <InputField
          rows={3}
          value={input}
          onPaste={handlePaste}
          onChange={(e) => setInput(e.target.value)}
          placeholder="輸入需求或插入圖片"
        />
       
        <SendButton onClick={handleSend}>送出</SendButton>
      </InputContainer>
    </ChatContainer>
  );
}

export default ChatWindow;
