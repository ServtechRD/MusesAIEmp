import React, { useState, useEffect, useRef } from "react";
import {
  Box,
  Grid,
  AppBar,
  Toolbar,
  Typography,
  TextField,
  Button,
  Paper,
  Avatar,
  IconButton,
} from "@mui/material";
import { styled } from "@mui/material/styles";
//import SendIcon from '@mui/icons-material/Send';
//import DeleteIcon from '@mui/icons-material/Delete';

//

import {
  Brightness4 as Brightness4Icon,
  Brightness7 as Brightness7Icon,
  Send as SendIcon,
  Delete as DeleteIcon,
} from "@mui/icons-material";

import { PrismLight as SyntaxHighlighter } from "react-syntax-highlighter";
import { dracula, prism } from "react-syntax-highlighter/dist/esm/styles/prism";
import jsx from "react-syntax-highlighter/dist/esm/languages/prism/jsx";

import ReactMarkdown from "react-markdown";
import { jwtDecode } from "jwt-decode";
import api from "../services/api";

SyntaxHighlighter.registerLanguage("jsx", jsx);

const ChatContainer = styled(Box)(({ theme }) => ({
  display: "flex",
  flexDirection: "column",
  height: "80vh",
}));

const MessagesContainer = styled(Box)(({ theme }) => ({
  flex: 1,
  padding: theme.spacing(2),
  overflowY: "auto",
}));

const MessageBubble = styled(Box)(({ theme, isUser }) => ({
  maxWidth: "60%",
  marginBottom: theme.spacing(2),
  alignSelf: isUser ? "flex-end" : "flex-start",
  display: "flex",
  flexDirection: "column",
}));

const UserInfoContainer = styled(Box)(({ theme }) => ({
  display: "flex",
  flexDirection: "row",
  alignItems: "center",
  marginBottom: theme.spacing(0.5),
}));

const BubbleContent = styled(Paper)(({ theme, isUser }) => ({
  padding: theme.spacing(1.5, 2.5),
  borderRadius: 20,
  borderBottomRightRadius: isUser ? 0 : 20,
  borderBottomLeftRadius: isUser ? 20 : 0,
  backgroundColor: isUser
    ? theme.palette.primary.main
    : theme.palette.grey[200],
  color: isUser
    ? theme.palette.primary.contrastText
    : theme.palette.text.primary,
  wordBreak: "break-word",
}));

const InputContainer = styled(Box)(({ theme }) => ({
  padding: theme.spacing(1, 2),
  display: "flex",
  borderTop: `1px solid ${theme.palette.divider}`,
}));

const UserName = styled(Typography)(({ theme, isUser }) => ({
  fontSize: 14,
  fontWeight: "bold",
  color: isUser ? theme.palette.primary.main : theme.palette.text.primary,
  marginBottom: theme.spacing(0.5),
  alignSelf: isUser ? "flex-end" : "flex-start",
}));

const ThumbnailContainer = styled(Box)(({ theme }) => ({
  display: "flex",
  justifyContent: "center",
  marginBottom: theme.spacing(1),
}));

const Thumbnail = styled("img")(({ theme }) => ({
  maxWidth: 100,
  maxHeight: 100,
  margin: theme.spacing(0.5),
  border: `1px solid ${theme.palette.divider}`,
  borderRadius: theme.shape.borderRadius,
}));

