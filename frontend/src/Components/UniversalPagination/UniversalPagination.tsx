import { FC } from 'react';
import styles from './UniversalPagination.module.scss';

interface UniversalPaginationProps {
    currentPage: number;
    itemsPerPage: number;
    totalItems: number;
    itemsPerPageOptions?: number[];
    onPageChange: (page: number) => void;
    onItemsPerPageChange: (pageSize: number) => void;
}

const UniversalPagination: FC<UniversalPaginationProps> = ({
                                                               currentPage,
                                                               itemsPerPage,
                                                               totalItems,
                                                               itemsPerPageOptions = [5, 10, 20, 50],
                                                               onPageChange,
                                                               onItemsPerPageChange,
                                                           }) => {
    const totalPages = Math.ceil(totalItems / itemsPerPage);

    const handleNextPage = () => {
        if (currentPage < totalPages) onPageChange(currentPage + 1);
    };

    const handlePrevPage = () => {
        if (currentPage > 1) onPageChange(currentPage - 1);
    };

    const handleItemsPerPageChange = (event: React.ChangeEvent<HTMLSelectElement>) => {
        const newPageSize = Number(event.target.value);
        onItemsPerPageChange(newPageSize);
        onPageChange(1); // Reset to first page
    };

    return (
        <div className={styles.paginationContainer}>
            <div className={styles.paginationControls}>
                <button onClick={handlePrevPage} disabled={currentPage === 1}>
                    &lt;
                </button>
                <span>
                    Page {currentPage} of {totalPages}
                </span>
                <button onClick={handleNextPage} disabled={currentPage === totalPages}>
                    &gt;
                </button>
            </div>
            <div className={styles.itemsPerPageSelect}>
                <label>Items per page:</label>
                <select value={itemsPerPage} onChange={handleItemsPerPageChange}>
                    {itemsPerPageOptions.map(option => (
                        <option key={option} value={option}>
                            {option}
                        </option>
                    ))}
                </select>
            </div>
        </div>
    );
};

export default UniversalPagination;
