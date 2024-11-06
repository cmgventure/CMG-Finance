import { FC } from "react";
import { Modal } from "../Modal";
import { Button } from "../Button";
import styles from "./CancelDeleteModal.module.scss";

interface ICancelDeleteModalProps {
    showModal: boolean;
    onCancel: () => void;
    onSubmit: () => void;
    title: string;
    description: string;
    submitButtonText?: string;
    submitButtonVariant?: string;
}

const CancelDeleteModal: FC<ICancelDeleteModalProps> = ({
                                                            showModal,
                                                            onCancel,
                                                            onSubmit,
                                                            title,
                                                            description,
                                                            submitButtonText = "Confirm",
                                                            submitButtonVariant="danger"
                                                        }) => {
    return (
        <Modal showModal={showModal}>
            <div className={styles.modalContent}>
                <h2 className={styles.modalTitle}>{title}</h2>
                <p className={styles.modalDescription}>{description}</p>

                <div className={styles.buttonContainer}>
                    <Button variant={submitButtonVariant} onClick={onSubmit}>
                        {submitButtonText}
                    </Button>
                    <Button variant="inverted" onClick={onCancel}>
                        Cancel
                    </Button>
                </div>
            </div>
        </Modal>
    );
};

export default CancelDeleteModal;