function ChatPage({ token }) {
  const [darkMode, setDarkMode] = useState(false);
  const [code, setCode] = useState("// Your React code here");

  const [messages, setMessages] = useState([]);
  const [input, setInput] = useState("");
  const [userName, setUserName] = useState("");
  const [uploadedImages, setUploadedImages] = useState([]);
  const [imageFiles, setImageFiles] = useState([]);
  const [taskId, setTaskId] = useState(null);
  const [prevStatus, setPrevStatus] = useState("---");
  const [assistantName, setAssistantName] = useState("A001");
  const [configStatus, setConfigStatus] = useState("Activate");
  const [fileInputKey, setFileInputKey] = useState(Date.now());
  const messagesEndRef = useRef(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  };

  const theme = createTheme({
    palette: {
      mode: darkMode ? "dark" : "light",
    },
  });

  useEffect(() => {
    if (token) {
      const decodedToken = jwtDecode(token);
      setUserName(decodedToken?.sub || "User");
    }

    if (taskId) {
      const intervalId = setInterval(async () => {
        const response = await api.get(`task_status/${taskId}`);
        let curStatus = response.data.status;

        if (curStatus.startsWith("@@END@@")) {
          curStatus = curStatus.replace("@@END@@", "");
        }

        if (curStatus !== prevStatus) {
          setMessages((prevMessages) => [
            ...prevMessages,
            { sender: "assistant", text: curStatus },
          ]);
        }

        setPrevStatus(curStatus);

        if (
          response.data.status.startsWith("@@END@@") ||
          response.data.status.startsWith("錯誤")
        ) {
          clearInterval(intervalId);
        }
      }, 500);

      return () => clearInterval(intervalId);
    }

    const fetchMessages = async () => {
      try {
        const response = await api.get("/messages", {
          headers: { Authorization: `Bearer ${token}` },
        });
        setMessages(response.data);
        scrollToBottom();
      } catch (error) {
        console.log(error);
      }
    };
    fetchMessages();
  }, [token, taskId, prevStatus]);

  useEffect(() => {
    const getInfo = async () => {
      try {
        const response = await api.get("/info", {
          headers: { Authorization: `Bearer ${token}` },
        });
        setAssistantName(response.data.name);
        let config = response.data.config;
        let configStatus = `${config["PROJ_ID"]} | ${config["PROJ_DESC"]} | ${config["APP_DESC"]} | ${config["FUNC_DESC"]} | ${config["FUNC_FILE"]}`;
        setConfigStatus(configStatus);
      } catch (error) {
        console.log(error);
      }
    };
    getInfo();
  }, [assistantName, configStatus, token]);

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  const handleImageChange = (e) => {
    const files = Array.from(e.target.files).slice(0, 5);
    setImageFiles(files[0]);
    setUploadedImages((prevImages) => [
      ...prevImages,
      URL.createObjectURL(files[0]),
    ]);
  };

  const handlePaste = (event) => {
    const clipboardItems = event.clipboardData.items;

    for (let i = 0; i < clipboardItems.length; i++) {
      const item = clipboardItems[i];

      if (item.type.includes("image")) {
        const file = item.getAsFile();
        const reader = new FileReader();

        setImageFiles(file);

        reader.onload = (e) => {
          setUploadedImages((prevImages) => [...prevImages, e.target.result]);
        };

        reader.readAsDataURL(file);
        event.preventDefault();
        return;
      } else if (item.kind === "string") {
        item.getAsString((text) => {
          setInput((prevValue) => prevValue + text);
        });
      }
    }
  };

  const handleReset = async () => {
    setInput("");
    setImageFiles([]);
    setUploadedImages([]);
    setFileInputKey(Date.now());
  };

  const handleSend = async () => {
    if (!input.trim()) return;

    setMessages([...messages, { sender: "user", text: input, name: userName }]);

    try {
      const formData = new FormData();
      formData.append("message", input);

      let api_name = "/message";
      if (imageFiles instanceof File) {
        api_name = "/message_images";
        formData.append("images", imageFiles);
      }

      const response = await api.post(api_name, formData, {
        headers: {
          Authorization: `Bearer ${token}`,
          "Content-Type": "multipart/form-data",
        },
      });

      if (response.data.task_id) {
        setTaskId(response.data.task_id);
      } else if (input.includes("/CONFIG") && input.includes("SET")) {
        await getInfo();
      }

      setInput("");
      setImageFiles([]);
      setUploadedImages([]);
      setFileInputKey(Date.now());

      setMessages((prevMessages) => [
        ...prevMessages,
        { sender: "assistant", text: response.data.message },
      ]);
    } catch (error) {
      setMessages((prevMessages) => [
        ...prevMessages,
        { sender: "assistant", text: error.toString() },
      ]);
    }
  };

  return (
    <ThemeProvider theme={theme}>
      <Box sx={{ flexGrow: 1 }}>
        <AppBar position="static">
          <Toolbar>
            <Typography variant="h6" component="div" sx={{ flexGrow: 1 }}>
              AI Chat & Code Editor
            </Typography>
            <IconButton color="inherit" onClick={() => setDarkMode(!darkMode)}>
              {darkMode ? <Brightness7Icon /> : <Brightness4Icon />}
            </IconButton>
          </Toolbar>
        </AppBar>
        <Grid container spacing={2} sx={{ height: "calc(100vh - 64px)" }}>
          <Grid item xs={12} md={6}>
            <ChatContainer>
              <MessagesContainer>
                {messages.map((msg, index) => (
                  <MessageBubble key={index} isUser={msg.sender === "user"}>
                    {msg.sender === "user" && (
                      <UserName variant="body2" isUser={msg.sender === "user"}>
                        {msg.name}
                      </UserName>
                    )}
                    {msg.sender === "assistant" && (
                      <UserInfoContainer>
                        <Avatar
                          src="/static/assets/images/A001.png"
                          alt="A001"
                          sx={{ width: 40, height: 40, marginRight: 1 }}
                        />
                        <Box>
                          <Typography variant="subtitle2">
                            {assistantName}
                          </Typography>
                          <Typography variant="caption" color="text.secondary">
                            {configStatus}
                          </Typography>
                        </Box>
                      </UserInfoContainer>
                    )}
                    <BubbleContent isUser={msg.sender === "user"}>
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
                      <Thumbnail
                        key={index}
                        src={image}
                        alt={`Pasted content ${index}`}
                      />
                    ))}
                  </ThumbnailContainer>
                )}

                <input
                  type="file"
                  key={fileInputKey}
                  multiple
                  onChange={handleImageChange}
                  style={{ display: "none" }}
                  id="image-upload"
                />
                <label htmlFor="image-upload">
                  <Button variant="contained" component="span" sx={{ mr: 1 }}>
                    Upload Image
                  </Button>
                </label>
                <TextField
                  multiline
                  rows={3}
                  value={input}
                  onPaste={handlePaste}
                  onChange={(e) => setInput(e.target.value)}
                  placeholder="輸入需求或插入圖片"
                  fullWidth
                  variant="outlined"
                  sx={{ mr: 1 }}
                />
                <IconButton color="primary" onClick={handleSend}>
                  <SendIcon />
                </IconButton>
                <IconButton color="error" onClick={handleReset}>
                  <DeleteIcon />
                </IconButton>
              </InputContainer>
            </ChatContainer>
          </Grid>
          <Grid item xs={12} md={6}>
            <Paper sx={{ height: "100%", overflow: "auto" }}>
              <SyntaxHighlighter
                language="jsx"
                style={darkMode ? dracula : prism}
                customStyle={{ height: "100%", margin: 0 }}
              >
                {code}
              </SyntaxHighlighter>
            </Paper>
          </Grid>
        </Grid>
      </Box>
    </ThemeProvider>
  );
}

export default ChatPage;
