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
  Chip,
} from "@mui/material";

import { DataGrid } from "@mui/x-data-grid";
import { ThemeProvider, createTheme, styled } from "@mui/material/styles";
import {
  Snackbar,
  Alert,
  ToggleButton,
  ToggleButtonGroup,
} from "@mui/material";
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
  Sync as SyncIcon,
  ExitToApp as ExitToAppIcon,
  NavigateBefore as NavigateBeforeIcon,
  NavigateNext as NavigateNextIcon,
  Edit as EditIcon,
  CheckCircle as CheckCircleIcon,
  HelpOutline as HelpOutlineIcon,
} from "@mui/icons-material";

import { Light as SyntaxHighlighter } from "react-syntax-highlighter";
import { dracula, prism } from "react-syntax-highlighter/dist/esm/styles/prism";
import docco from "react-syntax-highlighter/dist/esm/styles/hljs/docco";

//import jsx from "react-syntax-highlighter/dist/esm/languages/prism/jsx";
import js from "react-syntax-highlighter/dist/esm/languages/hljs/javascript";
import html from "react-syntax-highlighter/dist/esm/languages/hljs/xml";
import css from "react-syntax-highlighter/dist/esm/languages/hljs/css";

import ReactMarkdown from "react-markdown";
import { jwtDecode } from "jwt-decode";
import api from "../services/api";

//import ImageDialog from "./ImageDialog";

//SyntaxHighlighter.registerLanguage("jsx", jsx);
SyntaxHighlighter.registerLanguage("javascript", js);
SyntaxHighlighter.registerLanguage("html", html);
SyntaxHighlighter.registerLanguage("css", css);

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

