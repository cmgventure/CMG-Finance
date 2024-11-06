import React from 'react';
import styles from './LoginPage.module.scss';
import { Button } from "~/Components/Button";
import * as Yup from 'yup';
import { Form, Formik } from "formik";
import InputField from "~/Components/InputField/InputField";
import { useNavigate } from "react-router-dom";
import { loginUser } from "~/Api/Auth/ApiService.ts";
import {useDispatch} from "react-redux";
import {setIsAuth} from "~/Store/Reducers/AuthReducer.ts";
import {showToast} from "~/Utils/ShowToast.tsx";

const LoginPage: React.FC = () => {
    const validationSchema = Yup.object({
        email: Yup.string().email('Invalid email address').required('Email is required'),
        password: Yup.string().min(6, 'Password must be at least 6 characters').required('Password is required'),
    });
    const dispatch = useDispatch()
    const navigate = useNavigate();

    return (
        <div className={styles.loginPage}>
            <div className={styles.header}>Login to admin</div>
            <div className={styles.mainBlock}>
                <Formik
                    initialValues={{ email: '', password: '' }}
                    validationSchema={validationSchema}
                    onSubmit={async (values) => {
                        const result = await loginUser({ email: values.email, password: values.password });
                        if (result && result.success) {
                            dispatch(setIsAuth(true));
                            navigate('/admin/categories');
                        } else {
                            console.error('Login failed:', result.message);
                            showToast('error', 'Error', result.message);
                        }
                    }}
                >
                    {() => (
                        <Form>
                            <InputField
                                type="email"
                                name="email"
                                label="Email"
                                placeholder="Enter your email"
                            />
                            <InputField
                                type="password"
                                name="password"
                                label="Password"
                                placeholder="Enter your password"
                            />
                            <div>
                                <Button variant="active" className={styles.continueButton} type="submit">
                                    Continue
                                </Button>
                            </div>
                        </Form>
                    )}
                </Formik>
            </div>
        </div>
    );
};

export default LoginPage;
