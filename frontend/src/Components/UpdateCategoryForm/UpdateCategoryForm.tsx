import { FC} from "react";
import { Form, Formik } from "formik";
import * as Yup from "yup";
import InputField from "../InputField/InputField.tsx";
import styles from "./UpdateCategoryForm.module.scss";
import { CategoryType, ICategory, ICreateCategory } from "~/Api/Categories/Types/types.tsx";
import { updateCategory } from "~/Api/Categories/ApiService.ts";
import { Modal } from "../Modal";
import { Button } from "~/Components/Button";
import { showToast } from "~/Utils/ShowToast.tsx";

interface IUpdateCategoryFormProps {
    showModal: boolean;
    onClose: () => void;
    onSuccess: (updatedCategory: ICategory) => void;
    category: ICategory;
}

const UpdateCategoryForm: FC<IUpdateCategoryFormProps> = ({
                                                              showModal,
                                                              onClose,
                                                              onSuccess,
                                                              category,
                                                          }) => {
    const initialValues: ICreateCategory = {
        label: category.label,
        value_definition: category.value_definition,
        description: category.description,
        type: category.type as CategoryType,
        priority: category.priority,
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
            .min(1, "Priority must be at least 1.")
            .required("Priority is required"),
    });

    const handleSubmit = async (values: ICreateCategory) => {
        const response = await updateCategory(category.id, values);
        if (response.success) {
            onSuccess(response.category);
            onClose();
            showToast('success', 'Success', 'Category was updated successfully');
        } else {
            showToast('error', 'Error', 'Error during category update');
            onClose();
        }
    };

    return (
        <Modal showModal={showModal}>
            <div className={styles.modalContent}>
                <span className={styles.closeButton} onClick={onClose}>X</span>
                <h2 className={styles.modalTitle}>Update Category</h2>
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
                                    Update Category
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

export default UpdateCategoryForm;
