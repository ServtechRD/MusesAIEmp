import React, { useState } from 'react';
import styled from 'styled-components';
import api from '../services/api';

const UploadContainer = styled.div`
  padding: 20px;
`;

const FileInput = styled.input`
  margin-bottom: 10px;
`;

const DescriptionInput = styled.textarea`
  width: 100%;
  resize: none;
  border-radius: 10px;
  padding: 10px;
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

function ImageUpload({ token }) {
  const [images, setImages] = useState([]);
  const [descriptions, setDescriptions] = useState({});
  const [generatedCode, setGeneratedCode] = useState('');

  const handleImageChange = (e) => {
    const files = Array.from(e.target.files).slice(0, 5); // 最多5张图片
    setImages(files);
  };

  const handleDescriptionChange = (index, value) => {
    setDescriptions({ ...descriptions, [index]: value });
  };

  const handleSubmit = async () => {
    const formData = new FormData();
    images.forEach((image, index) => {
      formData.append('images', image);
      formData.append('descriptions', descriptions[index] || '');
    });

    try {
      const response = await api.post('/upload', formData, {
        headers: {
          Authorization: `Bearer ${token}`,
          'Content-Type': 'multipart/form-data',
        },
      });
      // 在聊天窗口中显示返回的代码
      setGeneratedCode(response.data.code);
    } catch (error) {
      console.error('Error uploading images:', error);
    }
  };

  return (
    <UploadContainer>
      <h3>上传图片</h3>
      <FileInput type="file" multiple onChange={handleImageChange} />
      {images.map((image, index) => (
        <div key={index}>
          <p>{image.name}</p>
          <DescriptionInput
            rows={2}
            placeholder="说明文字"
            onChange={(e) => handleDescriptionChange(index, e.target.value)}
          />
        </div>
      ))}
      <SubmitButton onClick={handleSubmit}>提交</SubmitButton>
      {generatedCode && (
        <div>
          <h4>生成的代码：</h4>
          <pre>{generatedCode}</pre>
        </div>
      )}
    </UploadContainer>
  );
}

export default ImageUpload;
