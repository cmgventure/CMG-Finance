import { FC } from "react";
import styles from './Table.module.scss';
import FilterSearchHeader from "~/Components/FilterSearchHeader/FilterSearchHeader.tsx";
import {SortByType} from "~/Api/Categories/Types/types.tsx";

interface TableProps<T> {
    columns: string[];
    data: T[];
    renderRow: (item: T, index: number) => JSX.Element;
    onSort: (value: string, column: string) => void;
    onFilter: (value: SortByType, column: string) => void;
}

const Table: FC<TableProps<any>> = ({ columns, data, renderRow, onSort, onFilter }) => {
    return (
        <div className={styles.tableContainer}>
            <table className={styles.table}>
                <thead>
                <tr>
                    {columns.map((col, index) => (
                        <th key={index}>
                            <div className={styles.headerContent}>
                                <span>{col}</span>
                                {col !== "Actions" && (
                                    <FilterSearchHeader onFilter={onFilter} onSort={onSort} column={col}/>
                                )}
                            </div>
                        </th>
                    ))}
                </tr>
                </thead>
                <tbody>
                {data.map((item, index) => renderRow(item, index))}
                </tbody>
            </table>
        </div>
    );
};

export default Table;
