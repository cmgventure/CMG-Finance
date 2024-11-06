import { FC } from "react";
import { Form, Formik } from "formik";
import * as Yup from "yup";
import InputField from "../InputField/InputField.tsx";
import styles from "./CreateCategoryForm.module.scss";
import {CategoryType, ICreateCategory} from "~/Api/Categories/Types/types.tsx";
import {createCategory} from "~/Api/Categories/ApiService.ts";
import { Modal } from "../Modal";
import {Button} from "~/Components/Button";
import {showToast} from "~/Utils/ShowToast.tsx";

interface ICreateCategoryFormProps {
    showModal: boolean;
    onClose: () => void;
    onSuccess: () => void;
}

const CreateCategoryForm: FC<ICreateCategoryFormProps> = ({
                                                                showModal,
                                                                onClose,
                                                                onSuccess,
                                                            }) => {
    const initialValues: ICreateCategory = {
        label: "",
        value_definition: "",
        description: "",
        type: CategoryType.API_TAG,
        priority: 0,
    };

    const validationSchema = Yup.object({
        label: Yup.string().required("Label is required"),
        value_definition: Yup.string().required("Value definition is required"),
        description: Yup.string().required("Description is required"),
        type: Yup.mixed<CategoryType>()
            .oneOf(
                Object.values(CategoryType) as Array<CategoryType>,
                "Invalid category type"
            )
            .required("Type is required"),
        priority: Yup.number()
            .min(1, "Priority can't be a negative number or 0.")
            .required("Priority is required"),
    });

    const handleSubmit = async (values: ICreateCategory) => {
        const response = await createCategory(values);
        if (response.status === 200 || response.status === 201) {
            onSuccess();
            onClose();
            showToast('success', 'Success', 'Category was created successfully');
        } else {
            showToast('error', 'Error', 'Error during category creation');
            onClose()
        }
    };

    return (
        <Modal showModal={showModal}>
            <div className={styles.modalContent}>
                <span className={styles.closeButton} onClick={onClose}>X</span>
                <h2 className={styles.modalTitle}>Create Category</h2>
                <Formik
                    initialValues={initialValues}
                    validationSchema={validationSchema}
                    onSubmit={handleSubmit}
                >
                    {({ isSubmitting }) => (
                        <Form>
                            <InputField
                                name="label"
                                label="Label"
                                placeholder="Enter label"
                            />
                            <InputField
                                name="value_definition"
                                label="Value Definition"
                                placeholder="Enter value definition"
                            />
                            <InputField
                                name="description"
                                label="Description"
                                placeholder="Enter description"
                            />

                            <InputField
                                name="type"
                                label="Type"
                                as="select"
                            >
                                <option value={CategoryType.API_TAG}>API Tag</option>
                                <option value={CategoryType.CUSTOM_FORMULA}>Custom Formula</option>
                                <option value={CategoryType.EXACT_VALUE}>Exact Value</option>
                            </InputField>
                            <InputField
                                name="priority"
                                label="Priority"
                                type="number"
                                placeholder="Enter priority"
                            />
                            <div className={styles.buttonContainer}>
                                <Button
                                    type="submit"
                                    variant="active"
                                    disabled={isSubmitting}
                                >
                                    Create Category
                                </Button>
                                <Button
                                    variant="inverted"
                                    onClick={onClose}
                                >
                                    Cancel
                                </Button>
                            </div>
                        </Form>
                    )}
                </Formik>
            </div>
        </Modal>
    );
};

export default CreateCategoryForm;
