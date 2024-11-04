// src/components/RecordList.js
import React, { useEffect, useState } from 'react';
// import axios from 'axios';
import axios from '../axiosConfig';
import { Table, Button } from 'antd';
import RecordForm from './RecordForm';

function RecordList() {
  const [records, setRecords] = useState([]);
  const [visible, setVisible] = useState(false);
  const [editingRecord, setEditingRecord] = useState(null);

  useEffect(() => {
    fetchRecords();
  }, []);

  const fetchRecords = async () => {
    const response = await axios.get('/api/records');
    setRecords(response.data);
  };

  const columns = [
    // Define your table columns here
    {
      title: 'ID',
      dataIndex: 'id',
      key: 'id',
    },
    // Add more columns as needed
    {
      title: 'Action',
      key: 'action',
      render: (text, record) => (
        <>
          <Button
            onClick={() => {
              setEditingRecord(record);
              setVisible(true);
            }}
          >
            Edit
          </Button>
          <Button danger onClick={() => deleteRecord(record.id)}>
            Delete
          </Button>
        </>
      ),
    },
  ];

  const deleteRecord = async (id) => {
    await axios.delete(`/api/records/${id}`);
    fetchRecords();
  };

  return (
    <>
      <Button type="primary" onClick={() => setVisible(true)}>
        Add Record
      </Button>
      <Table dataSource={records} columns={columns} rowKey="id" />
      {visible && (
        <RecordForm
          visible={visible}
          setVisible={setVisible}
          record={editingRecord}
          fetchRecords={fetchRecords}
          setEditingRecord={setEditingRecord}
        />
      )}
    </>
  );
}

export default RecordList;
