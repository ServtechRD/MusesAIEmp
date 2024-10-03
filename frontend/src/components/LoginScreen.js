import React, { useState, useEffect } from "react";
import {
  Box,
  TextField,
  Button,
  Typography,
  Container,
  CssBaseline,
  Alert,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  Select,
  MenuItem,
  FormControl,
  InputLabel,
} from "@mui/material";
import { createTheme, ThemeProvider } from "@mui/material/styles";

import api from "../services/api";

const theme = createTheme();

export default function LoginPage({ setToken, setEngineer, engineer }) {
  const [username, setUsername] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState("");
  const [success, setSuccess] = useState("");
  const [openRegister, setOpenRegister] = useState(false);
  const [registerUsername, setRegisterUsername] = useState("");
  const [registerPassword, setRegisterPassword] = useState("");

  const [engineerList, setEngineerList] = useState([]);

  const [version, setVersion] = useState("0.5.1");

  useEffect(() => {
    fetchEngineerList();
  }, []);

  const fetchEngineerList = async () => {
    try {
      // 替換成您的實際API端點
      const response = await api.get("/employees");
      const empList = Object.values(response.data);
      setEngineerList(empList);
    } catch (error) {
      console.error("Error fetching options:", error);
    }
  };

  const handleSubmit = async (event) => {
    event.preventDefault();
    // 這裡模擬登入邏輯
    /*if (username === 'admin' && password === 'password') {
      console.log('Login successful');
      setError('');
      // 這裡可以添加成功登入後的邏輯，比如重定向到主頁
    } else {
      setError('登入失敗。請檢查您的帳號和密碼。');
    }*/

    try {
      let employee = engineer.EMP_ID;
      const response = await api.post("/login", {
        username,
        password,
        employee,
      });
      setToken(response.data.access_token);
    } catch (error) {
      setError("代號或密碼錯誤");
    }
  };

  const handleRegister = async () => {
    console.log("Register:", registerUsername, registerPassword);
    setOpenRegister(false);
    // 這裡添加實際的註冊邏輯
    try {
      let username = registerUsername;
      let password = registerPassword;
      const response = await api.post("/register", { username, password });
      setError("");
      setSuccess("註冊成功, 請登入");
    } catch (error) {
      setError("註冊失敗, 使用者代碼可能已存在");
    }
  };

  const handleEngineerChange = (event) => {
    console.log(engineerList[event.target.value]);
    setEngineer(engineerList[event.target.value]);
  };

  return (
    <ThemeProvider theme={theme}>
      <Container component="main" maxWidth="xs">
        <CssBaseline />
        <Box
          sx={{
            marginTop: 8,
            display: "flex",
            flexDirection: "column",
            alignItems: "center",
          }}
        >
          <Box
            component="img"
            sx={{
              height: 150,
              mb: 2,
            }}
            alt="A001 logo"
            src="/static/assets/images/logo.png"
          />
          <Typography component="h1" variant="h5">
            登入
          </Typography>
          {error && (
            <Alert severity="error" sx={{ mt: 2, width: "100%" }}>
              {error}
            </Alert>
          )}
          {success && (
            <Alert severity="success" sx={{ mt: 2, width: "100%" }}>
              {success}
            </Alert>
          )}
          <Box
            component="form"
            onSubmit={handleSubmit}
            noValidate
            sx={{ mt: 1 }}
          >
            <TextField
              margin="normal"
              required
              fullWidth
              id="username"
              label="帳號"
              name="username"
              autoComplete="username"
              autoFocus
              value={username}
              onChange={(e) => setUsername(e.target.value)}
            />
            <TextField
              margin="normal"
              required
              fullWidth
              name="password"
              label="密碼"
              type="password"
              id="password"
              autoComplete="current-password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
            />

            <FormControl fullWidth margin="normal">
              <InputLabel id="selectLabelEngType">工程師</InputLabel>
              <Select
                labelId="selectLabelEngType"
                value={engineer.EMP_ID}
                label="工程師"
                id="selectEngType"
                onChange={handleEngineerChange}
              >
                {engineerList.map((person, index) => (
                  <MenuItem key={person.EMP_ID} value={index}>
                    {person.EMP_DESC + "(" + person.EMP_NAME + ")"}
                  </MenuItem>
                ))}
              </Select>
            </FormControl>

            <Button
              type="submit"
              fullWidth
              variant="contained"
              sx={{ mt: 3, mb: 2 }}
            >
              登入
            </Button>
          </Box>
          <Button
            fullWidth
            variant="outlined"
            sx={{ mt: 1, mb: 2 }}
            onClick={() => setOpenRegister(true)}
          >
            註冊新帳號
          </Button>
        </Box>
        <Typography
          variant="body2"
          color="text.secondary"
          align="center"
          sx={{ mt: 5 }}
        >
          "版本 :" {version}
        </Typography>
      </Container>

      <Dialog open={openRegister} onClose={() => setOpenRegister(false)}>
        <DialogTitle>註冊新帳號</DialogTitle>
        <DialogContent>
          <TextField
            autoFocus
            margin="dense"
            id="register-username"
            label="帳號"
            type="text"
            fullWidth
            variant="standard"
            value={registerUsername}
            onChange={(e) => setRegisterUsername(e.target.value)}
          />
          <TextField
            margin="dense"
            id="register-password"
            label="密碼"
            type="password"
            fullWidth
            variant="standard"
            value={registerPassword}
            onChange={(e) => setRegisterPassword(e.target.value)}
          />
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setOpenRegister(false)}>取消</Button>
          <Button onClick={handleRegister}>註冊</Button>
        </DialogActions>
      </Dialog>
    </ThemeProvider>
  );
}
