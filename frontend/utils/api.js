// frontend/utils/api.js
import axios from 'axios';

// 如果在外部没有定义 NEXT_PUBLIC_API_BASE_URL，则默认用 'http://localhost:5000'
export const baseURL =
  process.env.NEXT_PUBLIC_API_BASE_URL || 'http://localhost:5000';

// 创建一个 axios 实例，以后所有请求都用这个实例
export const apiClient = axios.create({
  baseURL,
  // 可以在此添加通用的 headers / 超时等配置
});
