import axios, {
    AxiosInstance,
} from 'axios';
import {refreshResponse} from "~/Api/Auth/Types/ResponseTypes.ts";

/**
 * API Handler to make all requests through Axios instance
 */
class ApiHandler {
    private axiosInstance: AxiosInstance;

    constructor(baseURL?: string) {
        this.axiosInstance = axios.create({
            baseURL: baseURL,
            // headers: {
            //     'Content-Type': 'application/json',
            // },
        });
        this.axiosInstance.interceptors.request.use(
            (config) => {
                const token = localStorage.getItem('access_token');
                if (token) {
                    config.headers.Authorization = `Bearer ${token}`;
                }
                return config;
            },
            (error) => {
                return Promise.reject(error);
            }
        );
        this.axiosInstance.interceptors.response.use(
            (response) => response,
            async (error) => {
                const originalRequest = error.config;

                if (error.response.status === 409 && !originalRequest._retry) {
                    originalRequest._retry = true;
                    try {
                        const refreshToken = localStorage.getItem("refresh_token");
                        const response = await axios.post<refreshResponse>(
                            `http://localhost:8000/admin/auth/token/refresh?refresh_token=${refreshToken}`,
                        );
                        localStorage.setItem("access_token", response.data.access_token);
                        originalRequest.headers.Authorization = `Bearer ${response.data.access_token}`;
                        return await axios(originalRequest);
                    } catch (error) {
                        localStorage.removeItem("access_token");
                        localStorage.removeItem("refresh_token");
                        window.location.href = "/";
                        console.log(error)
                    }
                } else {
                    // localStorage.removeItem("access_token");
                    // localStorage.removeItem("refresh_token");
                    // window.location.href = "/";
                }

                return Promise.reject(error);
            }
        );
    }

    public get = <T>(url: string, config = {}) => {
        return this.axiosInstance.get<T>(url, config);
    };

    public post = <T>(url: string, data: any, config = {}) => {
        return this.axiosInstance.post<T>(url, data, config);
    };

    public put = <T>(url: string, data: any, config = {}) => {
        return this.axiosInstance.put<T>(url, data, config);
    };
    public patch = <T>(url: string, data: any, config = {}) => {
        return this.axiosInstance.patch<T>(url, data, config);
    };

    public delete = <T>(url: string, config = {}) => {
        return this.axiosInstance.delete<T>(url, config);
    };
}

const apiHandler = new ApiHandler(import.meta.env.VITE_API_URL || "http://localhost:8080");


export default apiHandler;
