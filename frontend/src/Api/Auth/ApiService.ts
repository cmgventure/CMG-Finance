import apiHandler from "../ApiHandler";
import {BaseResponse, LoginData, Token} from "./Types/ResponseTypes"

export const loginUser = async (
    data: LoginData,
) => {
    try {
        const response = await apiHandler.post<BaseResponse<Token>>('/admin/auth/login', data);
        if (response.status === 200) {
            const responseData = response.data ;
            if (responseData) {
                if (responseData.access_token && responseData.refresh_token) {
                    localStorage.setItem('access_token', responseData.access_token);
                    localStorage.setItem('refresh_token', responseData.refresh_token);
                    return { success: true, message: 'You were logged in successfully'};
                } else {
                    console.error('Error:', response);
                    return { success: false, message: "Response doesn'\t have tokens" };
                }
            } else {
                console.error('Error:', response);
                return { success: false, message: 'Something went wrong. Please try again later.' };
            }
        }
    } catch (error: any) {
        console.error('Error:', error.response.data.detail);
        return { success: false, message: error.response.data.detail };
    }
};