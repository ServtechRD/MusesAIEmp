import React, { useState } from 'react';
import styled from 'styled-components';
import api from '../services/api';

const UploadContainer = styled.div`
  padding: 20px;
`;

const FileInput = styled.input`
  margin-bottom: 10px;
`;

const SubmitButton = styled.button`
  background-color: #007aff;
  color: #fff;
  border: none;
  border-radius: 20px;
  padding: 10px 15px;
  cursor: pointer;
  font-size: 16px;
`;

const CodeDisplay = styled.pre`
  background-color: #f0f0f0;
  padding: 15px;
  border-radius: 10px;
  overflow-x: auto;
`;

function CodeUpload({ token }) {
  const [codeFile, setCodeFile] = useState(null);
  const [modifiedCode, setModifiedCode] = useState('');

  const handleFileChange = (e) => {
    setCodeFile(e.target.files[0]);
  };

  const handleSubmit = async () => {
    if (!codeFile) return;

    const formData = new FormData();
    formData.append('code_file', codeFile);

    try {
      const response = await api.post('/upload_code', formData, {
        headers: {
          Authorization: `Bearer ${token}`,
          'Content-Type': 'multipart/form-data',
        },
      });

      setModifiedCode(response.data.modified_code);
    } catch (error) {
      console.error('Error uploading code file:', error);
    }
  };

  return (
    <UploadContainer>
      <h3>上传代码文件</h3>
      <FileInput
        type="file"
        accept=".py,.js,.java,.cpp,.c,.txt"
        onChange={handleFileChange}
      />
      <SubmitButton onClick={handleSubmit}>提交</SubmitButton>
      {modifiedCode && (
        <div>
          <h4>修改后的代码：</h4>
          <CodeDisplay>{modifiedCode}</CodeDisplay>
        </div>
      )}
    </UploadContainer>
  );
}

export default CodeUpload;
