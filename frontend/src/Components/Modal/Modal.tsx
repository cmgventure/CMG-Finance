import { FC, PropsWithChildren} from 'react';
import styles from './Modal.module.scss';
import { createPortal } from 'react-dom';

interface IModalProps extends PropsWithChildren {
    showModal: boolean;
    modalClassname?: string;
    modalBaseClassname?: string;
}

export const Modal: FC<IModalProps> = (props) => {
    const { children, showModal, modalBaseClassname, modalClassname } = props;

    return createPortal(
        showModal ? (
            <div className={[styles.modalLayout, modalClassname].join(' ')}>
                <div className={[styles.modalBase, modalBaseClassname].join(' ')}>
                    {children}
                </div>
            </div>
        ) : null,
        document.body
    );
};

export default Modal;
