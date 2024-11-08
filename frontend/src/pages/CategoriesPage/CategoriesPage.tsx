import {FC, useEffect, useState} from 'react';
import styles from './CategoriesPage.module.scss';
import Table from "~/Components/Table/Table.tsx";
import {ICategory, SortByType} from "~/Api/Categories/Types/types.tsx";
import {deleteCategory, getAllCategories} from "~/Api/Categories/ApiService.ts";
import TrashIcon from "~/Icons/TrashIcon/TrashIcon.tsx";
import PenIcon from "~/Icons/PenIcon/PenIcon.tsx";
import UniversalPagination from "~/Components/UniversalPagination/UniversalPagination.tsx";
import {Loader} from "~/Components/Loader/Loader.tsx";
import CancelDeleteModal from "~/Components/CancelDeleteModal/CancelDeleteModal.tsx";
import {showToast} from "~/Utils/ShowToast.tsx";
import {Button} from "~/Components/Button";
import CreateCategoryModal from "~/Components/CreateCategoryForm/CreateCategoryForms.tsx";
import UpdateCategoryForm from "~/Components/UpdateCategoryForm/UpdateCategoryForm.tsx";

const CategoriesPage: FC = () => {
    const [loading, setLoading] = useState(false);
    const [page, setPage] = useState(1);
    const [pageSize, setPageSize] = useState(10);
    const [totalResults, setTotalResults] = useState(0);
    const [categories, setCategories] = useState<ICategory[]>([])
    const columns = ["Definition", "Label", "Description", "Type", "Priority", "Actions"];
    const [isDeleteModalOpen, setIsDeleteModalOpen] = useState<boolean>(false)
    const [isCreateModalOpen, setIsCreateModalOpen] = useState<boolean>(false)
    const [isUpdateModalOpen, setIsUpdateModalOpen] = useState<boolean>(false)
    const [chosenCategory, setChosenCategory] = useState<ICategory | null>(null)
    const [sortOrder, setSortOrder] = useState<SortByType>(SortByType.ASC)
    const [sortBy, setSortBy] = useState<string | null>(null)
    const [filterBy, setFilterBy] = useState<string | null>(null)
    const [filterValue, setfilterValue] = useState<string | null>(null)
    const renderRow = (item: ICategory, index) => (
        <tr key={index}>
            <td className={styles.col1}>{item.value_definition}</td>
            <td className={styles.col1}>{item.label}</td>
            <td className={styles.col1}>{item.description}</td>
            <td className={styles.col2}>{item.type}</td>
            <td>{item.priority}</td>
            <td>
                <div className={styles.actionsBlock}>
                    <div className={styles.action} onClick={
                        ()=>{
                            setChosenCategory(item);
                            setIsUpdateModalOpen(true)
                        }
                    }>
                        <PenIcon stroke={"blue"}/>
                    </div>
                    <div className={styles.action} onClick={
                        () => {
                            setChosenCategory(item);
                            setIsDeleteModalOpen(true)
                        }
                    }>
                        <TrashIcon stroke={"red"}/>
                    </div>
                </div>
            </td>
        </tr>
    );

    const handlePageChange = (newPage: number) => {
        setPage(newPage);
    };

    const handleItemsPerPageChange = (newPageSize: number) => {
        setPageSize(newPageSize);
        setPage(1);
    };

    const fetchCategories = async ({
                                       page,
                                       pageSize,
                                       sortBy,
                                       sortOrder,
                                       filterBy,
                                       filterValue,
                                   }: {
        page: number;
        pageSize: number;
        sortBy?: string;
        sortOrder?: SortByType;
        filterBy?: string;
        filterValue?: string;
    }) => {
        setLoading(true);
        try {
            const response = await getAllCategories(page, pageSize, sortBy, sortOrder, filterBy, filterValue);

            if (response) {
                setCategories(response.items);
                setTotalResults(response.total);
            } else {
                showToast(
                    'error',
                    'Error',
                    'Something went wrong during getting the list of categories. Please try again later.'
                );
            }
        } catch (error: unknown) {
            if (error instanceof Error) {
                showToast('error', 'Error', error.message);
            } else {
                showToast('error', 'Error', 'An unknown error occurred. Please try again later.');
            }
        }
        setLoading(false);
    };


    const handleDeleteCategory = async () => {
        const status = await deleteCategory(chosenCategory.id);
        if (status === 200) {
            showToast('success', 'Success', 'Category deleted successfully');
            setCategories((prevCategories) =>
                prevCategories.filter(category => category.id !== chosenCategory.id)
            );
            setChosenCategory(null)
            setIsDeleteModalOpen(false)
        } else {
            showToast('error', 'Error', 'Error during category deletion');
            setIsDeleteModalOpen(false)
        }
    };

    const handleUpdateCategory = (updatedCategory: ICategory) => {
        setCategories(prevCategories =>
            prevCategories.map(category =>
                category.id === updatedCategory.id ? updatedCategory : category
            )
        );
    };

    const handleSort = (value: SortByType, column: string) => {
        setSortOrder(value)
        setSortBy(column)
        fetchCategories({
            page: page,
            pageSize: pageSize,
            sortBy: column,
            sortOrder: value,
            filterBy: filterBy,
            filterValue: filterValue
        });
    }
    const handleFilter = (value: string, column: string) => {
        setPage(1)
        setFilterBy(column)
        setfilterValue(value)
        fetchCategories({
            page: page,
            pageSize: pageSize,
            filterBy: column,
            filterValue: value,
            sortBy: sortBy,
            sortOrder: sortOrder
        });
    }

    useEffect(() => {
        fetchCategories({
            page: page,
            pageSize: pageSize,
            sortBy: sortBy,
            sortOrder: sortOrder,
            filterBy: filterBy,
            filterValue: filterValue
        });
    }, [page, pageSize]);

    return (
        <>
            {loading ? <Loader/> : (
                <>
                    <div className={styles.headerBlock}>
                        <div className={styles.createButton}>
                            <Button onClick={() => setIsCreateModalOpen(true)}>Create category</Button>
                            <Button onClick={()=>window.location.reload()} variant={'inverted'}
                            >Reset filter</Button>
                        </div>
                        <div className={styles.centerTitle}>Categories</div>
                    </div>
                    <div className={styles.mainBlock}>
                        <Table
                            columns={columns}
                            data={categories}
                            renderRow={renderRow}
                            onSort={handleSort}
                            onFilter={handleFilter}
                        />
                        <UniversalPagination
                            currentPage={page}
                            itemsPerPage={pageSize}
                            totalItems={totalResults}
                            onPageChange={handlePageChange}
                            onItemsPerPageChange={handleItemsPerPageChange}
                        />
                    </div>
                    <CancelDeleteModal
                        showModal={isDeleteModalOpen}
                        onCancel={() => setIsDeleteModalOpen(false)}
                        onSubmit={() => handleDeleteCategory()}
                        title="Delete category"
                        description="Do you really want to delete the category"
                        submitButtonText="Delete"
                    />
                    <CreateCategoryModal
                        showModal={isCreateModalOpen}
                        onClose={() => setIsCreateModalOpen(false)}
                        onSuccess={() => {}}
                    />
                    {chosenCategory && (
                        <UpdateCategoryForm
                            showModal={isUpdateModalOpen}
                            onClose={() => setIsUpdateModalOpen(false)}
                            onSuccess={handleUpdateCategory}
                            category={chosenCategory}
                        />
                    )}
                </>
            )}
        </>
    );
};

export default CategoriesPage;
