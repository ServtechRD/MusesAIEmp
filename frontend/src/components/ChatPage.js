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
  List,
  ListItem,
  ListItemText,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  MenuItem,
  Select,
  InputLabel,
  FormControl,
} from "@mui/material";
import { ThemeProvider, createTheme, styled } from "@mui/material/styles";

//import SendIcon from '@mui/icons-material/Send';
//import DeleteIcon from '@mui/icons-material/Delete';

//

import {
  Brightness4 as Brightness4Icon,
  Brightness7 as Brightness7Icon,
  Send as SendIcon,
  Delete as DeleteIcon,
  Code as CodeIcon,
  Menu as MenuIcon,
  Image as ImageIcon,
  Link as LinkIcon,
  Close as CloseIcon,
} from "@mui/icons-material";

import { Light as SyntaxHighlighter } from "react-syntax-highlighter";
import { dracula, prism } from "react-syntax-highlighter/dist/esm/styles/prism";
import docco from "react-syntax-highlighter/dist/esm/styles/hljs/docco";
import jsx from "react-syntax-highlighter/dist/esm/languages/prism/jsx";
import js from "react-syntax-highlighter/dist/esm/languages/hljs/javascript";

import ReactMarkdown from "react-markdown";
import { jwtDecode } from "jwt-decode";
import api from "../services/api";

import ImageDialog from "./ImageDialog";

SyntaxHighlighter.registerLanguage("jsx", jsx);
SyntaxHighlighter.registerLanguage("javascript", js);

// 调整 AppBar 高度
const LowAppBar = styled(AppBar)(({ theme }) => ({
  height: 48, // 降低 AppBar 高度
}));

const LowToolbar = styled(Toolbar)(({ theme }) => ({
  minHeight: 48, // 降低 Toolbar 高度
  paddingTop: theme.spacing(0.5),
  paddingBottom: theme.spacing(0.5),
}));

const NewConversationButton = styled(Button)(({ theme }) => ({
  margin: theme.spacing(2),
  padding: theme.spacing(1, 2),
}));

// 调整主容器高度计算
const MainContainer = styled(Box)(({ theme }) => ({
  height: "calc(100vh - 20vh)", // 根据新的 AppBar 高度调整
  display: "flex",
}));

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
  maxWidth: "80%",
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
    ? theme.palette.secondary.light
    : theme.palette.success.light,
  color: isUser
    ? theme.palette.secondary.contrastText
    : theme.palette.success.contrastText,
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
  color: isUser ? theme.palette.info.main : theme.palette.success.main,
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

