import { FC } from "react";
import styles from './Table.module.scss';

interface TableProps<T> {
    columns: string[];
    data: T[];
    renderRow: (item: T, index: number) => JSX.Element;
}

const Table: FC<TableProps<any>> = ({ columns, data, renderRow }) => {
    return (
        <div className={styles.tableContainer}>
            <table className={styles.table}>
                <thead>
                <tr>
                    {columns.map((col, index) => (
                        <th key={index}>{col}</th>
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
