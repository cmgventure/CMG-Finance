import React, { useState, useRef } from 'react';
import styles from './FilterSearchHeader.module.scss';
import { FaSearch, FaAngleUp, FaAngleDown } from 'react-icons/fa';
import {SortByType} from "~/Api/Categories/Types/types.tsx";

interface FilterSearchHeaderProps {
    onFilter: (value: string, column: string) => void;
    onSort: (value: SortByType, column: string) => void;
    column: string;
}

const FilterSearchHeader: React.FC<FilterSearchHeaderProps> = ({ onFilter, onSort, column }) => {
    const [isModalOpen, setModalOpen] = useState(false);
    const [filterValue, setFilterValue] = useState('');
    const searchIconRef = useRef<HTMLDivElement | null>(null);

    const handleSearchClick = () => {
        setModalOpen(true);
    };

    let new_column = null
    if (column.toLowerCase().includes('definition')) {
        new_column = 'value_definition'
    } else {
        new_column = column.toLowerCase()
    }
    const handleSortClick = (direction: SortByType) => {
        onSort(direction, new_column);
        setModalOpen(false);
        setFilterValue("")
    };

    const handleFilter = () => {
        onFilter(filterValue, new_column);
        setModalOpen(false);
        setFilterValue("")
    };

    const modalPosition = searchIconRef.current
        ? {
            top: `${searchIconRef.current.offsetTop + searchIconRef.current.offsetHeight + 10}px`,
            left: `${searchIconRef.current.offsetLeft}px`,
        }
        : { top: '0', left: '20px' };

    return (
        <div className={styles['filter-search-header']}>
            <div className={styles.icons}>
                <FaSearch
                    onClick={handleSearchClick}
                    className={styles['search-icon']}
                    ref={searchIconRef}
                />
                <FaAngleUp onClick={() => handleSortClick(SortByType.ASC)} className={styles['arrow-icon']} />
                <FaAngleDown onClick={() => handleSortClick(SortByType.DESC)} className={styles['arrow-icon']} />
            </div>

            {isModalOpen && (
                <div
                    className={styles.modal}
                    style={{top: modalPosition.top, left: modalPosition.left}}
                >
                    <input
                        type="text"
                        value={filterValue}
                        onChange={(e) => setFilterValue(e.target.value)}
                        placeholder={"Enter search term"}
                    />
                    <button onClick={handleFilter}>OK</button>
                    <div className={styles.closeButton} onClick={()=>setModalOpen(false)}>X</div>
                </div>
            )}
        </div>
    );
};

export default FilterSearchHeader;
