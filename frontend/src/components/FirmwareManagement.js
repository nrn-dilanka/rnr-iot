import React, { useState, useEffect } from 'react';
import {
  Card,
  Table,
  Button,
  Upload,
  Modal,
  Form,
  Input,
  Select,
  Space,
  notification,
  Progress,
  Popconfirm,
  Tag,
  Divider,
} from 'antd';
import {
  UploadOutlined,
  CloudUploadOutlined,
  DeleteOutlined,
  RocketOutlined,
  InboxOutlined,
} from '@ant-design/icons';
import { firmwareAPI, nodeAPI } from '../services/api';
import moment from 'moment';

const { Dragger } = Upload;
const { Option } = Select;

const FirmwareManagement = () => {
  const [firmwares, setFirmwares] = useState([]);
  const [nodes, setNodes] = useState([]);
  const [loading, setLoading] = useState(false);
  const [uploadModalVisible, setUploadModalVisible] = useState(false);
  const [deployModalVisible, setDeployModalVisible] = useState(false);
  const [selectedFirmware, setSelectedFirmware] = useState(null);
  const [uploadProgress, setUploadProgress] = useState(0);
  const [uploading, setUploading] = useState(false);
  const [form] = Form.useForm();
  const [deployForm] = Form.useForm();

  useEffect(() => {
    loadFirmwares();
    loadNodes();
  }, []);

  const loadFirmwares = async () => {
    try {
      setLoading(true);
      const response = await firmwareAPI.getFirmware();
      setFirmwares(response.data);
    } catch (error) {
      console.error('Error loading firmwares:', error);
      notification.error({
        message: 'Error',
        description: 'Failed to load firmware versions',
      });
    } finally {
      setLoading(false);
    }
  };

  const loadNodes = async () => {
    try {
      const response = await nodeAPI.getNodes();
      setNodes(response.data);
    } catch (error) {
      console.error('Error loading nodes:', error);
    }
  };

  const handleUpload = async (values) => {
    const { version, file: fileWrapper } = values;
    
    console.log('Form values:', values);
    console.log('File wrapper:', fileWrapper);
    
    // Extract the actual file from the fileWrapper
    let file = null;
    
    if (fileWrapper && fileWrapper.fileList && fileWrapper.fileList.length > 0) {
      const fileObj = fileWrapper.fileList[0];
      file = fileObj.originFileObj || fileObj.file || fileObj;
    } else if (fileWrapper && fileWrapper.file) {
      file = fileWrapper.file;
    } else if (fileWrapper && fileWrapper.originFileObj) {
      file = fileWrapper.originFileObj;
    }
    
    console.log('Extracted file:', file);
    
    if (!file) {
      notification.error({
        message: 'Error',
        description: 'Please select a firmware file',
      });
      return;
    }

    // Validate file type
    if (!file.name || !file.name.endsWith('.bin')) {
      notification.error({
        message: 'Error',
        description: 'Please upload a .bin firmware file',
      });
      return;
    }

    // Validate file size (max 10MB)
    if (file.size > 10 * 1024 * 1024) {
      notification.error({
        message: 'Error',
        description: 'File size must be less than 10MB',
      });
      return;
    }

    const formData = new FormData();
    formData.append('version', version);
    formData.append('file', file);

    console.log('FormData contents:');
    for (let [key, value] of formData.entries()) {
      console.log(key, value);
    }

    try {
      setUploading(true);
      setUploadProgress(0);

      // Simulate upload progress
      const progressInterval = setInterval(() => {
        setUploadProgress(prev => {
          if (prev >= 90) {
            clearInterval(progressInterval);
            return prev;
          }
          return prev + 10;
        });
      }, 200);

      const response = await firmwareAPI.uploadFirmware(formData);
      
      clearInterval(progressInterval);
      setUploadProgress(100);
      
      notification.success({
        message: 'Success',
        description: `Firmware v${version} uploaded successfully`,
      });
      
      setUploadModalVisible(false);
      form.resetFields();
      loadFirmwares();
    } catch (error) {
      console.error('Error uploading firmware:', error);
      console.error('Error response:', error.response);
      console.error('Error data:', error.response?.data);
      
      let errorMessage = 'Failed to upload firmware. Please try again.';
      
      if (error.response?.data?.detail) {
        errorMessage = error.response.data.detail;
      } else if (error.response?.status === 413) {
        errorMessage = 'File is too large. Maximum size is 10MB.';
      } else if (error.response?.status === 400) {
        errorMessage = 'Invalid file format. Please upload a .bin file.';
      } else if (error.message) {
        errorMessage = error.message;
      }
      
      notification.error({
        message: 'Upload Failed',
        description: errorMessage,
        duration: 5,
      });
    } finally {
      setUploading(false);
      setUploadProgress(0);
    }
  };

  const handleDeploy = async (values) => {
    try {
      const { node_ids } = values;
      
      for (const nodeId of node_ids) {
        await firmwareAPI.deployFirmware({
          node_id: nodeId,
          firmware_id: selectedFirmware.id,
        });
      }
      
      notification.success({
        message: 'Success',
        description: `OTA update initiated for ${node_ids.length} device(s)`,
      });
      
      setDeployModalVisible(false);
      deployForm.resetFields();
    } catch (error) {
      console.error('Error deploying firmware:', error);
      notification.error({
        message: 'Error',
        description: 'Failed to deploy firmware',
      });
    }
  };

  const getOnlineNodes = () => {
    const fiveMinutesAgo = new Date(Date.now() - 5 * 60 * 1000);
    return nodes.filter(node => 
      node.last_seen && new Date(node.last_seen) > fiveMinutesAgo
    );
  };

  const uploadProps = {
    name: 'file',
    multiple: false,
    accept: '.bin',
    beforeUpload: () => false, // Prevent auto upload
    onChange: (info) => {
      console.log('Upload onChange:', info);
      // Store the file info in form
      form.setFieldsValue({ file: info });
    },
    onRemove: () => {
      form.setFieldsValue({ file: null });
    },
    maxCount: 1,
    showUploadList: {
      showPreviewIcon: false,
      showRemoveIcon: true,
      showDownloadIcon: false,
    },
  };

  const firmwareColumns = [
    {
      title: 'Version',
      dataIndex: 'version',
      key: 'version',
      render: (version) => <Tag color="blue">{version}</Tag>,
    },
    {
      title: 'File Name',
      dataIndex: 'file_name',
      key: 'file_name',
    },
    {
      title: 'Upload Date',
      dataIndex: 'uploaded_at',
      key: 'uploaded_at',
      render: (date) => moment(date).format('MMM DD, YYYY HH:mm'),
    },
    {
      title: 'File URL',
      dataIndex: 'file_url',
      key: 'file_url',
      render: (url) => url ? (
        <a href={url} target="_blank" rel="noopener noreferrer">
          Download
        </a>
      ) : '-',
    },
    {
      title: 'Actions',
      key: 'actions',
      render: (_, record) => (
        <Space>
          <Button
            type="primary"
            size="small"
            icon={<RocketOutlined />}
            onClick={() => {
              setSelectedFirmware(record);
              setDeployModalVisible(true);
            }}
          >
            Deploy
          </Button>
          <Popconfirm
            title="Are you sure you want to delete this firmware?"
            onConfirm={() => {
              // TODO: Implement firmware deletion
              notification.info({
                message: 'Info',
                description: 'Firmware deletion not implemented yet',
              });
            }}
            okText="Yes"
            cancelText="No"
          >
            <Button
              danger
              size="small"
              icon={<DeleteOutlined />}
            >
              Delete
            </Button>
          </Popconfirm>
        </Space>
      ),
    },
  ];

  return (
    <div>
      <Card>
        <div style={{ marginBottom: 16, display: 'flex', justifyContent: 'space-between' }}>
          <div>
            <h2>Firmware Management</h2>
            <p style={{ color: '#666', marginBottom: 16 }}>
              Upload new firmware versions and deploy them to your ESP32 devices via OTA (Over-The-Air) updates.
              Only .bin files are supported with a maximum size of 10MB.
            </p>
          </div>
          <Button 
            type="primary" 
            icon={<UploadOutlined />} 
            onClick={() => setUploadModalVisible(true)}
          >
            Upload Firmware
          </Button>
        </div>

        <Table
          columns={firmwareColumns}
          dataSource={firmwares}
          rowKey="id"
          loading={loading}
          pagination={{
            pageSize: 10,
            showSizeChanger: true,
            showTotal: (total, range) => 
              `${range[0]}-${range[1]} of ${total} firmware versions`,
          }}
        />
      </Card>

      {/* Upload Firmware Modal */}
      <Modal
        title="Upload New Firmware"
        open={uploadModalVisible}
        onOk={() => form.submit()}
        onCancel={() => {
          setUploadModalVisible(false);
          form.resetFields();
          setUploadProgress(0);
        }}
        confirmLoading={uploading}
        width={600}
      >
        <Form
          form={form}
          layout="vertical"
          onFinish={handleUpload}
          requiredMark={false}
        >
          <Form.Item
            name="version"
            label="Firmware Version"
            rules={[
              { required: true, message: 'Please enter firmware version' },
              { pattern: /^\d+\.\d+\.\d+$/, message: 'Version must be in format x.x.x' },
            ]}
          >
            <Input placeholder="e.g., 1.2.0" />
          </Form.Item>

          <Form.Item
            name="file"
            label="Firmware File"
            rules={[
              { 
                required: true, 
                message: 'Please select a firmware file',
                validator: (_, value) => {
                  console.log('File validation, value:', value);
                  
                  if (!value || !value.fileList || value.fileList.length === 0) {
                    return Promise.reject(new Error('Please select a firmware file'));
                  }
                  
                  const file = value.fileList[0];
                  const actualFile = file.originFileObj || file.file || file;
                  
                  if (!actualFile || !actualFile.name) {
                    return Promise.reject(new Error('Invalid file selected'));
                  }
                  
                  if (!actualFile.name.endsWith('.bin')) {
                    return Promise.reject(new Error('Please upload a .bin file'));
                  }
                  
                  if (actualFile.size > 10 * 1024 * 1024) { // 10MB limit
                    return Promise.reject(new Error('File size must be less than 10MB'));
                  }
                  
                  return Promise.resolve();
                }
              }
            ]}
          >
            <Dragger {...uploadProps}>
              <p className="ant-upload-drag-icon">
                <InboxOutlined />
              </p>
              <p className="ant-upload-text">
                Click or drag firmware file to this area to upload
              </p>
              <p className="ant-upload-hint">
                Support for .bin files only. Maximum file size: 10MB
              </p>
            </Dragger>
          </Form.Item>

          {uploading && (
            <div style={{ marginTop: 16 }}>
              <Progress percent={uploadProgress} />
            </div>
          )}
        </Form>
      </Modal>

      {/* Deploy Firmware Modal */}
      <Modal
        title={`Deploy Firmware ${selectedFirmware?.version}`}
        open={deployModalVisible}
        onOk={() => deployForm.submit()}
        onCancel={() => {
          setDeployModalVisible(false);
          deployForm.resetFields();
        }}
        width={500}
      >
        <Form
          form={deployForm}
          layout="vertical"
          onFinish={handleDeploy}
          requiredMark={false}
        >
          <div style={{ marginBottom: 16 }}>
            <h4>Selected Firmware:</h4>
            <p><strong>Version:</strong> {selectedFirmware?.version}</p>
            <p><strong>File:</strong> {selectedFirmware?.file_name}</p>
          </div>

          <Divider />

          <Form.Item
            name="node_ids"
            label="Select Devices to Update"
            rules={[{ required: true, message: 'Please select at least one device' }]}
          >
            <Select
              mode="multiple"
              placeholder="Select devices for OTA update"
              showSearch
              filterOption={(input, option) =>
                option.children.toLowerCase().includes(input.toLowerCase())
              }
            >
              {getOnlineNodes().map(node => (
                <Option key={node.node_id} value={node.node_id}>
                  {node.name || node.node_id} - {node.node_id}
                </Option>
              ))}
            </Select>
          </Form.Item>

          <div style={{ 
            background: '#f6ffed', 
            border: '1px solid #b7eb8f', 
            borderRadius: 6, 
            padding: 12,
            marginTop: 16 
          }}>
            <p style={{ margin: 0, fontSize: 12, color: '#52c41a' }}>
              <strong>Note:</strong> Only online devices are shown. 
              The OTA update will be sent immediately to selected devices.
            </p>
          </div>

          {getOnlineNodes().length === 0 && (
            <div style={{ 
              background: '#fff2e8', 
              border: '1px solid #ffbb96', 
              borderRadius: 6, 
              padding: 12,
              marginTop: 16 
            }}>
              <p style={{ margin: 0, fontSize: 12, color: '#fa8c16' }}>
                <strong>Warning:</strong> No online devices available for deployment.
              </p>
            </div>
          )}
        </Form>
      </Modal>
    </div>
  );
};

export default FirmwareManagement;
