// src/components/Categories.js
import React, { useEffect, useState } from 'react';
import axios from '../axiosConfig';
import { Table, Spin } from 'antd';

function Categories() {
  const [categories, setCategories] = useState([]);
  const [loading, setLoading] = useState(true);
  const [pagination, setPagination] = useState({
    current: 1,
    pageSize: 100,
    total: 0,
  });
  const [sortOrder, setSortOrder] = useState(null);
  const [sortField, setSortField] = useState('id');

  useEffect(() => {
    fetchCategories();
  }, [pagination.current, pagination.pageSize, sortField, sortOrder]);

  const fetchCategories = async () => {
    setLoading(true);
    try {
      const response = await axios.get('/admin/api/categories/', {
        params: {
          page: pagination.current,
          sort_by: sortField,
          filters: "{}",
        },
      });
      setCategories(response.data.items); // Assuming the response has an `items` key
      setPagination({
        ...pagination,
        total: response.data.total_amount / response.data.current_page_amount,
      });
    } catch (error) {
      console.error('Error fetching categories:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleTableChange = (pagination, filters, sorter) => {
    setPagination({
      ...pagination,
      current: pagination.current,
      pageSize: pagination.pageSize,
    });

    if (sorter.order) {
      setSortOrder(sorter.order === 'ascend' ? 'asc' : 'desc');
      setSortField(sorter.field);
    } else {
      setSortOrder(null);
      setSortField('id'); // Default sort field
    }
  };
// // src/components/Categories.js
// import React, { useEffect, useState } from 'react';
// import axios from '../axiosConfig';
// import { Table, Spin } from 'antd';
//
// function Categories() {
//   const [categories, setCategories] = useState([]);
//   const [loading, setLoading] = useState(true);
//
//   useEffect(() => {
//     // Fetch categories from the backend API
//     const fetchCategories = async () => {
//       try {
//         const params = {
//           a: "",
//           b: ""
//         };
//         const response = await axios.get('/admin/api/categories/', { params });
//         setCategories(response.data);
//       } catch (error) {
//         console.error('Error fetching categories:', error);
//       } finally {
//         setLoading(false);
//       }
//     };
//
//     fetchCategories();
//   }, []);
//
//   if (loading) {
//     return <Spin tip="Loading Categories..." />;
//   }

  // Define the columns for the Ant Design table
  const columns = [
    {
      title: 'ID',
      dataIndex: 'id',
      key: 'id',
    },
    {
      title: 'label',
      dataIndex: 'label',
      key: 'label',
    },
    {
      title: 'value_definition',
      dataIndex: 'value_definition',
      key: 'value_definition',
    },
    {
      title: 'description',
      dataIndex: 'description',
      key: 'description',
    },
    {
      title: 'type',
      dataIndex: 'type',
      key: 'type',
    },
    {
      title: 'priority',
      dataIndex: 'priority',
      key: 'priority',
    }
  ];

  return loading ? (
    <Spin tip="Loading Categories..." />
  ) : (
    <Table
      dataSource={categories}
      columns={columns}
      rowKey="id"
      pagination={{
        current: pagination.current,
        pageSize: pagination.pageSize,
        total: pagination.total,
      }}
      onChange={handleTableChange}
    />
  );
}

export default Categories;
