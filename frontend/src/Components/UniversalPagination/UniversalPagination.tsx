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

    const getVisiblePages = () => {
        const pages = [];
        const startPage = Math.max(1, currentPage - 2);
        const endPage = Math.min(totalPages, currentPage + 2);

        for (let i = startPage; i <= endPage; i++) {
            pages.push(i);
        }
        return pages;
    };

    const handleNextPage = () => {
        if (currentPage < totalPages) onPageChange(currentPage + 1);
    };

    const handlePrevPage = () => {
        if (currentPage > 1) onPageChange(currentPage - 1);
    };

    const handleItemsPerPageChange = (event: React.ChangeEvent<HTMLSelectElement>) => {
        const newPageSize = Number(event.target.value);
        onItemsPerPageChange(newPageSize);
        onPageChange(1);
    };

    return (
        <div className={styles.paginationContainer}>
            <div className={styles.paginationControls}>
                <button onClick={handlePrevPage} disabled={currentPage === 1}>
                    &lt;
                </button>

                {currentPage > 3 && (
                    <>
                        <button onClick={() => onPageChange(1)}>1</button>
                        {currentPage > 4 && <span>...</span>}
                    </>
                )}

                {getVisiblePages().map(page => (
                    <button
                        key={page}
                        onClick={() => onPageChange(page)}
                        className={page === currentPage ? styles.active : ''}
                    >
                        {page}
                    </button>
                ))}

                {currentPage < totalPages - 2 && (
                    <>
                        {currentPage < totalPages - 3 && <span>...</span>}
                        <button onClick={() => onPageChange(totalPages)}>{totalPages}</button>
                    </>
                )}

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
