import React from 'react';
import { Field, ErrorMessage } from 'formik';
import styles from './InputField.module.scss';

interface InputFieldProps {
    type?: string;
    name: string;
    label: string;
    placeholder?: string;
    className?: string;
    as?: 'input' | 'select';
    children?: React.ReactNode;
}

const InputField: React.FC<InputFieldProps> = ({
                                                   type = 'text',
                                                   name,
                                                   label,
                                                   placeholder,
                                                   className,
                                                   as = 'input',
                                                   children
                                               }) => {
    return (
        <div className={`${styles.formGroup} ${className ? className : ''}`}>
            <label htmlFor={name}>{label}</label>
            <Field
                as={as}
                type={type}
                name={name}
                id={name}
                className={styles.inputField}
                placeholder={placeholder}
                autoComplete="off"
            >
                {as === 'select' ? children : null}
            </Field>
            <ErrorMessage name={name} component="div" className={styles.errorMessage} />
        </div>
    );
};

export default InputField;
