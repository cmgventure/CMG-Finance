// src/components/RecordForm.js
import React from 'react';
import { Modal, Form, Input } from 'antd';
// import axios from 'axios';
import axios from '../axiosConfig';

function RecordForm({
                      visible,
                      setVisible,
                      record,
                      fetchRecords,
                      setEditingRecord,
                    }) {
  const [form] = Form.useForm();

  const onFinish = async (values) => {
    if (record) {
      // Update existing record
      await axios.put(`/api/records/${record.id}`, values);
    } else {
      // Create new record
      await axios.post('/api/records', values);
    }
    fetchRecords();
    setVisible(false);
    form.resetFields();
    setEditingRecord(null);
  };

  return (
    <Modal
      visible={visible}
      title={record ? 'Edit Record' : 'Add Record'}
      onCancel={() => {
        setVisible(false);
        form.resetFields();
        setEditingRecord(null);
      }}
      onOk={() => form.submit()}
    >
      <Form form={form} onFinish={onFinish} initialValues={record}>
        {/* Define your form fields here */}
        <Form.Item name="name" label="Name" rules={[{ required: true }]}>
          <Input />
        </Form.Item>
        {/* Add more form items as needed */}
      </Form>
    </Modal>
  );
}

export default RecordForm;