function ChatPage({ token, engineer }) {
  const [darkMode, setDarkMode] = useState(false);
  const [code, setCode] = useState("// Your React code here");
  const [codeDialogOpen, setCodeDialogOpen] = useState(false);
  const [conversations, setConversations] = useState([]);
  const [currentConversationId, setCurrentConversationId] = useState(0);
  const [showConversationList, setShowConversationList] = useState(true);

  // State for dialogs
  const [projectDialogOpen, setProjectDialogOpen] = useState(false);
  const [switchProjectDialogOpen, setSwitchProjectDialogOpen] = useState(false);
  const [switchFunctionDialogOpen, setSwitchFunctionDialogOpen] =
    useState(false);

  const [reDoDialogOpen, setReDoDialogOpen] = useState(false);

  const [thumbnails, setThumbnails] = useState([]);
  const [selectedImage, setSelectedImage] = useState(null);
  const [markdownText, setMarkdownText] = useState("");
  const [codeText, setCodeText] = useState("");
  const [selectedFilename, setSelectedFilename] = useState(null);

  // Project data
  const [projectId, setProjectId] = useState("");
  const [projectDescription, setProjectDescription] = useState("");
  const [projectMode, setProjectMode] = useState("Basic");

  // Feature data
  const [appName, setAppName] = useState("");
  const [appDescription, setAppDescription] = useState("");
  const [funcDescription, setFuncDescription] = useState("");
  const [funcFileName, setFuncFileName] = useState("");

  const [currentProject, setCurrentProject] = useState("");
  const [projects, setProjects] = useState([
    "Project A",
    "Project B",
    "Project C",
  ]); // Placeholder project list

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
      success: { main: "#bcfa8d" },
      secondary: { main: "#daf079" },
    },
  });

  useEffect(() => {
    if (token) {
      const decodedToken = jwtDecode(token);
      setUserName(decodedToken?.sub || "User");
    }

    const fetchConversations = async () => {
      try {
        const response = await api.get("/conversations", {
          headers: { Authorization: `Bearer ${token}` },
        });
        setConversations(response.data);
        if (response.data.length > 0) {
          setCurrentConversationId(response.data[0].id);
        }
      } catch (error) {
        console.log(error);
      }
    };
    fetchConversations();
  }, [token]);

  // if update id , fetch messages()
  useEffect(() => {
    fetchMessages();
  }, [currentConversationId]);

  const fetchMessages = async () => {
    try {
      if (currentConversationId == 0) {
        return;
      }
      const response = await api.get(
        "/conversations/" + currentConversationId + "/messages",
        {
          headers: { Authorization: `Bearer ${token}` },
        },
      );
      setMessages(response.data);
      scrollToBottom();
    } catch (error) {
      console.log(error);
    }
  };

  useEffect(() => {
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

    fetchMessages();
  }, [token, taskId, prevStatus]);

  useEffect(() => {
    getInfo();
  }, [assistantName, configStatus, token]);

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  useEffect(() => {
    if (reDoDialogOpen) {
      fetchThumbnails();
    }
  }, [reDoDialogOpen]);

  const getInfo = async () => {
    try {
      const response = await api.get("/info", {
        headers: { Authorization: `Bearer ${token}` },
      });
      setAssistantName(engineer.EMP_NAME);
      //setAssistantName(response.data.name);
      let config = response.data.config;
      let configStatus = `${config["PROJ_ID"]} | ${config["PROJ_DESC"]} | ${config["APP_DESC"]} | ${config["FUNC_DESC"]} | ${config["FUNC_FILE"]}`;

      setAppName(config["APP_NAME"]);
      setAppDescription(config["APP_DESC"]);
      setFuncDescription(config["FUNC_DESC"]);
      setFuncFileName(config["FUNC_FILE"]);

      setConfigStatus(configStatus);
    } catch (error) {
      console.log(error);
    }
  };

  const openSwitchDialog = async () => {
    try {
      const response = await api.get("/projects", {
        headers: { Authorization: `Bearer ${token}` },
      });

      let prjs = JSON.parse(response.data.projects);
      console.log(prjs);
      setProjects(prjs);

      setSwitchProjectDialogOpen(true);
    } catch (error) {
      console.log(error);
    }
  };

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

  const handleApiCall = async (msg, images) => {
    const formData = new FormData();
    formData.append("message", msg);
    formData.append("conversation_id", currentConversationId);

    let api_name = "/message";
    if (images instanceof File) {
      api_name = "/message_images";
      formData.append("images", images);
    }

    const response = await api.post(api_name, formData, {
      headers: {
        Authorization: `Bearer ${token}`,
        "Content-Type": "multipart/form-data",
      },
    });

    if (response.data.task_id) {
      setTaskId(response.data.task_id);
    } else if (msg.includes("/CONFIG") && msg.includes("SET")) {
      await getInfo();
    }
    return response;
  };

  const handleSend = async () => {
    if (!input.trim()) return;

    setMessages([...messages, { sender: "user", text: input, name: userName }]);

    try {
      const response = await handleApiCall(input, imageFiles);

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

  const handleNewConversation = async () => {
    try {
      const employee_id = engineer.EMP_ID;
      const title = Date.now().toLocaleString();
      const response = await api.post(
        "/conversations",
        { title, employee_id },
        {
          headers: { Authorization: `Bearer ${token}` },
        },
      );
      setConversations([...conversations, response.data]);
      setCurrentConversationId(response.data.id);
      setMessages([]);
    } catch (error) {
      console.log(error);
    }
  };

  // Function to handle creating a new project
  const handleCreateProject = async () => {
    try {
      const input1 = "/CONFIG SET PROJ_ID " + projectId;
      const input2 = "/CONFIG SET PROJ_DESC " + projectDescription;
      const input3 = "/CONFIG SET PROJ_MODE 0";

      setMessages([
        ...messages,
        {
          sender: "user",
          text: "建立專案" + projectDescription,
          name: userName,
        },
      ]);

      const rep1 = await handleApiCall(input1, null);
      console.log("Creating project id:", rep1);

      const rep2 = await handleApiCall(input2, null);
      console.log("Creating project desc:", rep2);

      const rep3 = await handleApiCall(input3, null);
      console.log("Creating project mode:", rep3);

      setProjects([...projects, projectId + "|" + projectDescription]);
      setMessages((prevMessages) => [
        ...prevMessages,
        { sender: "assistant", text: "建立成功" },
      ]);
    } catch (error) {
      setMessages((prevMessages) => [
        ...prevMessages,
        { sender: "assistant", text: "建立失敗-" + error.toString() },
      ]);
    }
    setProjectDialogOpen(false);
  };

  // Function to handle switching projects
  const handleSwitchProject = async () => {
    try {
      let items = currentProject.split("|");

      console.log(currentProject);

      setProjectId(items[0]);
      setProjectDescription(items[1]);
      // 因為不會馬上同步,所以用items

      const input1 = "/CONFIG SET PROJ_ID " + items[0];
      const input2 = "/CONFIG SET PROJ_DESC " + items[1];
      //const input3 = "/CONFIG SET PROJ_MODE " + projectMode;

      console.log(input1);
      console.log(input2);

      setMessages([
        ...messages,
        {
          sender: "user",
          text: "切換專案 :" + items[1],
          name: userName,
        },
      ]);

      const rep1 = await handleApiCall(input1, null);
      console.log("Swtich project id:", rep1);

      const rep2 = await handleApiCall(input2, null);
      console.log("Swtich project desc:", rep2);

      //  const rep3 = handleApiCall(input3, null);
      //  console.log("Creating project mode:", rep3);

      setProjects([...projects, currentProject]);
      setMessages((prevMessages) => [
        ...prevMessages,
        { sender: "assistant", text: "切換成功" },
      ]);
    } catch (error) {
      setMessages((prevMessages) => [
        ...prevMessages,
        { sender: "assistant", text: "切換失敗-" + error.toString() },
      ]);
    }
    setSwitchProjectDialogOpen(false);
  };

  // Function to handle creating a new feature
  const handleSwitchFunction = async () => {
    try {
      const input1 = "/CONFIG SET APP_NAME " + appName;
      const input2 = "/CONFIG SET APP_DESC " + appDescription;
      const input3 = "/CONFIG SET FUNC_DESC " + funcDescription;
      const input4 = "/CONFIG SET FUNC_FILE " + funcFileName;

      setMessages([
        ...messages,
        {
          sender: "user",
          text: "切換功能 :" + appDescription + " > " + funcDescription,
          name: userName,
        },
      ]);

      const rep1 = handleApiCall(input1, null);
      console.log("switch app name:", rep1);

      const rep2 = handleApiCall(input2, null);
      console.log("switch app desc:", rep2);

      const rep3 = handleApiCall(input3, null);
      console.log("switch func desc:", rep3);

      const rep4 = handleApiCall(input4, null);
      console.log("switch func name:", rep4);

      setMessages((prevMessages) => [
        ...prevMessages,
        { sender: "assistant", text: "切換成功" },
      ]);
    } catch (error) {
      setMessages((prevMessages) => [
        ...prevMessages,
        { sender: "assistant", text: "切換失敗-" + error.toString() },
      ]);
    }
    setSwitchFunctionDialogOpen(false);
  };

  const handleViewCode = async () => {
    try {
      setMessages([
        ...messages,
        {
          sender: "user",
          text: "讀取程式碼",
          name: userName,
        },
      ]);

      const rep = "<html> <body>b1</body> </html>";

      setCode(rep);

      setMessages((prevMessages) => [
        ...prevMessages,
        { sender: "assistant", text: "讀取程式碼成功" },
      ]);
    } catch (error) {
      setMessages((prevMessages) => [
        ...prevMessages,
        { sender: "assistant", text: "讀取程式碼失敗-" + error.toString() },
      ]);
    }
    setCodeDialogOpen(true);
  };

  const handleOpenLink = async () => {
    const response = await api.get("/workurl", {
      headers: {
        Authorization: `Bearer ${token}`,
        "Content-Type": "multipart/form-data",
      },
    });

    console.log(response);
    window.open(response.data, "_blank");
  };

  const fetchThumbnails = async () => {
    try {
      //const response = await fetch("/api/thumbnails");
      const response = await api.get("/thumbnails", {
        headers: { Authorization: `Bearer ${token}` },
      });
      const data = await response.data;
      setThumbnails(data);
    } catch (error) {
      console.error("Error fetching thumbnails:", error);
    }
  };

  const handleImageSelect = async (filename) => {
    try {
      setSelectedFilename(filename);
      console.log(filename);
      //const response = await fetch(`/api/image/${filename}`);
      const formData = new FormData();
      formData.append("filename", filename);
      const response = await api.post("/history", formData, {
        headers: { Authorization: `Bearer ${token}` },
      });
      const data = await response.data;
      setSelectedImage(data.image);
      setMarkdownText(data.markdownText);
      setCodeText(data.codeText);
    } catch (error) {
      console.error("Error fetching image details:", error);
    }
  };

  return (
    <ThemeProvider theme={theme}>
      <Box sx={{ flexGrow: 1 }}>
        <AppBar position="static" sx={{ flexShrink: 0 }}>
          <Toolbar>
            <IconButton
              color="inherit"
              onClick={() => setShowConversationList(!showConversationList)}
              size="small"
              edge="start"
              sx={{ mr: 2 }}
            >
              <MenuIcon fontSize="small" />
            </IconButton>
            <Typography variant="h6" component="div" sx={{ flexGrow: 1 }}>
              {engineer.EMP_DESC + " - " + engineer.EMP_NAME}
            </Typography>
            <IconButton
              color="inherit"
              onClick={() => setCodeDialogOpen(true)}
              size="small"
            >
              <CodeIcon fontSize="small" />
            </IconButton>

            <IconButton color="inherit" onClick={() => setDarkMode(!darkMode)}>
              {darkMode ? <Brightness7Icon /> : <Brightness4Icon />}
            </IconButton>
          </Toolbar>
        </AppBar>
        <MainContainer>
          <Grid container spacing={2}>
            {showConversationList && (
              <Grid item xs={3}>
                <Paper
                  sx={{
                    height: "100%",
                    overflow: "auto",
                    display: "flex",
                    flexDirection: "column",
                  }}
                >
                  <List sx={{ flexGrow: 1, overflowY: "auto" }}>
                    {conversations.map((conversation) => (
                      <ListItem
                        key={conversation.id}
                        button
                        onClick={() => {
                          console.log("current =>" + conversation.id);
                          setCurrentConversationId(conversation.id);
                          console.log("conv id " + currentConversationId);
                          setMessages([]);
                          //fetchMessages(); // didn't call direct , update when render
                        }}
                        selected={currentConversationId === conversation.id}
                      >
                        <ListItemText primary={`需求列表 ${conversation.id}`} />
                      </ListItem>
                    ))}
                  </List>
                  <NewConversationButton
                    variant="contained"
                    onClick={handleNewConversation}
                  >
                    新需求
                  </NewConversationButton>
                </Paper>
              </Grid>
            )}
            <Grid item xs={showConversationList ? 9 : 12}>
              <ChatContainer>
                <MessagesContainer>
                  {messages.map((msg, index) => (
                    <MessageBubble key={index} isUser={msg.sender === "user"}>
                      {msg.sender === "user" && (
                        <UserName
                          variant="body2"
                          isUser={msg.sender === "user"}
                        >
                          {msg.name}
                        </UserName>
                      )}
                      {msg.sender === "assistant" && (
                        <UserInfoContainer>
                          <Avatar
                            src={"/static/assets/images/" + engineer.EMP_IMAGE}
                            alt="A001"
                            sx={{ width: 40, height: 40, marginRight: 1 }}
                          />
                          <Box>
                            <Typography variant="subtitle2">
                              {assistantName}
                            </Typography>
                            <Typography variant="caption" color="text.success">
                              {configStatus}
                            </Typography>

                            <IconButton
                              color="inherit"
                              onClick={() => handleViewCode()}
                              size="small"
                            >
                              <CodeIcon fontSize="small" />
                            </IconButton>
                            <IconButton
                              color="inherit"
                              onClick={handleOpenLink}
                              size="small"
                            >
                              <LinkIcon fontSize="small" />
                            </IconButton>
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

                <Grid container spacing={2}>
                  {/* Main content area */}
                  <Grid item xs={12}>
                    <Box sx={{ display: "flex", gap: 2, p: 2 }}>
                      {/* Buttons */}
                      <Button
                        variant="contained"
                        onClick={() => setProjectDialogOpen(true)}
                      >
                        建立專案
                      </Button>
                      <Button
                        variant="contained"
                        onClick={() => openSwitchDialog()}
                      >
                        切換專案
                      </Button>
                      <Button
                        variant="contained"
                        onClick={() => setSwitchFunctionDialogOpen(true)}
                      >
                        切換功能
                      </Button>
                      <Button
                        variant="contained"
                        onClick={() => setReDoDialogOpen(true)}
                      >
                        再做一次
                      </Button>
                    </Box>
                  </Grid>
                </Grid>

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
                    <IconButton component="span" color="primary">
                      <ImageIcon />
                    </IconButton>
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
          </Grid>
        </MainContainer>
      </Box>
      <Dialog
        open={codeDialogOpen}
        onClose={() => setCodeDialogOpen(false)}
        fullWidth
        maxWidth="md"
      >
        <DialogTitle>程式碼</DialogTitle>
        <DialogContent>
          <SyntaxHighlighter
            language="jsx"
            style={darkMode ? dracula : prism}
            customStyle={{ height: "400px", margin: 0 }}
          >
            {code}
          </SyntaxHighlighter>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setCodeDialogOpen(false)}>下載</Button>
          <Button onClick={() => setCodeDialogOpen(false)}>關閉</Button>
        </DialogActions>
      </Dialog>

      {/* Create Project Dialog */}
      <Dialog
        open={projectDialogOpen}
        onClose={() => setProjectDialogOpen(false)}
      >
        <DialogTitle>建立專案</DialogTitle>
        <DialogContent>
          <TextField
            label="專案代號"
            fullWidth
            value={projectId}
            onChange={(e) => setProjectId(e.target.value)}
            margin="dense"
          />
          <TextField
            label="專案描述"
            fullWidth
            value={projectDescription}
            onChange={(e) => setProjectDescription(e.target.value)}
            margin="dense"
          />
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setProjectDialogOpen(false)}>取消</Button>
          <Button onClick={handleCreateProject}>建立</Button>
        </DialogActions>
      </Dialog>

      {/* Switch Project Dialog */}
      <Dialog
        open={switchProjectDialogOpen}
        onClose={() => setSwitchProjectDialogOpen(false)}
      >
        <DialogTitle>切換專案</DialogTitle>
        <DialogContent>
          <FormControl fullWidth margin="dense">
            <InputLabel>選擇專案</InputLabel>
            <Select
              value={currentProject}
              onChange={(e) => setCurrentProject(e.target.value)}
            >
              {projects.map((project) => (
                <MenuItem key={project} value={project}>
                  {project}
                </MenuItem>
              ))}
            </Select>
          </FormControl>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setSwitchProjectDialogOpen(false)}>
            取消
          </Button>
          <Button onClick={handleSwitchProject}>切換</Button>
        </DialogActions>
      </Dialog>

      {/* Create Feature Dialog */}
      <Dialog
        open={switchFunctionDialogOpen}
        onClose={() => setSwitchFunctionDialogOpen(false)}
      >
        <DialogTitle>切換功能</DialogTitle>
        <DialogContent>
          <TextField
            label="應用代號"
            fullWidth
            value={appName}
            onChange={(e) => setAppName(e.target.value)}
            margin="dense"
          />
          <TextField
            label="應用描述"
            fullWidth
            value={appDescription}
            onChange={(e) => setAppDescription(e.target.value)}
            margin="dense"
          />
          <TextField
            label="功能描述"
            fullWidth
            value={funcDescription}
            onChange={(e) => setFuncDescription(e.target.value)}
            margin="dense"
          />
          <TextField
            label="功能檔名"
            fullWidth
            value={funcFileName}
            onChange={(e) => setFuncFileName(e.target.value)}
            margin="dense"
          />
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setSwitchFunctionDialogOpen(false)}>
            取消
          </Button>
          <Button onClick={handleSwitchFunction}>切換</Button>
        </DialogActions>
      </Dialog>
      {/* Image Dialog */}
      <Dialog
        open={reDoDialogOpen}
        onClose={() => setReDoDialogOpen(false)}
        maxWidth="lg"
        fullWidth
      >
        <DialogTitle>
          Image Viewer
          <IconButton
            aria-label="close"
            onClick={() => setReDoDialogOpen(false)}
            sx={{ position: "absolute", right: 8, top: 8 }}
          >
            <CloseIcon />
          </IconButton>
        </DialogTitle>
        <DialogContent>
          <Grid container spacing={2}>
            <Grid item xs={3}>
              {thumbnails.map((thumb) => (
                <div
                  key={thumb.filename}
                  style={{
                    position: "relative",
                    marginBottom: "10px",
                    cursor: "pointer",
                  }}
                  onClick={() => handleImageSelect(thumb.filename)}
                >
                  <img
                    src={`data:image/jpeg;base64,${thumb.thumbnail}`}
                    alt={thumb.filename}
                    style={{
                      width: "100%",
                      border:
                        selectedFilename === thumb.filename
                          ? "3px solid #1976d2"
                          : "none",
                      borderRadius: "4px",
                      transition: "border 0.3s ease",
                    }}
                  />
                  {selectedFilename === thumb.filename && (
                    <div
                      style={{
                        position: "absolute",
                        top: "5px",
                        right: "5px",
                        background: "#1976d2",
                        color: "white",
                        borderRadius: "50%",
                        width: "20px",
                        height: "20px",
                        display: "flex",
                        alignItems: "center",
                        justifyContent: "center",
                        fontSize: "12px",
                      }}
                    >
                      ✓
                    </div>
                  )}
                </div>
              ))}
            </Grid>
            <Grid item xs={9}>
              <Box display="flex" flexDirection="column" height="100%">
                {selectedImage && (
                  <Box
                    mb={2}
                    display="flex"
                    justifyContent="center"
                    alignItems="center"
                    height="30%"
                  >
                    <img
                      src={selectedImage}
                      alt="Selected"
                      style={{
                        maxWidth: "100%",
                        maxHeight: "100%",
                        objectFit: "contain",
                      }}
                    />
                  </Box>
                )}
                <Box mb={2} height="35%" overflow="auto">
                  <ReactMarkdown>{markdownText}</ReactMarkdown>
                </Box>
                <Box height="35%" overflow="auto">
                  <SyntaxHighlighter language="javascript" style={docco}>
                    {codeText}
                  </SyntaxHighlighter>
                </Box>
              </Box>
            </Grid>
          </Grid>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => handleApiCall("reseeandwrite")}>
            再識別寫生成程式
          </Button>
          <Button onClick={() => handleApiCall("rewrite")}>
            再生成一次程式
          </Button>
          <Button onClick={() => handleApiCall("copycode")}>
            複製目前程式
          </Button>
          <Button onClick={() => setReDoDialogOpen(false)}>關閉</Button>
        </DialogActions>
      </Dialog>
    </ThemeProvider>
  );
}

export default ChatPage;
