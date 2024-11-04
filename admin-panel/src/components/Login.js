// src/components/Login.js
import React, { useState } from 'react';
import axios from '../axiosConfig'; // Ensure you're using your configured axios instance
import { Form, Input, Button } from 'antd';

function Login({ setAuthToken }) {
  const [loading, setLoading] = useState(false);

  const onFinish = async (values) => {
    setLoading(true);
    try {
      const response = await axios.post('/admin/api/auth/login', values);
      const token = response.data.access_token; // Get the access token from the response
      setAuthToken(token); // Update the auth token state
      localStorage.setItem('authToken', token); // Store the token in localStorage
    } catch (error) {
      console.error('Login failed:', error);
    }
    setLoading(false);
  };

  return (
    <Form onFinish={onFinish}>
      <Form.Item name="login" rules={[{ required: true }]}>
        <Input placeholder="Login" />
      </Form.Item>
      <Form.Item name="password" rules={[{ required: true }]}>
        <Input.Password placeholder="Password" />
      </Form.Item>
      <Button type="primary" htmlType="submit" loading={loading}>
        Log In
      </Button>
    </Form>
  );
}

export default Login;

// import axios from '../axiosConfig';
