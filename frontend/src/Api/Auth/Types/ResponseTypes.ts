export interface LoginData {
    email: string;
    password: string;
}

export interface Token {
    access_token: string;
    token_type: string;
}

export interface BaseResponse<T> {
    status: string;
    data: T;
    // result: Token;
}

export interface Token {
    access_token: string;
    refresh_token: string;
    token_type: string;
}

export interface refreshResponse {
    access_token: string;
}