const MessageBubble = styled(Box, {
  shouldForwardProp: (prop) => prop !== "isUser",
})(({ theme, isUser }) => ({
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

const BubbleContent = styled(Paper, {
  shouldForwardProp: (prop) => prop !== "isUser",
})(({ theme, isUser }) => ({
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

const UserName = styled(Typography, {
  shouldForwardProp: (prop) => prop !== "isUser",
})(({ theme, isUser }) => ({
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

const ClipArea = styled(Box)(({ theme }) => ({
  display: "flex",
  flexWrap: "wrap",
  padding: theme.spacing(1),
  gap: theme.spacing(1),
  borderBottom: `1px solid ${theme.palette.divider}`,
}));

// 自定義樣式的 ToggleButton
const StyledToggleButton = styled(ToggleButton)(({ theme }) => ({
  marginLeft: theme.spacing(2),
  "&.Mui-selected": {
    backgroundColor: theme.palette.primary.main,
    color: theme.palette.primary.contrastText,
    "&:hover": {
      backgroundColor: theme.palette.primary.main,
    },
  },
  "&:not(.Mui-selected)": {
    borderColor: theme.palette.primary.main,
    color: theme.palette.primary.dark,
  },
}));

function ChatPage({ token, engineer, setToken }) {
  const [darkMode, setDarkMode] = useState(false);
  const [code, setCode] = useState("// Your React code here");
  const [codeDialogOpen, setCodeDialogOpen] = useState(false);
  const [conversations, setConversations] = useState([]);
  const [currentConversationId, setCurrentConversationId] = useState(0);
  const [showConversationList, setShowConversationList] = useState(true);

  const [snackbarOpen, setSnackbarOpen] = useState(false);
  const [snackbarMessage, setSnackbarMessage] = useState("");
  const [snackbarSeverity, setSnackbarSeverity] = useState("success");

  // State for dialogs
  const [projectDialogOpen, setProjectDialogOpen] = useState(false);
  const [switchProjectDialogOpen, setSwitchProjectDialogOpen] = useState(false);
  const [switchFunctionDialogOpen, setSwitchFunctionDialogOpen] =
    useState(false);

  const [reDoDialogOpen, setReDoDialogOpen] = useState(false);

  const [versionInfo, setVersionInfo] = useState({
    current: 0,
    total: 0,
    versions: [],
  });

  const [thumbnails, setThumbnails] = useState([]);
  const [selectedImage, setSelectedImage] = useState(null);
  const [markdownText, setMarkdownText] = useState("");
  const [codeText, setCodeText] = useState("");
  const [selectedFilename, setSelectedFilename] = useState(null);

  // Project data
  const [projectId, setProjectId] = useState("prj01");
  const [projectDescription, setProjectDescription] = useState("預設專案");
  const [projectMode, setProjectMode] = useState("Basic");

  // Feature data
  const [appName, setAppName] = useState("01_Report");
  const [appDescription, setAppDescription] = useState("報表");
  const [funcDescription, setFuncDescription] = useState("預設子報表");
  const [funcFileName, setFuncFileName] = useState("sub_report1.html");

  const [currentProject, setCurrentProject] = useState("");
  const [projects, setProjects] = useState([
    "Project A",
    "Project B",
    "Project C",
  ]); // Placeholder project list

  const [clips, setClips] = useState([
    // 可以添加更多初始 clip
  ]);
  const [selectedClip, setSelectedClip] = useState(null);
  const [clipDialogOpen, setClipDialogOpen] = useState(false);

  const [isEditingCurrentVersion, setIsEditingCurrentVersion] = useState(false);

  const [functionData, setFunctionData] = useState([]);
  const [functionDialogOpen, setFunctionDialogOpen] = useState(false);

  const [helpDialogOpen, setHelpDialogOpen] = useState(false);

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
        //console.log(error);
        handleApiError(error);
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
      //console.log(error);
      handleApiError(error);
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
          setTaskId(null);
          clearInterval(intervalId);
          fetchVersionInfo();
        }
      }, 500);

      return () => clearInterval(intervalId);
    }

    fetchMessages();
  }, [token, taskId, prevStatus]);

  useEffect(() => {
    getInfo();
    fetchVersionInfo();
  }, [assistantName, configStatus, token]);

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  useEffect(() => {
    if (reDoDialogOpen) {
      fetchThumbnails();
    }
  }, [reDoDialogOpen]);

  const handleOpenHelpDialog = () => {
    setHelpDialogOpen(true);
  };

  const handleCloseHelpDialog = () => {
    setHelpDialogOpen(false);
  };

  const handleFetchFunctions = async () => {
    try {
      const formdata = new FormData();
      formdata.append("prj_id", projectId);
      const response = await api.post("/functions", formdata, {
        headers: { Authorization: `Bearer ${token}` },
      });
      // 為每個項目添加一個唯一的 id
      const dataWithIds = response.data.functions.map((item, index) => ({
        ...item,
        id: index + 1,
      }));
      setFunctionData(dataWithIds);
      setFunctionDialogOpen(true);
    } catch (error) {
      handleApiError(error);
    }
  };

  const handleFunctionSelect = (params) => {
    const selectedFunction = params.row;
    setAppName(selectedFunction.APP_NAME);
    setAppDescription(selectedFunction.APP_DESC);
    setFuncDescription(selectedFunction.FUNC_DESC);
    setFuncFileName(selectedFunction.FUNC_FILE);
    setFunctionDialogOpen(false);
  };

  const columns = [
    { field: "id", headerName: "ID", width: 70 },
    { field: "APP_NAME", headerName: "應用代號", width: 130 },
    { field: "APP_DESC", headerName: "應用描述", width: 200 },
    { field: "FUNC_DESC", headerName: "功能描述", width: 200 },
    { field: "FUNC_FILE", headerName: "功能檔名", width: 150 },
  ];

  const fetchVersionInfo = async () => {
    try {
      const response = await api.post(
        "/versions/func",
        {},
        {
          headers: { Authorization: `Bearer ${token}` },
        },
      );

      const versions = JSON.parse(response.data.versions);
      setVersionInfo({
        current: versions[versions.length - 1],
        total: versions.length,
        versions: versions,
      });
    } catch (error) {
      handleApiError(error);
    }
  };

  const handleVersionChange = async (newVersion) => {
    try {
      const formData = new FormData();
      formData.append("version", newVersion);
      await api.post("/version/func/switch", formData, {
        headers: { Authorization: `Bearer ${token}` },
      });
      setVersionInfo((prev) => ({ ...prev, current: newVersion }));
      fetchMessages(); // 重新加載消息
    } catch (error) {
      handleApiError(error);
    }
  };

  const handlePreviousVersion = () => {
    const currentIndex = versionInfo.versions.indexOf(versionInfo.current);
    if (currentIndex > 0) {
      handleVersionChange(versionInfo.versions[currentIndex - 1]);
    }
  };

  const handleNextVersion = () => {
    const currentIndex = versionInfo.versions.indexOf(versionInfo.current);
    if (currentIndex < versionInfo.versions.length - 1) {
      handleVersionChange(versionInfo.versions[currentIndex + 1]);
    }
  };

  const handleEditCurrentVersionToggle = () => {
    setIsEditingCurrentVersion(!isEditingCurrentVersion);
    // ... (可以添加更多邏輯)
  };

  const handleClipClick = (clip) => {
    setSelectedClip(clip);
    setClipDialogOpen(true);
  };

  const handleClipDelete = (clipToDelete) => {
    setClips(clips.filter((clip) => clip.id !== clipToDelete.id));
  };

  const handleClipDialogClose = () => {
    setClipDialogOpen(false);
    setSelectedClip(null);
  };

  const handleLogout = () => {
    setToken(null);
    // 不需要使用 navigate，因為 App.js 會根據 token 的值來渲染不同的組件
  };

  const handleApiError = (error) => {
    if (error.response && error.response.status === 401) {
      showMsg(false, "您的會話已過期，請重新登錄");
      setTimeout(() => {
        handleLogout();
      }, 3000);
    } else {
      console.error("API error:", error);
      showMsg(false, "發生錯誤，請稍後再試");
    }
  };

  const getInfo = async () => {
    try {
      const response = await api.get("/info", {
        headers: { Authorization: `Bearer ${token}` },
      });
      setAssistantName(engineer.EMP_NAME);
      //setAssistantName(response.data.name);
      let config = response.data.config;
      let configStatus = `專案: ${config["PROJ_DESC"]} (${config["PROJ_ID"]} ) > 應用: ${config["APP_DESC"]} > 功能: ${config["FUNC_DESC"]} ( ${config["FUNC_FILE"]} )`;

      setAppName(config["APP_NAME"] || "");
      setAppDescription(config["APP_DESC"] || "");
      setFuncDescription(config["FUNC_DESC"] || "");
      setFuncFileName(config["FUNC_FILE"] || "");

      setConfigStatus(configStatus);
    } catch (error) {
      handleApiError(error);
      //console.log(error);
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
      setCurrentProject("");

      setSwitchProjectDialogOpen(true);
    } catch (error) {
      handleApiError(error);
      //console.log(error);
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
    cleanSend();
  };

  const handleRedoAction = async (mode) => {
    try {
      setClips([]);

      let items = [];
      if (mode == 2) {
        items.push({
          id: 1,
          label: "圖片",
          type: 0,
          content: `data:image/jpeg;base64,${selectedImage}`,
        });
      } else if (mode == 1) {
        items.push({
          id: 2,
          label: "描述",
          type: 1,
          content: markdownText,
        });
      } else {
        items.push({
          id: 2,
          label: "描述",
          type: 1,
          content: markdownText,
        });
        items.push({
          id: 3,
          label: "程式",
          type: 2,
          content: codeText,
        });
      }

      setClips(items);
      /*

      const formData = new FormData();
      formData.append("filename", selectedFilename);
      formData.append("conversation_id", currentConversationId);

      let api_name = "/redo/copycode";
      if (mode == 1) {
        api_name = "/redo/rewrite";
      } else if (mode == 2) {
        api_name = "/redo/reseeandwrite";
      }

      const response = await api.post(api_name, formData, {
        headers: {
          Authorization: `Bearer ${token}`,
        },
      });

      if (response.data.task_id) {
        setTaskId(response.data.task_id);
      } */

      setReDoDialogOpen(false);

      //return response;
    } catch (error) {
      handleApiError(error);
      throw error;
    }
  };

  // 新增的函數
  const checkClipsMode = () => {
    if (clips.some((clip) => clip.type === 2)) {
      // code
      return 0;
    } else if (clips.some((clip) => clip.type === 0)) {
      // image
      return 2;
    } else {
      return 1;
    }
  };

  const handleApiCall = async (msg, images) => {
    try {
      const formData = new FormData();
      formData.append("message", msg);
      formData.append("conversation_id", currentConversationId);

      let api_name = "/redo/modifycode";

      if (clips.length > 0) {
        formData.append("filename", selectedFilename);

        let mode = checkClipsMode();
        api_name = "/redo/modifycode";

        if (mode == 1) {
          api_name = "/redo/rewrite";
        } else if (mode == 2) {
          api_name = "/redo/reseeandwrite";
        }
      } else if (isEditingCurrentVersion) {
        api_name = "/redo/editcode";
      } else {
        api_name = "/message";
        if (images instanceof File) {
          api_name = "/message_images";
          formData.append("images", images);
        }
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
    } catch (error) {
      handleApiError(error);
      throw error;
    }
  };

  const cleanSend = async () => {
    setInput("");
    setImageFiles([]);
    setUploadedImages([]);
    setFileInputKey(Date.now());
    setClips([]);
  };

  const handleSend = async () => {
    if (!input.trim()) return;
    if (taskId != null) {
      showMsg(false, "尚有命令未完成, 請等待");
    }

    if (currentConversationId == 0) {
      showMsg(false, "請先建立需求!");
    }

    setMessages([...messages, { sender: "user", text: input, name: userName }]);

    try {
      const response = await handleApiCall(input, imageFiles);

      cleanSend();

      setMessages((prevMessages) => [
        ...prevMessages,
        { sender: "assistant", text: response.data.message },
      ]);
    } catch (error) {
      setMessages((prevMessages) => [
        ...prevMessages,
        { sender: "assistant", text: error.toString() },
      ]);
      handleApiError(error);
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
      //console.log(error);
      handleApiError(error);
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
      handleApiError(error);
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

      fetchVersionInfo();

      setMessages((prevMessages) => [
        ...prevMessages,
        { sender: "assistant", text: "切換成功" },
      ]);
    } catch (error) {
      setMessages((prevMessages) => [
        ...prevMessages,
        { sender: "assistant", text: "切換失敗-" + error.toString() },
      ]);
      handleApiError(error);
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

      const rep1 = await handleApiCall(input1, null);
      console.log("switch app name:", rep1);

      const rep2 = await handleApiCall(input2, null);
      console.log("switch app desc:", rep2);

      const rep3 = await handleApiCall(input3, null);
      console.log("switch func desc:", rep3);

      const rep4 = await handleApiCall(input4, null);
      console.log("switch func name:", rep4);

      fetchVersionInfo();

      setMessages((prevMessages) => [
        ...prevMessages,
        { sender: "assistant", text: "切換成功" },
      ]);
    } catch (error) {
      setMessages((prevMessages) => [
        ...prevMessages,
        { sender: "assistant", text: "切換失敗-" + error.toString() },
      ]);
      handleApiError(error);
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

      const response = await api.get("/getcode", {
        headers: { Authorization: `Bearer ${token}` },
      });

      setCode(response.data.codeText);

      setMessages((prevMessages) => [
        ...prevMessages,
        { sender: "assistant", text: "讀取程式碼成功" },
      ]);
    } catch (error) {
      setMessages((prevMessages) => [
        ...prevMessages,
        { sender: "assistant", text: "讀取程式碼失敗-" + error.toString() },
      ]);
      handleApiError(error);
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

  const showMsg = (success, msg) => {
    setSnackbarMessage(msg);
    if (success) {
      setSnackbarSeverity("success");
    } else {
      setSnackbarSeverity("error");
    }
    setSnackbarOpen(true);
  };

  const handleReload = async () => {
    try {
      const response = await api.post(
        "/reload_employees",
        {},
        {
          headers: { Authorization: `Bearer ${token}` },
        },
      );
      console.log(response.data);
      showMsg(true, "重新載入AI員工成功");
    } catch (error) {
      showMsg(false, "重新載入AI員工失敗");
    }
  };

  const handleCodeCopy = async () => {
    if (navigator.clipboard && window.isSecureContext) {
      // 使用新的非同步 Clipboard API
      navigator.clipboard
        .writeText(code)
        .then(() => {
          console.log("copy new");
          showMsg(true, "程式碼已成功複製到剪貼板");
        })
        .catch((err) => {
          showMsg(false, "複製失敗：" + err.message);
        });
    } else {
      // 使用傳統方法
      let textArea = document.createElement("textarea");
      textArea.value = code;
      textArea.style.position = "fixed"; // 避免滾動到底部
      document.body.appendChild(textArea);
      textArea.focus();
      textArea.select();
      try {
        const successful = document.execCommand("copy");
        console.log(successful);
        if (successful) {
          showMsg(true, "程式碼已複製到剪貼板");
        } else {
          showMsg(false, "複製失敗，請手動複製");
        }
        setSnackbarOpen(true);
      } catch (err) {
        showMsg(false, "複製失敗：" + err.message);
      }
      document.body.removeChild(textArea);
    }
  };

  const handleSnackbarClose = (event, reason) => {
    /* if (reason === "clickaway") {
      return;
    }*/
    setSnackbarOpen(false);
  };

  const handleCodeDownload = async () => {
    try {
      const response = await api.get("/download_code", {
        headers: { Authorization: `Bearer ${token}` },
        responseType: "blob", // 指定響應類型為 blob
      });

      //if (!response.ok) throw new Error("Download failed");

      // Get the filename from the Content-Disposition header
      const contentDisposition = response.headers["content-disposition"];
      let filename = "download";
      if (contentDisposition) {
        const filenameMatch = contentDisposition.match(/filename="?(.+)"?/i);
        if (filenameMatch.length === 2) filename = filenameMatch[1];
      }

      // 創建 Blob 對象
      const blob = new Blob([response.data], {
        type: "application/octet-stream",
      });

      // 創建臨時 URL
      const url = window.URL.createObjectURL(blob);

      // 創建一個臨時的 <a> 元素來觸發下載
      const link = document.createElement("a");
      link.href = url;
      link.setAttribute("download", filename);
      document.body.appendChild(link);
      link.click();

      // 清理
      document.body.removeChild(link);
      window.URL.revokeObjectURL(url);
    } catch (error) {
      //console.log("down code error :");
      //console.log(error);
      handleApiError(error);
    }
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
      //console.error("Error fetching thumbnails:", error);
      handleApiError(error);
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
      //console.error("Error fetching image details:", error);
      handleApiError(error);
    }
  };

  const renderClipContent = (clip) => {
    switch (clip.type) {
      case 0: // Image
        return (
          <Box
            display="flex"
            justifyContent="center"
            alignItems="center"
            height="100%"
          >
            <img
              src={clip.content}
              alt="Clip content"
              style={{
                maxWidth: "100%",
                maxHeight: "100%",
                objectFit: "contain",
              }}
            />
          </Box>
        );
      case 1: // Markdown
        return (
          <Paper
            elevation={3}
            sx={{ p: 2, maxHeight: "60vh", overflow: "auto" }}
          >
            <ReactMarkdown>{clip.content}</ReactMarkdown>
          </Paper>
        );
      case 2: // Code
        return (
          <Paper
            elevation={3}
            sx={{ p: 2, maxHeight: "60vh", overflow: "auto" }}
          >
            <SyntaxHighlighter language="html" style={docco}>
              {clip.content}
            </SyntaxHighlighter>
          </Paper>
        );
      default:
        return <Typography>Unsupported clip type</Typography>;
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
            <IconButton color="inherit" onClick={handleReload} size="small">
              <SyncIcon fontSize="small" />
            </IconButton>
            <IconButton
              color="inherit"
              onClick={handleOpenHelpDialog}
              size="small"
            >
              <HelpOutlineIcon fontSize="small" />
            </IconButton>

            <IconButton color="inherit" onClick={() => setDarkMode(!darkMode)}>
              {darkMode ? <Brightness7Icon /> : <Brightness4Icon />}
            </IconButton>

            <IconButton color="inherit" onClick={handleLogout} size="small">
              <ExitToAppIcon fontSize="small" />
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
                    {conversations.map((conversation, idx) => (
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
                        <ListItemText primary={`需求: ${idx + 1}`} />
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
                    <Box
                      sx={{
                        display: "flex",
                        gap: 2,
                        p: 2,
                        alignItems: "center",
                      }}
                    >
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
                      <StyledToggleButton
                        value="check"
                        selected={isEditingCurrentVersion}
                        onChange={handleEditCurrentVersionToggle}
                        sx={{
                          height: 36, // 確保與其他按鈕高度一致
                          px: 2, // 增加水平內邊距
                        }}
                      >
                        {isEditingCurrentVersion && (
                          <CheckCircleIcon sx={{ mr: 1 }} />
                        )}
                        修改目前版本
                      </StyledToggleButton>
                    </Box>
                    <Box sx={{ display: "flex", alignItems: "center" }}>
                      <IconButton
                        onClick={handlePreviousVersion}
                        disabled={
                          versionInfo.versions.indexOf(versionInfo.current) ===
                          0
                        }
                      >
                        <NavigateBeforeIcon />
                      </IconButton>
                      <Typography variant="body2" sx={{ mx: 1 }}>
                        版本:{" "}
                        {versionInfo.versions.indexOf(versionInfo.current) + 1}/
                        {versionInfo.total}
                      </Typography>
                      <IconButton
                        onClick={handleNextVersion}
                        disabled={
                          versionInfo.versions.indexOf(versionInfo.current) ===
                          versionInfo.total - 1
                        }
                      >
                        <NavigateNextIcon />
                      </IconButton>
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
                  </Grid>
                </Grid>

                <ClipArea>
                  {clips.map((clip) => (
                    <Chip
                      key={clip.id}
                      label={clip.label}
                      onClick={() => handleClipClick(clip)}
                      onDelete={() => handleClipDelete(clip)}
                      sx={{ margin: 0.5 }}
                    />
                  ))}
                </ClipArea>

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
            language="html"
            style={darkMode ? dracula : prism}
            customStyle={{ height: "400px", margin: 0 }}
          >
            {code}
          </SyntaxHighlighter>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => handleCodeCopy()}>複製</Button>
          <Button onClick={() => handleCodeDownload()}>下載</Button>
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
              displayEmpty
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
          <Button onClick={handleFetchFunctions}>選擇原有功能</Button>

          <Button onClick={handleSwitchFunction}>切換</Button>
        </DialogActions>
      </Dialog>
      {/* Function Selection Dialog */}
      <Dialog
        open={functionDialogOpen}
        onClose={() => setFunctionDialogOpen(false)}
        maxWidth="lg"
        fullWidth
      >
        <DialogTitle>選擇功能</DialogTitle>
        <DialogContent>
          <div style={{ height: 400, width: "100%" }}>
            <DataGrid
              rows={functionData}
              columns={columns}
              pageSize={5}
              rowsPerPageOptions={[5]}
              onRowDoubleClick={handleFunctionSelect}
            />
          </div>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setFunctionDialogOpen(false)}>關閉</Button>
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
          再做一次
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
                <Paper elevation={3} sx={{ mb: 2, p: 2 }}>
                  <Typography variant="h6" gutterBottom>
                    選擇圖片
                  </Typography>
                  {selectedImage && (
                    <Box
                      mb={2}
                      display="flex"
                      justifyContent="center"
                      alignItems="center"
                      height="90%"
                    >
                      <img
                        src={`data:image/jpeg;base64,${selectedImage}`}
                        alt="Selected"
                        style={{
                          maxWidth: "100%",
                          maxHeight: "100%",
                          objectFit: "contain",
                        }}
                      />
                    </Box>
                  )}
                </Paper>
                <Paper
                  elevation={3}
                  sx={{ mb: 2, p: 2, flexGrow: 1, overflow: "auto" }}
                >
                  <Typography variant="h6" gutterBottom>
                    對應說明
                  </Typography>
                  <ReactMarkdown>{markdownText}</ReactMarkdown>
                </Paper>
                <Paper
                  elevation={3}
                  sx={{ p: 2, flexGrow: 1, overflow: "auto" }}
                >
                  <Typography variant="h6" gutterBottom>
                    對應程式碼
                  </Typography>
                  <SyntaxHighlighter language="html" style={docco}>
                    {codeText}
                  </SyntaxHighlighter>
                </Paper>
              </Box>
            </Grid>
          </Grid>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => handleRedoAction(2)}>再識別及生成程式</Button>
          <Button onClick={() => handleRedoAction(1)}>再生成一次程式</Button>
          <Button onClick={() => handleRedoAction(0)}>修改目前程式</Button>
          <Button onClick={() => setReDoDialogOpen(false)}>關閉</Button>
        </DialogActions>
      </Dialog>
      {/* Clip Content Dialog */}
      <Dialog
        open={clipDialogOpen}
        onClose={handleClipDialogClose}
        maxWidth="md"
        fullWidth
      >
        <DialogTitle>
          {selectedClip?.label}
          <IconButton
            aria-label="close"
            onClick={handleClipDialogClose}
            sx={{ position: "absolute", right: 8, top: 8 }}
          >
            <CloseIcon />
          </IconButton>
        </DialogTitle>
        <DialogContent>
          <Box sx={{ mt: 2 }}>
            {selectedClip && renderClipContent(selectedClip)}
          </Box>
        </DialogContent>
      </Dialog>
      <Dialog
        open={helpDialogOpen}
        onClose={handleCloseHelpDialog}
        maxWidth="md"
        fullWidth
      >
        <DialogTitle>功能說明</DialogTitle>
        <DialogContent>
          <Typography variant="body1" component="div">
            <ol>
              <li>
                <strong>新需求:</strong> 建立一個需求來啟動對話
              </li>
              <li>
                <strong>建立專案:</strong> 建立一個新專案來放程式
              </li>
              <li>
                <strong>切換專案:</strong> 選擇原有的專案來放程式
              </li>
              <li>
                <strong>切換功能:</strong> 建立或選擇已有的功能, 放生成的程式
              </li>
              <li>
                <strong>再做一次:</strong>{" "}
                從歷史的圖庫中選擇圖片,重新生成一次或以該程式為基礎修改(適合不用上傳圖片使用)
              </li>
              <li>
                <strong>修改目前版本:</strong> 按下(出現勾) ,
                依輸入框內容修改目前的程式(適合已生成程式,但部分功能無法正常運作)
              </li>
              <li>
                <strong>上傳圖片:</strong>{" "}
                上傳1張圖片,並輸入用途,依據圖片自動生成程式
              </li>
              <li>
                <strong>版本:</strong> 每個功能最多保持10版,
                可以隨時切換,並以該版本進行修改
              </li>
            </ol>
          </Typography>
        </DialogContent>
        <DialogActions>
          <Button onClick={handleCloseHelpDialog}>關閉</Button>
        </DialogActions>
      </Dialog>
      <Snackbar
        anchorOrigin={{
          vertical: "bottom",
          horizontal: "center",
        }}
        open={snackbarOpen}
        autoHideDuration={2000}
        onClose={handleSnackbarClose}
      >
        <Alert
          onClose={handleSnackbarClose}
          severity={snackbarSeverity}
          sx={{ width: "100%" }}
        >
          {snackbarMessage}
        </Alert>
      </Snackbar>
    </ThemeProvider>
  );
}

export default ChatPage;
