import { FC, ReactNode } from 'react';
import styles from './Button.module.scss';
import classNames from 'classnames';

interface ButtonProps {
    onClick?: (e: React.MouseEvent<HTMLButtonElement>) => void;
    children?: ReactNode;
    variant?: 'active' | 'danger' | 'underline' | 'text' | 'menu' | 'inverted' | string;
    className?: string;
    type?: 'button' | 'submit' | 'reset';
    disabled?: boolean;
}

export const Button: FC<ButtonProps> = ({
                                            onClick,
                                            children,
                                            className,
                                            variant = 'default',
                                            disabled = false,
                                            type = 'button',
                                        }) => {
    return (
        <button
            onClick={onClick}
            className={classNames(styles.button, styles[variant], className)}
            disabled={disabled}
            type={type}
        >
            {children}
        </button>
    );
};
