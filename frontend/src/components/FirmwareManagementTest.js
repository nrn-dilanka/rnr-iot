import React, { useState, useEffect } from 'react';
import { Card, Table, Button, notification } from 'antd';
import { firmwareAPI } from '../services/api';

const FirmwareManagementTest = () => {
  const [firmwares, setFirmwares] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  useEffect(() => {
    loadFirmwares();
  }, []);

  const loadFirmwares = async () => {
    try {
      setLoading(true);
      setError(null);
      console.log('Loading firmwares...');
      const response = await firmwareAPI.getFirmware();
      console.log('Firmware response:', response.data);
      setFirmwares(response.data);
    } catch (error) {
      console.error('Error loading firmwares:', error);
      setError(error.message);
      notification.error({
        message: 'Error',
        description: 'Failed to load firmware versions: ' + error.message,
      });
    } finally {
      setLoading(false);
    }
  };

  const columns = [
    {
      title: 'Version',
      dataIndex: 'version',
      key: 'version',
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
    },
  ];

  return (
    <div>
      <Card>
        <div style={{ marginBottom: 16 }}>
          <h2>Firmware Management (Test Version)</h2>
          <Button onClick={loadFirmwares}>Reload Data</Button>
        </div>
        
        {error && (
          <div style={{ color: 'red', marginBottom: 16 }}>
            Error: {error}
          </div>
        )}

        <div style={{ marginBottom: 16 }}>
          <strong>Status:</strong> {loading ? 'Loading...' : 'Ready'}
          <br />
          <strong>Firmware Count:</strong> {firmwares.length}
        </div>

        <Table
          columns={columns}
          dataSource={firmwares}
          rowKey="id"
          loading={loading}
          pagination={{
            pageSize: 10,
          }}
        />

        <div style={{ marginTop: 16 }}>
          <h3>Debug Info:</h3>
          <pre>{JSON.stringify(firmwares, null, 2)}</pre>
        </div>
      </Card>
    </div>
  );
};

export default FirmwareManagementTest;
