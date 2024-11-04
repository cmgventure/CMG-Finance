// src/axiosConfig.js
import axios from 'axios';

const axiosInstance = axios.create({
  baseURL: 'http://localhost:8000', // Replace with your API base URL
});

// Add a request interceptor to include the auth token
axiosInstance.interceptors.request.use(
  (config) => {
    const token = localStorage.getItem('authToken');
    if (token) {
      config.headers['Authorization'] = `Bearer ${token}`;
    }
    return config;
  },
  (error) => Promise.reject(error)
);

export default axiosInstance;




// // src/axiosConfig.js
// import axios from 'axios';
//
// const axiosInstance = axios.create({
//   baseURL: 'http://localhost:8000', // Replace with your API base URL
// });
//
// // Optionally, add interceptors to attach the auth token
// axiosInstance.interceptors.request.use((config) => {
//   const token = localStorage.getItem('authToken'); // Or however you're storing it
//   if (token) {
//     config.headers.Authorization = `Bearer ${token}`;
//   }
//   return config;
// });
//
// export default axiosInstance;
