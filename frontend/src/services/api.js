import axios from "axios";

const api = axios.create({
  baseURL: "https://192.168.1.234:35000", // 后端服务地址
});

export default api;
